"""Managed Agents에 올린 에이전트와 대화한다."""
import json
from pathlib import Path

from anthropic import Anthropic

import managed_tools

STATE = json.loads(Path("managed.json").read_text())
client = Anthropic()


def open_session(title="모과상점 문의"):
    """정해 둔 버전의 에이전트로 세션을 하나 연다."""
    return client.beta.sessions.create(
        agent={"type": "agent", "id": STATE["agent_id"],
               "version": STATE["agent_version"]},
        environment_id=STATE["environment_id"],
        title=title,
    )


def ask(session_id, text, show=print):
    """손님의 말을 보내고, 에이전트가 답을 마칠 때까지 이벤트를 처리한다."""
    answers, calls = [], []
    with client.beta.sessions.events.stream(session_id) as stream:
        client.beta.sessions.events.send(session_id, events=[
            {"type": "user.message",
             "content": [{"type": "text", "text": text}]},
        ])
        for event in stream:
            if event.type == "agent.message":
                answer = "".join(block.text for block in event.content
                                 if block.type == "text")
                answers.append(answer)
                show(f"모과: {answer}")
            elif event.type == "agent.custom_tool_use":
                calls.append(event.name)
                show(f"  [도구 호출] {event.name} {event.input}")
                result = managed_tools.run(event.name, event.input)
                show(f"  [도구 결과] {result}")
                client.beta.sessions.events.send(session_id, events=[
                    {"type": "user.custom_tool_result",
                     "custom_tool_use_id": event.id,
                     "content": [{"type": "text", "text": result}]},
                ])
            elif event.type == "session.error":
                show(f"  [오류] {event.error}")
            elif event.type == "session.status_idle":
                # 도구 결과를 기다리는 멈춤이면 계속 듣는다
                if event.stop_reason.type != "requires_action":
                    break
    return "\n".join(answers), calls


def main():
    session = open_session()
    print(f"세션 {session.id}")
    print("대화를 마치려면 '끝'을 입력하세요.")
    while True:
        question = input("손님: ").strip()
        if question in ("", "끝"):
            break
        ask(session.id, question)
    usage = client.beta.sessions.retrieve(session.id).usage
    cost = int(usage.list_cost.amount) / 100  # 센트 단위로 온다
    print(f"  [사용량] 실행 {usage.active_seconds:.0f}초 · 정가 기준 {cost:.2f} USD")


if __name__ == "__main__":
    main()
