class RagService:
    REFUND_TEXT = (
        "환불 규정 안내입니다.\n\n"
        "- 행사 시작 7일 전 취소: 전액 환불\n"
        "- 행사 시작 3~6일 전 취소: 50% 환불\n"
        "- 행사 시작 2일 전 ~ 당일 취소: 환불 불가\n"
        "- 주최자 사정으로 취소되거나 반려된 경우: 전액 환불\n"
        "- 실제 결제/환불 처리 시점은 PG사 또는 결제 수단 처리 일정에 따라 다를 수 있습니다."
    )

    FAQ = {
        "신청": "행사 상세 페이지에서 행사 상태가 '행사참여모집중'일 때 신청을 진행할 수 있어요.",
        "문의": "행사 상세 페이지에서 문의를 남길 수 있고, 마이페이지에서 작성 문의와 받은 문의를 확인할 수 있어요.",
        "찜": "관심 행사는 찜 기능으로 저장할 수 있고, 마이페이지에서 다시 볼 수 있어요.",
        "달력": "달력 페이지에서는 지역별 날짜별 행사 분포를 확인할 수 있어요.",
        "지도": "지도 페이지에서는 지역을 클릭해서 해당 지역 행사 흐름을 확인할 수 있어요.",
    }

    def answer(self, message: str) -> str | None:
        text = (message or "").strip()

        if "환불" in text or "취소" in text:
            return self.REFUND_TEXT

        for key, value in self.FAQ.items():
            if key in text:
                return value

        return None