# 클로드와 대화로 만드는 CS 에이전트 — 예제 소스

『클로드와 대화로 만드는 CS 에이전트 — 개발부터 배포·운영까지』(김영희 지음)의 예제 코드입니다.
가상의 1인 온라인 문구점 '모과상점'의 고객 응대 에이전트를 장마다 조금씩 만들어 갑니다.

## 폴더 구성

`chNN` 폴더에는 그 장을 마쳤을 때의 파일이 모두 들어 있습니다. 앞 장의 파일도 함께 들어 있으므로,
어느 장에서든 그 폴더 하나만 가져와 이어서 실습할 수 있습니다.

| 폴더 | 장 | 그 장에서 새로 생기거나 바뀌는 파일 |
|---|---|---|
| `ch01` | 문의 100건에서 시작하기 | `inquiries.csv`, `agent-brief.md`, `eval-seed.md` |
| `ch02` | 실습용 가게 만들기 | `CLAUDE.md`, `seed.py`, `check.py`, `policies.md` |
| `ch03` | 첫 에이전트 | `agent.py`, `chat.py`, `agent-brief.md` |
| `ch04` | 도구 연결하기 | `shop.py`, `tools.py`, `chat.py`, `agent-brief.md` |
| `ch05` | 환불 접수와 사람 승인 | `approve.py`, `shop.py`, `tools.py`, `chat.py`, `agent-brief.md` |
| `ch06` | 상담원 인계와 대화 요약 | `inbox.py`, `shop.py`, `tools.py`, `agent-brief.md` |
| `ch07` | 문의 30건 시험지 | `eval_cases.py`, `eval.py`, `judge.py`, `shop.py`, `tools.py`, `agent-brief.md` |
| `ch08` | 공격 시험 | `attack_cases.py`, `attack.py`, `shop.py`, `tools.py`, `inbox.py` |
| `ch09` | Managed Agents에 올리기 | `deploy.py`, `managed_tools.py`, `managed_chat.py`, `managed_eval.py` |
| `ch10` | 웹 채팅 위젯 | `server.py`, `static/widget.html`, `static/embed.js`, `static/shop.html` |
| `ch11` | 기록·비용·실패 사례 | `practice_customers.py`, `daily.py`, `review.py`, `server.py`, `eval_cases.py` |
| `ch12` | 버전·재평가·되돌리기 | `promote.py`, `compare.py`, `deploy.py`, `managed_chat.py`, `attack.py`, `attack_cases.py`, `agent-brief.md` |

`ch01`의 `inquiries_answer_key.csv`와 `make_csv.py`는 실습용 문의 100건을 만든 방법과 분류 기준을 확인하는 데 씁니다.

## 실행 준비

Python 3.10 이상이 필요합니다. 책의 실행 결과는 Python 3.13에서 얻었습니다.

```bash
cd ch04                              # 실습할 장의 폴더
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\Activate.ps1
pip install -r ../requirements.txt
export ANTHROPIC_API_KEY=발급받은키   # Windows: $env:ANTHROPIC_API_KEY = "발급받은키"
python seed.py                       # shop.db를 만든다
```

- `shop.db`는 저장소에 없습니다. `python seed.py`를 실행하면 책과 같은 주문 50건이 만들어집니다.
- 7장부터는 처음 상태의 `shop.db`를 `shop.clean.db`로 복사해 둡니다(`cp shop.db shop.clean.db`).
- 9장부터 쓰는 `managed.json`도 저장소에 없습니다. 계정마다 값이 다르므로 `python deploy.py`로 직접 만듭니다.
  12장의 코드로 시작할 때는 책 12장 장면 1의 안내대로 `latest_version` 값을 더합니다.

## 확인한 버전

| 패키지 | 버전 | 쓰는 장 |
|---|---|---|
| `claude-agent-sdk` | 0.2.172 | 3~8장 |
| `anthropic` | 2.7.0 | 9~12장 |
| `Flask` | 3.1.3 | 10~12장 |
| `waitress` | 3.0.2 | 10~12장 |

Claude Managed Agents는 집필 시점에 베타입니다. 코드가 그대로 실행되지 않으면 각 장 끝의 공식 문서를 먼저 확인합니다.

## 주의할 점

- API 키는 환경 변수로만 넣습니다. 코드, `static` 폴더, 저장소에 적지 않습니다.
- 3장부터는 프로그램을 실행할 때마다 API 요금이 듭니다. 장별 금액은 책의 '시작하기 전에'에 있습니다.
- 주문, 연락처 끝 네 자리, 택배사, 가게 정책은 모두 실습을 위해 만든 가상의 값입니다.
- 모델의 답은 실행할 때마다 달라집니다. 책과 문장이 달라도 도구 호출의 순서와 답에 담긴 사실이 같으면 정상입니다.
