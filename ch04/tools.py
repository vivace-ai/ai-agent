"""조회 함수를 에이전트의 도구로 등록한다."""
import json

from claude_agent_sdk import create_sdk_mcp_server, tool

import shop

NOT_FOUND = "주문을 찾을 수 없거나 연락처 끝 네 자리가 일치하지 않음"


def as_text(data):
    """도구 결과를 모델이 읽을 글로 바꾼다."""
    text = json.dumps(data, ensure_ascii=False)
    return {"content": [{"type": "text", "text": text}]}


@tool(
    "lookup_order",
    "주문번호와 연락처 끝 네 자리로 주문 한 건을 조회한다. "
    "상품, 수량, 결제 금액, 주문 상태, 송장번호, 주문 후 지난 날 수를 "
    "돌려준다. 두 값을 손님에게서 모두 받은 뒤에만 쓴다.",
    {"order_id": str, "phone_last4": str},
)
async def lookup_order(args):
    order = shop.lookup_order(args["order_id"], args["phone_last4"])
    return as_text(order or {"결과": NOT_FOUND})


@tool(
    "track_shipment",
    "송장번호로 택배사, 배송 상태, 현재 위치, 마지막 갱신일을 조회한다. "
    "송장번호는 lookup_order의 결과에서 얻는다.",
    {"tracking_no": str},
)
async def track_shipment(args):
    shipment = shop.track_shipment(args["tracking_no"])
    return as_text(shipment or {"결과": "배송 기록을 찾을 수 없음"})


@tool(
    "search_policy",
    "가게 정책 문서에서 낱말이 들어 있는 규정을 찾는다. 배송, 배송비, "
    "교환, 환불, 주문 변경, 취소, 선물 포장, 각인, 대량 구매를 다룬다. "
    "낱말은 띄어 써서 여러 개 줄 수 있다. 결과가 없으면 다른 낱말로 "
    "다시 찾는다.",
    {"keywords": str},
)
async def search_policy(args):
    found = shop.search_policy(args["keywords"])
    return as_text(found or {"결과": "해당 규정을 찾을 수 없음"})


SERVER = create_sdk_mcp_server(
    name="shop",
    tools=[lookup_order, track_shipment, search_policy],
)
TOOL_NAMES = [
    "mcp__shop__lookup_order",
    "mcp__shop__track_shipment",
    "mcp__shop__search_policy",
]
