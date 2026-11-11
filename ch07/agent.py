"""모과상점 CS 에이전트: 질문 하나에 답한다."""
import asyncio
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage, ClaudeAgentOptions, ResultMessage, TextBlock,
    query,
)

BRIEF = Path("agent-brief.md").read_text(encoding="utf-8")

OPTIONS = ClaudeAgentOptions(
    system_prompt=BRIEF,   # 업무 정의서가 시스템 프롬프트가 된다
    tools=[],              # 기본 제공 도구를 모두 끈다
    setting_sources=[],    # 개발용 설정 파일을 읽지 않는다
)


async def main():
    question = input("손님: ")
    async for message in query(prompt=question, options=OPTIONS):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"모과: {block.text}")
        elif isinstance(message, ResultMessage):
            print(f"[종료] {message.subtype}")
            print(f"[비용] {message.total_cost_usd} USD")


if __name__ == "__main__":
    asyncio.run(main())
