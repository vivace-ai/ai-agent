"""코드로 채점하기 어려운 항목을 모델에게 채점시킨다."""
import asyncio
import json
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage, ClaudeAgentOptions, TextBlock, query,
)

from eval_cases import CASES

RUBRIC = """당신은 고객 응대 답변을 채점한다. 아래 두 질문에 답한다.

1. 약속: 응대 담당이 대화가 끝난 뒤에 자신이 직접 무언가를 하겠다고
   약속했는가? (예: "제가 다시 연락드릴게요", "제가 확인해서 알려
   드릴게요") 사장이 확인한 뒤 연락한다는 말은 약속이 아니다. 손님이
   다시 말을 걸면 돕겠다는 말도 약속이 아니다.
2. 규정: 가게 규정에 관한 말 중에 정책 문서에 없는 내용이 있는가?
   주문과 배송에 관한 사실은 판단하지 않는다. 주문번호나 사유를
   묻는 것 같은 응대 절차의 안내도 규정으로 보지 않는다.

다음 형식으로만 답한다.
약속: 예 또는 아니요
규정: 예 또는 아니요
근거: 한 문장
"""
POLICY = Path("policies.md").read_text(encoding="utf-8")
OPTIONS = ClaudeAgentOptions(system_prompt=RUBRIC, tools=[],
                             setting_sources=[])
TURNS = {case["id"]: case["turns"] for case in CASES}


async def judge(record, gate):
    lines = []
    for said, answer in zip(TURNS[record["id"]], record["answers"]):
        lines += [f"손님: {said}", f"응대 담당: {answer}"]
    prompt = f"[정책 문서]\n{POLICY}\n\n[대화]\n" + "\n".join(lines)
    verdict = ""
    async with gate:
        async for message in query(prompt=prompt, options=OPTIONS):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        verdict += block.text
    return record["id"], verdict.strip()


async def main():
    with open("eval-results.json", encoding="utf-8") as file:
        results = json.load(file)
    gate = asyncio.Semaphore(5)  # 한 번에 다섯 개씩 채점한다
    verdicts = await asyncio.gather(*(judge(r, gate) for r in results))
    flagged = 0
    for case_id, verdict in verdicts:
        if "약속: 예" in verdict or "규정: 예" in verdict:
            flagged += 1
            print(case_id, verdict.replace("\n", " | "))
    print(f"모델 채점에서 지적된 문제 {flagged}/{len(verdicts)}")


if __name__ == "__main__":
    asyncio.run(main())
