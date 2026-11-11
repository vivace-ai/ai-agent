"""모과상점 데이터 조회 함수. 에이전트의 도구가 이 함수를 쓴다."""
import sqlite3
from datetime import date
from pathlib import Path

DB_PATH = "shop.db"
POLICY_PATH = "policies.md"
TODAY = date(2026, 11, 2)  # 실습 기준일 (seed.py와 같다)
REQUEST_KINDS = ("환불", "교환", "취소")
RETURN_DAYS = 7  # 받은 날부터 접수할 수 있는 기간
NOT_FOUND = "주문을 찾을 수 없거나 연락처 끝 네 자리가 일치하지 않음"
MAX_FAILURES = 3  # 이만큼 연속으로 틀리면 그 주문번호의 조회를 잠근다
LOCKED = ("본인 확인에 여러 번 실패해 이 주문번호는 조회가 잠겨 있음. "
          "사장에게 넘길 것")
ATTEMPTS_TABLE = """
CREATE TABLE IF NOT EXISTS attempts (
    order_id TEXT PRIMARY KEY,
    failures INTEGER NOT NULL
)
"""

HANDOFF_KINDS = ("배송 지연", "기타")
LINE_LIMIT = 80  # 요약 한 줄의 최대 글자 수
HANDOFFS_TABLE = """
CREATE TABLE IF NOT EXISTS handoffs (
    handoff_id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind       TEXT NOT NULL,   -- 배송 지연 또는 기타
    summary    TEXT NOT NULL,   -- 대화 요약, 세 줄 이하
    order_id   TEXT,            -- 주문이 없는 문의는 비어 있다
    reply_to   TEXT,            -- 주문이 없을 때 답을 보낼 이메일
    status     TEXT NOT NULL,   -- 대기, 완료
    created_at TEXT NOT NULL
)
"""

REQUESTS_TABLE = """
CREATE TABLE IF NOT EXISTS requests (
    request_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id     TEXT NOT NULL,
    kind         TEXT NOT NULL,   -- 환불 또는 교환
    reason       TEXT NOT NULL,
    amount       INTEGER NOT NULL,
    status       TEXT NOT NULL,   -- 승인 대기, 승인, 거절
    requested_at TEXT NOT NULL,
    decided_at   TEXT
)
"""


def _one(query, params):
    """조건에 맞는 한 줄을 사전으로 돌려준다. 없으면 None."""
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        row = db.execute(query, params).fetchone()
    return dict(row) if row else None


def _failures(order_id, change=None):
    """주문번호의 연속 실패 횟수를 읽거나 바꾼다."""
    with sqlite3.connect(DB_PATH) as db:
        db.execute(ATTEMPTS_TABLE)
        if change == "더하기":
            db.execute(
                "INSERT INTO attempts VALUES (?, 1) ON CONFLICT(order_id) "
                "DO UPDATE SET failures = failures + 1", (order_id,))
        elif change == "지우기":
            db.execute("DELETE FROM attempts WHERE order_id = ?", (order_id,))
        row = db.execute(
            "SELECT failures FROM attempts WHERE order_id = ?", (order_id,),
        ).fetchone()
    return row[0] if row else 0


def is_locked(order_id):
    return _failures(order_id.strip().upper()) >= MAX_FAILURES


