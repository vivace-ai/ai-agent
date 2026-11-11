"""모과상점 CS 에이전트: 대화를 이어 간다."""
import asyncio
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage, ClaudeAgentOptions, ClaudeSDKClient, TextBlock,
)

BRIEF = Path("agent-brief.md").read_text(encoding="utf-8")

OPTIONS = ClaudeAgentOptions(
    system_prompt=BRIEF,
    tools=[],
    setting_sources=[],
)


async def main():
    print("대화를 마치려면 '끝'을 입력하세요.")
    async with ClaudeSDKClient(options=OPTIONS) as client:
        while True:
            question = input("손님: ").strip()
            if question in ("", "끝"):
                return
            await client.query(question)
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(f"모과: {block.text}")


if __name__ == "__main__":
    asyncio.run(main())
