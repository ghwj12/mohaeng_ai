import re


REGION_ALIAS = {
    "강남": ("서울", 1100000000),
    "잠실": ("서울", 1100000000),
    "홍대": ("서울", 1100000000),
    "성수": ("서울", 1100000000),
    "서울": ("서울", 1100000000),

    "판교": ("경기", 4100000000),
    "수원": ("경기", 4100000000),
    "성남": ("경기", 4100000000),
    "경기": ("경기", 4100000000),

    "인천": ("인천", 2800000000),
    "부산": ("부산", 2600000000),
    "해운대": ("부산", 2600000000),
    "대구": ("대구", 2700000000),
    "광주": ("광주", 2900000000),
    "대전": ("대전", 3000000000),
    "울산": ("울산", 3100000000),
    "세종": ("세종", 3611000000),

    "전주": ("전북", 5200000000),
    "전북": ("전북", 5200000000),
    "광주광역시": ("광주", 2900000000),
    "전남": ("전남", 4600000000),
    "목포": ("전남", 4600000000),
    "순천": ("전남", 4600000000),

    "강원": ("강원", 5100000000),
    "강릉": ("강원", 5100000000),
    "춘천": ("강원", 5100000000),

    "충북": ("충북", 4300000000),
    "충남": ("충남", 4400000000),
    "경북": ("경북", 4700000000),
    "경남": ("경남", 4800000000),
    "제주": ("제주", 5000000000),
    "서귀포": ("제주", 5000000000),
}


class IntentService:
    def detect(self, message: str) -> str:
        text = (message or "").strip().lower()

        if any(x in text for x in ["안녕", "하이", "반가", "고마워", "감사", "뭐 할 수", "도움말"]):
            return "smalltalk"

        if "문의" in text and any(x in text for x in ["내", "나한테", "보여", "알려", "목록", "내역"]):
            return "my_inquiry"

        if "환불" in text or "취소" in text:
            return "refund"

        if any(x in text for x in ["추천", "행사 알려", "행사 찾아", "근처 행사", "신청 가능한 행사"]):
            return "recommend"

        if any(x in text for x in ["일정", "달력", "언제", "이번 주", "이번주"]):
            return "recommend"

        return "chat"

    def extract_region(self, message: str):
        text = (message or "").strip()
        for alias, (name, region_id) in REGION_ALIAS.items():
            if alias in text:
                return {
                    "alias": alias,
                    "name": name,
                    "regionId": region_id,
                }
        return None

    def wants_open_only(self, message: str) -> bool:
        text = (message or "").strip()
        return any(x in text for x in ["신청 가능", "모집중", "모집 중", "참여 모집", "신청할 수"])

    def wants_nearby(self, message: str) -> bool:
        text = (message or "").strip()
        return any(x in text for x in ["근처", "주변", "인근"])

    def extract_keyword(self, message: str) -> str | None:
        text = (message or "").strip()
        cleaned = re.sub(r"(추천해줘|알려줘|찾아줘|보여줘|행사|근처|주변|인근|신청 가능한|모집중|모집 중)", " ", text)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned or None