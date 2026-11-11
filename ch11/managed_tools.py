"""tools.py의 도구를 Managed Agents의 사용자 정의 도구로 바꾼다."""
import asyncio

import tools

SHOP_TOOLS = [tools.lookup_order, tools.track_shipment, tools.search_policy,
              tools.request_refund, tools.handoff_to_owner]
# 비워 둘 수 있는 입력. 나머지는 모두 필수다.
OPTIONAL = {"handoff_to_owner": ["order_id", "phone_last4", "reply_to"]}
HANDLERS = {tool.name: tool.handler for tool in SHOP_TOOLS}


def declare(tool):
    """도구 하나의 이름, 설명, 입력 형식을 선언문으로 만든다."""
    optional = OPTIONAL.get(tool.name, [])
    return {
        "type": "custom",
        "name": tool.name,
        "description": tool.description,
        "input_schema": {
            "type": "object",
            "properties": {key: {"type": "string"}
                           for key in tool.input_schema},
            "required": [key for key in tool.input_schema
                         if key not in optional],
        },
    }


DECLARATIONS = [declare(tool) for tool in SHOP_TOOLS]


def run(name, args):
    """도구를 이 컴퓨터에서 실행하고 결과를 글로 돌려준다."""
    if name not in HANDLERS:
        return f"없는 도구: {name}"
    result = asyncio.run(HANDLERS[name](args))
    return result["content"][0]["text"]
