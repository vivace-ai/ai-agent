"""shop.db가 계획대로 만들어졌는지 확인한다."""
import sqlite3

db = sqlite3.connect("shop.db")

print("[1] 주문 상태별 건수")
for status, count in db.execute(
    "SELECT status, COUNT(*) FROM orders "
    "GROUP BY status ORDER BY COUNT(*) DESC"
):
    print(f"  {status}: {count}건")

print("\n[2] 주문한 지 7일이 넘었는데 아직 배송 중인 주문")
rows = db.execute(
    """
    SELECT o.order_id, o.ordered_at, o.product,
           s.carrier, s.location, s.updated_at
    FROM orders AS o
    JOIN shipments AS s ON s.tracking_no = o.tracking_no
    WHERE o.status = '배송 중'
      AND julianday('2026-11-02') - julianday(o.ordered_at) >= 7
    ORDER BY o.ordered_at
    """
).fetchall()
for row in rows:
    print("  " + " | ".join(row))
print(f"  합계 {len(rows)}건")

print("\n[3] 발송 전 주문에 송장번호가 들어가 있지 않은지")
wrong = db.execute(
    "SELECT COUNT(*) FROM orders "
    "WHERE status IN ('결제 완료', '상품 준비 중', '취소') "
    "AND tracking_no IS NOT NULL"
).fetchone()[0]
print(f"  잘못 들어간 주문: {wrong}건")
