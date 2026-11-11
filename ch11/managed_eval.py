"""7장과 8장의 시험 문제를 Managed Agents에 올린 에이전트로 실행한다."""
import asyncio
import sys

import attack
import eval as base
import managed_chat


async def run_case(case):
    """문제 하나를 세션 하나로 실행해 답, 도구 호출, 비용을 모은다."""
    record = {"id": case["id"], "answers": [], "calls": [], "cost": 0}
    session = managed_chat.open_session(f"시험 {case['id']}")
    for turn in case["turns"]:
        # ask는 기다리는 동안 멈춰 있는 함수라서 별도 스레드에서 실행한다
        answer, calls = await asyncio.to_thread(
            managed_chat.ask, session.id, turn, lambda line: None)
        record["answers"].append(answer)
        record["calls"] += calls
    usage = managed_chat.client.beta.sessions.retrieve(session.id).usage
    record["cost"] = int(usage.list_cost.amount) / 100  # 센트 단위로 온다
    managed_chat.client.beta.sessions.archive(session.id)
    return record


if __name__ == "__main__":
    base.run_case = run_case  # 실행하는 부분만 바꾸고 채점은 그대로 쓴다
    if sys.argv[1:2] == ["attack"]:
        asyncio.run(attack.main(sys.argv[2:]))
    else:
        asyncio.run(base.main(sys.argv[1:]))
