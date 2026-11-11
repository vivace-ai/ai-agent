"""모과상점 실습용 데이터 만들기: 주문 50건과 배송 기록."""
import random
import sqlite3
from datetime import date, timedelta

TODAY = date(2026, 11, 2)  # 실습 기준일
random.seed(2026)          # 누가 실행해도 같은 데이터가 나온다

PRODUCTS = [
    ("모과 노트 A5", 6500), ("황동 클립 세트", 4800),
    ("리넨 필통", 12000), ("모과빛 만년필 잉크", 15000),
    ("탁상 달력", 9000), ("마스킹테이프 3종", 7500),
    ("가죽 북커버", 28000), ("편지지 세트", 5500),
    ("스티커 팩", 3000), ("연필 6자루 세트", 8000),
]
CARRIERS = ["솔택배", "바람택배"]
HUBS = ["옥천 터미널", "대전 터미널", "수원 터미널", "부산 터미널"]

# (주문 상태, 건수, 주문 후 지난 날 수의 범위)
PLAN = [
    ("결제 완료", 4, (0, 0)),
    ("상품 준비 중", 8, (1, 2)),
    ("배송 중", 9, (2, 4)),
    ("배송 중", 5, (7, 10)),   # 일부러 넣은 지연 주문
    ("배송 완료", 20, (5, 30)),
    ("취소", 4, (3, 20)),
]

SCHEMA = """
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS shipments;
CREATE TABLE orders (
    order_id    TEXT PRIMARY KEY,  -- 주문번호 (예: MG-2610-4821)
    ordered_at  TEXT NOT NULL,     -- 주문일
    product     TEXT NOT NULL,     -- 상품명
    quantity    INTEGER NOT NULL,  -- 수량
    amount      INTEGER NOT NULL,  -- 결제 금액(원)
    status      TEXT NOT NULL,     -- 주문 상태
    phone_last4 TEXT NOT NULL,     -- 연락처 끝 네 자리
    tracking_no TEXT               -- 송장번호 (발송 전에는 없음)
);
CREATE TABLE shipments (
    tracking_no TEXT PRIMARY KEY,  -- 송장번호
    carrier     TEXT NOT NULL,     -- 택배사
    status      TEXT NOT NULL,     -- 배송 상태
    location    TEXT NOT NULL,     -- 현재 위치
    updated_at  TEXT NOT NULL      -- 마지막 갱신일
);
"""


def new_order_id(ordered_at, used):
    """주문일의 연·월을 넣어 겹치지 않는 주문번호를 만든다."""
    while True:
        order_id = f"MG-{ordered_at:%y%m}-{random.randint(1000, 9999)}"
        if order_id not in used:
            used.add(order_id)
            return order_id


def shipment_for(status, days_ago):
    """주문 상태와 지난 날 수에 맞는 배송 기록을 만든다."""
    if status == "배송 완료":
        updated = TODAY - timedelta(days=max(days_ago - 3, 0))
        return "배송 완료", "배송지", updated
    if days_ago >= 7:  # 지연: 발송 이틀 뒤부터 기록이 멈춰 있다
        updated = TODAY - timedelta(days=days_ago - 2)
    else:
        updated = TODAY - timedelta(days=random.randint(0, 1))
    return "이동 중", random.choice(HUBS), updated


def main():
    db = sqlite3.connect("shop.db")
    db.executescript(SCHEMA)
    used = set()

    for status, count, (lo, hi) in PLAN:
        for _ in range(count):
            days_ago = random.randint(lo, hi)
            ordered_at = TODAY - timedelta(days=days_ago)
            order_id = new_order_id(ordered_at, used)
            product, price = random.choice(PRODUCTS)
            quantity = random.choice([1, 1, 1, 2, 3])
            tracking_no = None

            if status in ("배송 중", "배송 완료"):
                tracking_no = str(random.randint(10**11, 10**12 - 1))
                ship_status, location, updated = shipment_for(
                    status, days_ago
                )
                db.execute(
                    "INSERT INTO shipments VALUES (?, ?, ?, ?, ?)",
                    (tracking_no, random.choice(CARRIERS), ship_status,
                     location, updated.isoformat()),
                )

            db.execute(
                "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (order_id, ordered_at.isoformat(), product, quantity,
                 price * quantity, status,
                 f"{random.randint(0, 9999):04d}", tracking_no),
            )

    db.commit()
    orders = db.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    ships = db.execute("SELECT COUNT(*) FROM shipments").fetchone()[0]
    print(f"shop.db 생성 완료: 주문 {orders}건, 배송 기록 {ships}건")


if __name__ == "__main__":
    main()
