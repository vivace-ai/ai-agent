"""모과상점 데이터 조회 함수. 에이전트의 도구가 이 함수를 쓴다."""
import sqlite3
from datetime import date
from pathlib import Path

DB_PATH = "shop.db"
POLICY_PATH = "policies.md"
TODAY = date(2026, 11, 2)  # 실습 기준일 (seed.py와 같다)


def _one(query, params):
    """조건에 맞는 한 줄을 사전으로 돌려준다. 없으면 None."""
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        row = db.execute(query, params).fetchone()
    return dict(row) if row else None


def lookup_order(order_id, phone_last4):
    """본인 확인을 거쳐 주문 한 건을 돌려준다."""
    order = _one(
        "SELECT * FROM orders WHERE order_id = ?",
        (order_id.strip().upper(),),
    )
    # 주문이 없는 경우와 끝 네 자리가 틀린 경우를 구분하지 않는다
    if order is None or order["phone_last4"] != phone_last4.strip():
        return None
    ordered = date.fromisoformat(order["ordered_at"])
    return {
        "주문번호": order["order_id"],
        "주문일": order["ordered_at"],
        "주문 후 지난 날 수": (TODAY - ordered).days,
        "상품": order["product"],
        "수량": order["quantity"],
        "결제 금액": order["amount"],
        "주문 상태": order["status"],
        "송장번호": order["tracking_no"],
    }


def track_shipment(tracking_no):
    """송장번호로 배송 기록 한 건을 돌려준다."""
    shipment = _one(
        "SELECT * FROM shipments WHERE tracking_no = ?",
        (tracking_no.strip(),),
    )
    if shipment is None:
        return None
    return {
        "택배사": shipment["carrier"],
        "배송 상태": shipment["status"],
        "현재 위치": shipment["location"],
        "마지막 갱신일": shipment["updated_at"],
    }


def search_policy(keywords):
    """정책 문서에서 낱말이 들어 있는 규정을 찾아 돌려준다."""
    words = [w for w in keywords.split() if len(w) >= 2]
    section, found = "", []
    text = Path(POLICY_PATH).read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("## "):
            section = line[3:]
        elif line.startswith("- "):
            if any(w in line or w in section for w in words):
                found.append(f"[{section}] {line[2:]}")
    return found


if __name__ == "__main__":
    print(lookup_order("MG-2610-1003", "0731"))
    print(lookup_order("MG-2610-1003", "9999"))
    print(lookup_order("MG-0000-0000", "0731"))
    print(track_shipment("193786430984"))
    print(search_policy("배송비"))
