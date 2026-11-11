"""사장이 넘겨받은 문의를 확인하고 완료로 표시한다."""
import sqlite3
import sys

import shop


def show_waiting(db):
    rows = db.execute(
        "SELECT handoff_id, kind, summary, order_id, reply_to "
        "FROM handoffs WHERE status = '대기' ORDER BY handoff_id"
    ).fetchall()
    if not rows:
        print("넘겨받은 문의가 없습니다.")
    for number, kind, summary, order_id, reply_to in rows:
        where = order_id or f"주문 없음 · 답장 {reply_to}"
        print(f"[{number}] {kind} · {where}")
        for line in summary.splitlines():
            print(f"     {line}")


def close(db, number):
    done = db.execute(
        "UPDATE handoffs SET status = '완료' "
        "WHERE handoff_id = ? AND status = '대기'", (number,),
    ).rowcount
    if done:
        print(f"인계번호 {number}: 완료")
    else:
        print(f"인계번호 {number}은 대기 상태가 아닙니다.")


def main():
    with sqlite3.connect(shop.DB_PATH) as db:
        db.execute(shop.HANDOFFS_TABLE)
        if len(sys.argv) == 1:
            show_waiting(db)
        elif len(sys.argv) == 3 and sys.argv[2] == "완료":
            close(db, int(sys.argv[1]))
        else:
            print("사용법: python inbox.py [인계번호 완료]")


if __name__ == "__main__":
    main()
