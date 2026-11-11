"""에이전트와 환경을 Managed Agents에 만든다."""
import json
from pathlib import Path

from anthropic import Anthropic

import shop
from managed_tools import DECLARATIONS

STATE = Path("managed.json")  # 만든 것의 ID를 적어 두는 파일
MODEL = "claude-sonnet-5-5"

BRIEF = Path("agent-brief.md").read_text(encoding="utf-8")
BRIEF += f"\n\n## 오늘 날짜\n오늘은 {shop.TODAY}이다.\n"


def main():
    client = Anthropic()
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    if "agent_id" in state:  # 이미 있으면 고쳐서 새 버전을 만든다
        agent = client.beta.agents.update(
            state["agent_id"], version=state["agent_version"],
            system=BRIEF, tools=DECLARATIONS,
        )
    else:
        agent = client.beta.agents.create(
            name="모과상점 CS", model=MODEL,
            system=BRIEF, tools=DECLARATIONS,
        )
    if "environment_id" not in state:
        environment = client.beta.environments.create(
            name="mogwa-cs",
            config={"type": "cloud", "networking": {"type": "limited"}},
        )
        state["environment_id"] = environment.id
    state["agent_id"], state["agent_version"] = agent.id, agent.version
    STATE.write_text(json.dumps(state, indent=1))
    print(f"에이전트 {agent.id} · 버전 {agent.version}")
    print(f"환경 {state['environment_id']}")


if __name__ == "__main__":
    main()
