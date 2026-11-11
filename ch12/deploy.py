"""에이전트의 새 버전을 만든다. 운영 중인 버전은 바꾸지 않는다."""
import json
import sys
from datetime import date
from pathlib import Path

from anthropic import Anthropic

import shop
from managed_tools import DECLARATIONS

STATE = Path("managed.json")  # 만든 것의 ID를 적어 두는 파일
MODEL = "claude-sonnet-5-5"

BRIEF = Path("agent-brief.md").read_text(encoding="utf-8")
BRIEF += f"\n\n## 오늘 날짜\n오늘은 {shop.TODAY}이다.\n"


def main(note):
    client = Anthropic()
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    if "agent_id" in state:  # 이미 있으면 고쳐서 새 버전을 만든다
        agent = client.beta.agents.update(
            state["agent_id"], version=state["latest_version"],
            system=BRIEF, tools=DECLARATIONS,
        )
    else:
        agent = client.beta.agents.create(
            name="모과상점 CS", model=MODEL,
            system=BRIEF, tools=DECLARATIONS,
        )
        state["agent_id"] = agent.id
        state["agent_version"] = agent.version  # 처음 만든 버전은 바로 쓴다
    if "environment_id" not in state:
        environment = client.beta.environments.create(
            name="mogwa-cs",
            config={"type": "cloud", "networking": {"type": "limited"}},
        )
        state["environment_id"] = environment.id
    state["latest_version"] = agent.version
    STATE.write_text(json.dumps(state, indent=1))
    with open("versions.md", "a", encoding="utf-8") as file:
        file.write(f"- 버전 {agent.version} · {date.today()} · 만듦 · {note}\n")
    print(f"만든 버전 {agent.version} · 운영 중인 버전 {state['agent_version']}")


if __name__ == "__main__":
    main(" ".join(sys.argv[1:]) or "메모 없음")
