"""시험 문제를 실행하고 코드로 채점한다."""
import asyncio
import json
import re
import shutil
import sqlite3
import sys

from claude_agent_sdk import (
    AssistantMessage, ClaudeSDKClient, ResultMessage, TextBlock,
    ToolUseBlock,
)

import chat
import shop
from eval_cases import CASES

CLEAN_DB = "shop.clean.db"  # 처음 상태의 데이터베이스
EVAL_DB = "eval.db"         # 문제마다 새로 복사해서 쓴다
MAX_CHARS = 400             # 답 하나의 최대 길이
MARKS = re.compile(r"\*\*|^[-*] |^#+ |[\U0001F300-\U0001FAFF]", re.M)
INTERNAL = ("lookup_order", "track_shipment", "search_policy",
            "request_refund", "handoff_to_owner", "mcp__", "shop.db")


async def run_case(case):
    """문제 하나를 실행해 답, 도구 호출, 비용을 모은다."""
    record = {"id": case["id"], "answers": [], "calls": [], "cost": 0}
    async with ClaudeSDKClient(options=chat.OPTIONS) as client:
        for turn in case["turns"]:
            await client.query(turn)
            texts = []
            async for message in client.receive_response():
                if isinstance(message, ResultMessage):
                    record["cost"] = message.total_cost_usd
                if not isinstance(message, AssistantMessage):
                    continue
                for block in message.content:
                    if isinstance(block, TextBlock):
                        texts.append(block.text)
                    elif isinstance(block, ToolUseBlock):
                        name = block.name.replace("mcp__shop__", "")
                        record["calls"].append(name)
            record["answers"].append("\n".join(texts))
    return record


def saved(table):
    """시험 중에 표에 기록된 줄을 돌려준다."""
    with sqlite3.connect(EVAL_DB) as db:
        db.execute(shop.REQUESTS_TABLE)
        db.execute(shop.HANDOFFS_TABLE)
        return db.execute(f"SELECT * FROM {table}").fetchall()


def grade(case, record):
    """통과하지 못한 항목의 이름을 돌려준다."""
    failed = []
    text = "\n".join(record["answers"])
    requests, handoffs = saved("requests"), saved("handoffs")
    for name in case.get("call", []):
        if name not in record["calls"]:
            failed.append(f"호출 없음:{name}")
    for name in case.get("no_call", []):
        if name in record["calls"]:
            failed.append(f"불필요한 호출:{name}")
    if "request" in case and bool(requests) != case["request"]:
        failed.append("접수 기록")
    if case.get("kind") and requests and requests[0][2] != case["kind"]:
        failed.append("접수 종류")
    if "handoff" in case and bool(handoffs) != case["handoff"]:
        failed.append("인계 기록")
    for word in case.get("say", []):
        if word not in text:
            failed.append(f"빠진 내용:{word}")
    for word in case.get("not_say", []):
        if word in text:
            failed.append(f"금지 내용:{word}")
    if any(len(answer) > MAX_CHARS for answer in record["answers"]):
        failed.append("길이")
    if MARKS.search(text):
        failed.append("형식")
    if any(word in text for word in INTERNAL):
        failed.append("내부 정보")
    return failed


async def main(prefixes):
    shop.DB_PATH = EVAL_DB
    results = []
    for case in CASES:
        if prefixes and not case["id"].startswith(tuple(prefixes)):
            continue
        shutil.copy(CLEAN_DB, EVAL_DB)
        record = await run_case(case)
        record["failed"] = grade(case, record)
        results.append(record)
        mark = "통과" if not record["failed"] else "실패"
        print(f"{record['id']} {mark} {record['cost']:.4f} "
              f"{', '.join(record['failed'])}")
    passed = sum(1 for r in results if not r["failed"])
    cost = sum(r["cost"] for r in results)
    print(f"통과 {passed}/{len(results)} · 비용 {cost:.2f} USD")
    with open("eval-results.json", "w", encoding="utf-8") as file:
        json.dump(results, file, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
