"""하루 치 기록 파일과 세션의 사용량을 모아 요약한다."""
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

from anthropic import Anthropic


def load(day):
    """그날의 기록 파일을 읽어 한 줄씩 돌려준다."""
    path = Path(f"logs/{day}.jsonl")
    return [json.loads(line) for line in path.read_text().splitlines()]


def main(day):
    turns = load(day)
    sessions = sorted({turn["session_id"] for turn in turns})
    seconds = [turn["seconds"] for turn in turns]
    calls = Counter(name for turn in turns for name in turn["calls"])
    errors = sum(1 for turn in turns if turn["error"])
    print(f"{day} 하루 기록")
    print(f"대화 {len(sessions)}건 · 말 {len(turns)}마디 · 오류 {errors}건")
    print(f"응답 시간: 평균 {sum(seconds) / len(seconds):.1f}초 · "
          f"가장 긴 것 {max(seconds)}초")
    print("도구 호출: " + " · ".join(
        f"{name} {count}" for name, count in calls.most_common()))
    print(f"도구 없이 답한 말: "
          f"{sum(1 for turn in turns if not turn['calls'])}마디")

    client = Anthropic()
    total = Counter()
    for session_id in sessions:
        usage = client.beta.sessions.retrieve(session_id).usage
        total["새 입력"] += usage.input_tokens
        total["캐시에 쓴 입력"] += usage.cache_creation.ephemeral_5m_input_tokens
        total["캐시에서 읽은 입력"] += usage.cache_read_input_tokens
        total["출력"] += usage.output_tokens
        total["실행 초"] += usage.active_seconds
        total["센트"] += int(usage.list_cost.amount)
    print("토큰: " + " · ".join(
        f"{name} {total[name]:,}" for name in
        ("새 입력", "캐시에 쓴 입력", "캐시에서 읽은 입력", "출력")))
    print(f"세션 실행 시간: 합계 {total['실행 초']:.0f}초")
    print(f"비용(정가 기준, 세션마다 센트로 반올림된 값의 합): "
          f"{total['센트'] / 100:.2f} USD")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat())
