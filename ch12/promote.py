"""운영 중인 버전을 바꾼다. 올릴 때도, 되돌릴 때도 쓴다."""
import json
import sys
from datetime import date
from pathlib import Path

STATE = Path("managed.json")


def main(version, note):
    state = json.loads(STATE.read_text())
    if not 1 <= version <= state["latest_version"]:
        sys.exit(f"버전 {version}은 없습니다. "
                 f"가장 최근 버전은 {state['latest_version']}입니다.")
    before = state["agent_version"]
    state["agent_version"] = version
    STATE.write_text(json.dumps(state, indent=1))
    kind = "올림" if version > before else "되돌림"
    with open("versions.md", "a", encoding="utf-8") as file:
        file.write(f"- 버전 {version} · {date.today()} · {kind} · {note}\n")
    print(f"운영 중인 버전: {before} → {version}")
    print("서버를 다시 켜야 새 대화에 적용됩니다.")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("사용법: python promote.py 버전 이유")
    main(int(sys.argv[1]), " ".join(sys.argv[2:]))
