"""조회 함수를 에이전트의 도구로 등록한다."""
import json

from claude_agent_sdk import create_sdk_mcp_server, tool

import shop

NOT_FOUND = shop.NOT_FOUND


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


@tool(
    "request_refund",
    "교환이나 환불 요청을 승인 대기 목록에 올린다. 교환이나 환불을 "
    "실행하지 않는다. 사장이 승인한 뒤에 처리된다. 손님이 주문번호, "
    "연락처 끝 네 자리, 종류(환불 또는 교환), 사유를 모두 말한 뒤에만 "
    "쓴다. 접수되면 접수번호를 손님에게 알려 준다.",
    {"order_id": str, "phone_last4": str, "kind": str, "reason": str},
)
async def request_refund(args):
    return as_text(shop.create_request(
        args["order_id"], args["phone_last4"],
        args["kind"], args["reason"],
    ))


@tool(
    "handoff_to_owner",
    "에이전트가 처리할 수 없는 문의를 사장에게 넘긴다. 배송 지연 항의, "
    "정책 문서에 답이 없는 문의, 손님이 사람과 이야기하기를 원할 때 "
    "쓴다. summary에는 대화를 세 줄로, 한 줄에 80자 이하로 요약한다. "
    "첫 줄은 손님이 원하는 "
    "것, 둘째 줄은 확인된 사실, 셋째 줄은 지금까지 안내한 내용이다. "
    "주문에 관한 문의면 order_id와 phone_last4를 넣고, 주문이 없는 "
    "문의면 둘을 비우고 reply_to에 손님의 이메일을 넣는다. kind는 "
    "배송 지연 또는 기타다. 넘긴 뒤 인계번호를 손님에게 알려 준다. "
    "이미 넘긴 주문에 새 내용이 생기면 전체 요약을 다시 써서 한 번 더 "
    "호출한다.",
    {"kind": str, "summary": str, "order_id": str,
     "phone_last4": str, "reply_to": str},
)
async def handoff_to_owner(args):
    return as_text(shop.create_handoff(
        args["kind"], args["summary"], args.get("order_id", ""),
        args.get("phone_last4", ""), args.get("reply_to", ""),
    ))


SERVER = create_sdk_mcp_server(
    name="shop",
    tools=[lookup_order, track_shipment, search_policy, request_refund,
           handoff_to_owner],
)
TOOL_NAMES = [
    "mcp__shop__lookup_order",
    "mcp__shop__track_shipment",
    "mcp__shop__search_policy",
    "mcp__shop__request_refund",
    "mcp__shop__handoff_to_owner",
]
