"""모과상점 CS 에이전트: 대화를 이어 간다."""
import asyncio
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage, ClaudeAgentOptions, ClaudeSDKClient,
    ResultMessage, TextBlock, ToolResultBlock, ToolUseBlock, UserMessage,
)

import shop
from tools import SERVER, TOOL_NAMES

BRIEF = Path("agent-brief.md").read_text(encoding="utf-8")
BRIEF += f"\n\n## 오늘 날짜\n오늘은 {shop.TODAY}이다.\n"

OPTIONS = ClaudeAgentOptions(
    system_prompt=BRIEF,
    tools=[],                      # 기본 제공 도구는 끈다
    mcp_servers={"shop": SERVER},  # 직접 만든 도구를 연결한다
    allowed_tools=TOOL_NAMES,      # 이 도구들은 승인 없이 실행한다
    setting_sources=[],
)


def show(message):
    """메시지에서 답, 도구 호출, 도구 결과를 골라 출력한다."""
    if isinstance(message, ResultMessage):
        print(f"  [비용] {message.total_cost_usd} USD")
    if not isinstance(message, (AssistantMessage, UserMessage)):
        return
    if isinstance(message.content, str):
        return
    for block in message.content:
        if isinstance(block, TextBlock):
            print(f"모과: {block.text}")
        elif isinstance(block, ToolUseBlock):
            print(f"  [도구 호출] {block.name} {block.input}")
        elif isinstance(block, ToolResultBlock):
            for part in block.content:
                print(f"  [도구 결과] {part['text']}")


async def main():
    print("대화를 마치려면 '끝'을 입력하세요.")
    async with ClaudeSDKClient(options=OPTIONS) as client:
        while True:
            question = input("손님: ").strip()
            if question in ("", "끝"):
                return
            await client.query(question)
            async for message in client.receive_response():
                show(message)


if __name__ == "__main__":
    asyncio.run(main())
