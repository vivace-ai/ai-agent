"""사장이 교환·환불 요청을 승인하거나 거절한다."""
import sqlite3
import sys

import shop

USAGE = "사용법: python approve.py [접수번호 승인|거절]"


def show_waiting(db):
    rows = db.execute(
        "SELECT r.request_id, r.order_id, r.kind, r.amount, r.reason, "
        "o.product, o.quantity FROM requests r "
        "JOIN orders o ON o.order_id = r.order_id "
        "WHERE r.status = '승인 대기' ORDER BY r.request_id"
    ).fetchall()
    if not rows:
        print("승인 대기 중인 요청이 없습니다.")
    for number, order_id, kind, amount, reason, product, quantity in rows:
        print(f"[{number}] {kind} · {order_id} · {product} {quantity}개"
              f" · {amount}원")
        print(f"     사유: {reason}")


def decide(db, number, decision):
    row = db.execute(
        "SELECT order_id, kind, status FROM requests "
        "WHERE request_id = ?", (number,),
    ).fetchone()
    if row is None or row[2] != "승인 대기":
        print(f"접수번호 {number}은 승인 대기 상태가 아닙니다.")
        return
    order_id, kind, _ = row
    db.execute(
        "UPDATE requests SET status = ?, decided_at = ? "
        "WHERE request_id = ?",
        (decision, shop.TODAY.isoformat(), number),
    )
    if decision == "승인":
        # 실제 가게에서는 여기서 결제 대행사의 환불 기능을 부른다
        db.execute(
            "UPDATE orders SET status = ? WHERE order_id = ?",
            (f"{kind} 승인", order_id),
        )
    print(f"접수번호 {number}: {kind} {decision} ({order_id})")


def main():
    with sqlite3.connect(shop.DB_PATH) as db:
        db.execute(shop.REQUESTS_TABLE)
        if len(sys.argv) == 1:
            show_waiting(db)
        elif len(sys.argv) == 3 and sys.argv[2] in ("승인", "거절"):
            decide(db, int(sys.argv[1]), sys.argv[2])
        else:
            print(USAGE)


if __name__ == "__main__":
    main()
