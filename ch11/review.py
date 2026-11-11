"""하루 치 대화를 내려받아 검사하고, 사람이 읽을 파일로 만든다."""
import asyncio
import sys
from datetime import date
from pathlib import Path

from anthropic import Anthropic
from claude_agent_sdk import AssistantMessage, TextBlock, query

import daily
from eval import INTERNAL, MARKS, MAX_CHARS
from judge import OPTIONS, POLICY

client = Anthropic()


def transcript(session_id):
    """세션의 이벤트에서 손님의 말, 도구 호출, 에이전트의 답을 골라낸다."""
    lines = []
    for event in client.beta.sessions.events.list(
            session_id, limit=100, order="asc"):
        if event.type == "user.message":
            lines.append(("손님", event.content[0].text))
        elif event.type == "agent.custom_tool_use":
            lines.append(("도구", event.name))
        elif event.type == "agent.message":
            text = "".join(block.text for block in event.content
                           if block.type == "text")
            lines.append(("응대 담당", text))
    return lines


def check(lines):
    """코드로 볼 수 있는 항목을 검사한다."""
    found = []
    answers = [text for who, text in lines if who == "응대 담당"]
    if any(len(answer) > MAX_CHARS for answer in answers):
        found.append("길이")
    if MARKS.search("\n".join(answers)):
        found.append("형식")
    if any(word in answer for answer in answers for word in INTERNAL):
        found.append("내부 정보")
    return found


async def judge(lines, gate):
    """7장의 채점 기준으로 약속과 규정을 모델에게 묻는다."""
    talk = "\n".join(f"{who}: {text}" for who, text in lines
                     if who != "도구")
    prompt = f"[정책 문서]\n{POLICY}\n\n[대화]\n{talk}"
    verdict = ""
    async with gate:
        async for message in query(prompt=prompt, options=OPTIONS):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        verdict += block.text
    return verdict.strip()


async def main(day):
    sessions = []
    for turn in daily.load(day):  # 대화가 시작된 순서를 지킨다
        if turn["session_id"] not in sessions:
            sessions.append(turn["session_id"])
    talks = [transcript(session_id) for session_id in sessions]
    gate = asyncio.Semaphore(5)
    verdicts = await asyncio.gather(*(judge(lines, gate) for lines in talks))

    pages, flagged = [], 0
    for number, (lines, verdict) in enumerate(zip(talks, verdicts), start=1):
        found = check(lines)
        if "약속: 예" in verdict:
            found.append("약속")
        if "규정: 예" in verdict:
            found.append("규정")
        flagged += bool(found)
        mark = ", ".join(found) or "표시 없음"
        print(f"대화 {number:>2} · {mark}")
        body = "\n".join(f"- **{who}**: {text}" for who, text in lines)
        pages.append(f"## 대화 {number} — {mark}\n\n{body}\n\n"
                     f"> 모델 채점: {verdict}\n")
    Path("review").mkdir(exist_ok=True)
    path = Path(f"review/{day}.md")
    path.write_text(f"# {day} 대화 검토\n\n" + "\n".join(pages),
                    encoding="utf-8")
    print(f"표시된 대화 {flagged}건 / 전체 {len(talks)}건 · {path}")


if __name__ == "__main__":
    asyncio.run(main(
        sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()))