def lookup_order(order_id, phone_last4):
    """본인 확인을 거쳐 주문 한 건을 돌려준다."""
    order_id = order_id.strip().upper()
    if is_locked(order_id):
        return None
    order = _one("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    # 주문이 없는 경우와 끝 네 자리가 틀린 경우를 구분하지 않는다
    if order is None or order["phone_last4"] != phone_last4.strip():
        _failures(order_id, "더하기")  # 없는 주문번호도 똑같이 센다
        return None
    _failures(order_id, "지우기")
    ordered = date.fromisoformat(order["ordered_at"])
    return {
        "주문번호": order["order_id"],
        "주문일": order["ordered_at"],
        "주문 후 지난 날 수": (TODAY - ordered).days,
        "상품": order["product"],
        "수량": order["quantity"],
        "결제 금액": order["amount"],
        "주문 상태": order["status"],
        "송장번호": order["tracking_no"],
        "교환·환불 접수": _request_summary(order["order_id"]),
    }


def _request_summary(order_id):
    """주문에 접수된 요청이 있으면 한 줄로 돌려준다."""
    with sqlite3.connect(DB_PATH) as db:
        db.execute(REQUESTS_TABLE)
    row = _one(
        "SELECT * FROM requests WHERE order_id = ? "
        "ORDER BY request_id DESC",
        (order_id,),
    )
    if row is None:
        return "없음"
    return f"접수번호 {row['request_id']} · {row['kind']} · {row['status']}"


def _refuse(why, key="접수"):
    return {key: False, "이유": why}


def create_request(order_id, phone_last4, kind, reason):
    """교환·환불 요청을 승인 대기로 기록한다. 실행하지는 않는다."""
    order = lookup_order(order_id, phone_last4)
    if order is None:
        return _refuse(NOT_FOUND)
    if kind not in REQUEST_KINDS:
        return _refuse("종류는 환불, 교환, 취소 중 하나여야 함")
    if not reason.strip():
        return _refuse("사유가 비어 있음")
    state = order["주문 상태"]
    if kind == "취소":  # 취소는 발송 준비가 시작되기 전에만 받는다
        if state != "결제 완료":
            return _refuse(f"결제 완료 상태에서만 취소할 수 있음 (현재 {state})")
    elif state != "배송 완료":
        return _refuse(f"상품을 받은 뒤에만 접수할 수 있음 (현재 {state})")
    else:
        received = track_shipment(order["송장번호"])["마지막 갱신일"]
        days = (TODAY - date.fromisoformat(received)).days
        if days > RETURN_DAYS:
            return _refuse(f"받은 날부터 {days}일이 지나 접수 기간이 끝남")
    waiting = _one(
        "SELECT request_id FROM requests "
        "WHERE order_id = ? AND status = '승인 대기'",
        (order["주문번호"],),
    )
    if waiting:
        number = waiting["request_id"]
        return _refuse(f"이미 접수된 요청이 있음 (접수번호 {number})")
    with sqlite3.connect(DB_PATH) as db:
        cursor = db.execute(
            "INSERT INTO requests (order_id, kind, reason, amount, "
            "status, requested_at) VALUES (?, ?, ?, ?, '승인 대기', ?)",
            (order["주문번호"], kind, reason.strip(),
             order["결제 금액"], TODAY.isoformat()),
        )
    return {
        "접수": True,
        "접수번호": cursor.lastrowid,
        "종류": kind,
        "상태": "승인 대기",
        "상품": order["상품"],
        "결제 금액": order["결제 금액"],
    }


def track_shipment(tracking_no):
    """송장번호로 배송 기록 한 건을 돌려준다."""
    shipment = _one(
        "SELECT * FROM shipments WHERE tracking_no = ?",
        (tracking_no.strip(),),
    )
    if shipment is None:
        return None
    return {
        "택배사": shipment["carrier"],
        "배송 상태": shipment["status"],
        "현재 위치": shipment["location"],
        "마지막 갱신일": shipment["updated_at"],
    }


def search_policy(keywords):
    """정책 문서에서 낱말이 들어 있는 규정을 찾아 돌려준다."""
    words = [w for w in keywords.split() if len(w) >= 2]
    section, found = "", []
    text = Path(POLICY_PATH).read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("## "):
            section = line[3:]
        elif line.startswith("- "):
            if any(w in line or w in section for w in words):
                found.append(f"[{section}] {line[2:]}")
    return found


def create_handoff(kind, summary, order_id="", phone_last4="",
                   reply_to=""):
    """문의를 사장에게 넘길 목록에 기록한다."""
    if kind not in HANDOFF_KINDS:
        return _refuse("종류는 배송 지연 또는 기타여야 함", "인계")
    lines = [line for line in summary.strip().splitlines() if line.strip()]
    if not lines:
        return _refuse("요약이 비어 있음", "인계")
    if len(lines) > 3:
        return _refuse(f"요약은 세 줄 이하여야 함 (현재 {len(lines)}줄)", "인계")
    if any(len(line) > LINE_LIMIT for line in lines):
        return _refuse(f"요약 한 줄은 {LINE_LIMIT}자 이하여야 함", "인계")
    order_id = order_id.strip().upper()
    if order_id:
        if lookup_order(order_id, phone_last4) is None:
            return _refuse(NOT_FOUND, "인계")
        reply_to = ""  # 주문에 등록된 연락처로 답한다
    elif "@" not in reply_to:
        return _refuse("주문이 없는 문의는 답을 받을 이메일이 필요함", "인계")
    with sqlite3.connect(DB_PATH) as db:
        db.execute(HANDOFFS_TABLE)
        if order_id:
            waiting = db.execute(
                "SELECT handoff_id FROM handoffs "
                "WHERE order_id = ? AND status = '대기'", (order_id,),
            ).fetchone()
            if waiting:  # 같은 주문은 새로 만들지 않고 요약을 고친다
                number = waiting[0]
                db.execute(
                    "UPDATE handoffs SET summary = ? WHERE handoff_id = ?",
                    ("\n".join(lines), number),
                )
                return {"인계": True, "인계번호": number,
                        "상태": "대기", "비고": "요약을 새 내용으로 고침"}
        cursor = db.execute(
            "INSERT INTO handoffs (kind, summary, order_id, reply_to, "
            "status, created_at) VALUES (?, ?, ?, ?, '대기', ?)",
            (kind, "\n".join(lines), order_id, reply_to.strip(),
             TODAY.isoformat()),
        )
    return {"인계": True, "인계번호": cursor.lastrowid, "상태": "대기"}


if __name__ == "__main__":
    print(lookup_order("MG-2610-1003", "0731"))
    print(lookup_order("MG-2610-1003", "9999"))
    print(lookup_order("MG-0000-0000", "0731"))
    print(track_shipment("193786430984"))
    print(search_policy("배송비"))
    print(create_request("MG-2610-2525", "0445", "환불", "색이 달라요"))
    print(create_request("MG-2610-2525", "0445", "환불", "색이 달라요"))
    print(create_request("MG-2610-3015", "9949", "환불", "마음이 바뀜"))
    print(create_request("MG-2610-1003", "0731", "교환", "다른 색으로"))
    print(create_request("MG-2610-2525", "1111", "환불", "색이 달라요"))
    three = "배송이 8일째 멈춤\n손님이 항의함\n택배사 확인 필요"
    print(create_handoff("배송 지연", three, "MG-2610-6370", "2521"))
    print(create_handoff("배송 지연", three, "MG-2610-6370", "2521"))
    print(create_handoff("기타", three + "\n넷째 줄", "MG-2610-1003", "0731"))
    print(create_handoff("기타", "해외 배송 문의"))
    print(create_handoff("기타", "해외 배송 문의", reply_to="a@example.com"))
