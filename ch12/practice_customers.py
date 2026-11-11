"""연습용 손님. 켜져 있는 가게 서버에 대화 20건을 차례로 보낸다."""
import json
import sys
import urllib.request

SERVER = "http://localhost:8000"
CUSTOMERS = [
    ["안녕하세요. 주문한 지 좀 됐는데 배송이 궁금해서요.",
     "MG-2610-8955이고 끝자리는 5188이에요."],
    ["MG-2610-5211, 0376입니다. 북커버 환불할게요."],
    ["MG-2610-3172, 0990인데요. 배송 완료라고 뜨는데 문 앞에 아무것도 "
     "없어요."],
    ["현금영수증 발급되나요?"],
    ["MG-2610-6843, 1250이요. 각인 문구를 바꾸고 싶은데 가능한가요?"],
    ["할인 쿠폰 같은 거 없어요?"],
    ["Do you ship to Japan?"],
    ["아까 문의했던 사람인데요, 그 건 어떻게 됐어요?"],
    ["MG-2610-9404 7035랑 MG-2610-3333 9171 둘 다 어디쯤인지 알려 주세요."],
    ["사장님 전화번호 좀 알려 주세요. 직접 통화하고 싶어요."],
    ["모과 노트 5권 사면 배송비 포함해서 얼마예요?"],
    ["MG-2610-9318, 0231이에요. 2주째 안 와요. 그냥 환불해 주세요."],
    ["교환하려면 택배는 제가 불러야 하나요?"],
    ["영업시간이 어떻게 되나요?"],
    ["노트에 이름 각인하고 선물 포장도 같이 되나요?"],
    ["MG-2611-5706, 0188이요. 주소를 잘못 적었어요. 서울시 마포구 "
     "모과로 12로 바꿔 주세요."],
    ["MG-2610-3059, 0471이에요. 스티커 색이 화면이랑 달라요.",
     "환불로 해 주세요.", "언제쯤 돈이 들어와요?"],
    ["오후 3시에 결제했는데 오늘 출발하나요?"],
    ["MG-2610-5768 0227 리뷰 쓰면 적립금 주나요"],
    ["감사합니다. 잘 받았어요!"],
]


def post(path, body, visitor=""):
    request = urllib.request.Request(
        SERVER + path, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "X-Visitor": visitor})
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def main(count):
    for number, turns in enumerate(CUSTOMERS[:count], start=1):
        visitor = post("/api/visitors", {})["visitor"]
        for text in turns:
            post("/api/messages", {"text": text}, visitor)
        print(f"대화 {number} · {len(turns)}마디")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else len(CUSTOMERS))
