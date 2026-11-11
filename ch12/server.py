"""채팅 창과 Managed Agents 세션 사이에서 메시지를 전달하는 가게 서버."""
import json
import logging
import secrets
import threading
import time
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request

import managed_chat

MAX_CHARS = 500   # 손님의 말 한 번의 최대 길이
MAX_TURNS = 30    # 대화 하나에서 받을 수 있는 말의 수
MAX_NEW = 20      # 1분 동안 새로 열 수 있는 대화의 수
ALLOWED_SITES = ["https://mogwa.example"]  # 채팅 창을 붙여도 되는 홈페이지
BUSY = "앞의 문의에 답하는 중이에요. 답이 온 뒤에 다시 보내 주세요."
FAILED = "지금은 답을 드릴 수 없어요. 잠시 뒤에 다시 시도해 주세요."

app = Flask(__name__)
log = logging.getLogger("mogwa")
log.setLevel(logging.INFO)
handler = logging.FileHandler("server.log", encoding="utf-8")
handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
log.addHandler(handler)
visitors = {}  # 방문자 번호 -> 세션 ID, 받은 말의 수, 잠금
opened = []    # 최근에 대화를 연 시각


def record(session_id, started, calls, asked, answered, error=""):
    """말 한 마디의 처리 결과를 그날의 기록 파일에 한 줄로 적는다."""
    now = datetime.now()
    Path("logs").mkdir(exist_ok=True)
    line = {"time": now.isoformat(timespec="seconds"),
            "session_id": session_id,
            "seconds": round(time.time() - started, 1),
            "calls": calls, "asked": asked, "answered": answered,
            "error": error}
    with open(f"logs/{now:%Y-%m-%d}.jsonl", "a", encoding="utf-8") as file:
        file.write(json.dumps(line, ensure_ascii=False) + "\n")


def refuse(message, status):
    return jsonify({"error": message}), status


@app.post("/api/visitors")
def create_visitor():
    """대화를 시작한다. 세션을 열고, 세션 ID 대신 방문자 번호를 돌려준다."""
    now = time.time()
    opened[:] = [at for at in opened if now - at < 60]
    if len(opened) >= MAX_NEW:
        return refuse("문의가 몰리고 있어요. 잠시 뒤에 다시 시도해 주세요.", 429)
    opened.append(now)
    session = managed_chat.open_session("웹 채팅")
    token = secrets.token_urlsafe(24)
    visitors[token] = {"session_id": session.id, "turns": 0,
                       "lock": threading.Lock()}
    log.info("새 대화 %s", session.id)
    return jsonify({"visitor": token})


@app.post("/api/messages")
def send_message():
    """손님의 말을 검사한 뒤 세션에 보내고 에이전트의 답을 돌려준다."""
    visitor = visitors.get(request.headers.get("X-Visitor", ""))
    if visitor is None:
        return refuse("대화를 새로 시작해 주세요.", 401)
    body = request.get_json(silent=True) or {}
    text = str(body.get("text", "")).strip()
    if not text:
        return refuse("내용을 입력해 주세요.", 400)
    if len(text) > MAX_CHARS:
        return refuse(f"{MAX_CHARS}자 안으로 줄여서 보내 주세요.", 400)
    if visitor["turns"] >= MAX_TURNS:
        return refuse("대화가 길어졌어요. 새 대화로 이어서 문의해 주세요.", 429)
    if not visitor["lock"].acquire(blocking=False):
        return refuse(BUSY, 429)
    started = time.time()
    try:
        visitor["turns"] += 1
        answer, calls = managed_chat.ask(
            visitor["session_id"], text, show=lambda line: None)
        record(visitor["session_id"], started, calls, len(text), len(answer))
        return jsonify({"answer": answer})
    except Exception as error:
        log.exception("답하지 못함 %s", visitor["session_id"])
        record(visitor["session_id"], started, [], len(text), 0,
               type(error).__name__)
        return refuse(FAILED, 502)
    finally:
        visitor["lock"].release()


@app.get("/")
def widget():
    """채팅 창을 내준다. 정해 둔 홈페이지 안에서만 열리게 한다."""
    response = app.send_static_file("widget.html")
    sites = " ".join(["'self'"] + ALLOWED_SITES)
    response.headers["Content-Security-Policy"] = f"frame-ancestors {sites}"
    return response


if __name__ == "__main__":
    app.run(port=8000, threaded=True)
