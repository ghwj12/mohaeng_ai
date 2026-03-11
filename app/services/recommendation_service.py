from __future__ import annotations
from typing import List, Tuple
from app.services.spring_api_service import SpringApiService
from app.services.intent_service import IntentService


class RecommendationService:
    def __init__(self):
        self.spring = SpringApiService()
        self.intent = IntentService()

    def _extract_region_text(self, event: dict) -> str:
        region = event.get("region")

        if isinstance(region, dict):
            return (
                region.get("regionName")
                or region.get("name")
                or ""
            )

        if isinstance(region, str):
            return region

        parent = event.get("parent")
        if isinstance(parent, dict):
            return parent.get("regionName") or parent.get("name") or ""

        return (
            event.get("regionName")
            or event.get("lotNumberAdr")
            or event.get("address")
            or ""
        )

    def _normalize_card(self, event: dict, idx: int) -> dict:
        if not isinstance(event, dict):
            event = {}

        event_id = (
            event.get("eventId")
            or event.get("id")
            or event.get("EVENT_ID")
            or event.get("event_id")
        )

        title = event.get("title") or event.get("eventTitle") or "추천 행사"
        description = (
            event.get("simpleExplain")
            or event.get("description")
            or event.get("eventDesc")
            or ""
        )
        region = self._extract_region_text(event)

        start_date = event.get("startDate") or event.get("start_date") or ""
        end_date = event.get("endDate") or event.get("end_date") or ""
        status = event.get("eventStatus") or event.get("status") or ""
        thumbnail = (
            event.get("thumbnail")
            or event.get("thumbnailUrl")
            or event.get("thumbUrl")
            or ""
        )

        return {
            "eventId": event_id,
            "title": str(title),
            "description": str(description),
            "region": str(region),
            "startDate": str(start_date),
            "endDate": str(end_date),
            "thumbnail": str(thumbnail),
            "eventStatus": str(status),
            "detailUrl": f"/events/{event_id}" if event_id else "",
            "applyUrl": f"/events/{event_id}/apply" if event_id and status == "행사참여모집중" else "",
        }

    def _match_region(self, region_text: str, region_name: str, alias: str | None) -> bool:
        text = (region_text or "").replace(" ", "")
        rn = (region_name or "").replace(" ", "")
        al = (alias or "").replace(" ", "")

        if not rn and not al:
            return True
        if rn and rn in text:
            return True
        if al and al in text:
            return True
        return False

    async def recommend(self, message: str, authorization: str | None = None) -> Tuple[str, List[dict]]:
        region = self.intent.extract_region(message)
        open_only = self.intent.wants_open_only(message)
        keyword = self.intent.extract_keyword(message)

        candidates: list[dict] = []

        if region:
            candidates = await self.spring.search_events(
                keyword=keyword,
                region_id=region.get("regionId"),
                hide_closed=True,
                event_status="행사참여모집중" if open_only else None,
                size=12,
            )
        else:
            try:
                candidates = await self.spring.recommend_events(authorization=authorization)
            except Exception:
                candidates = []

            if not candidates:
                candidates = await self.spring.search_events(
                    keyword=keyword,
                    hide_closed=True,
                    event_status="행사참여모집중" if open_only else None,
                    size=12,
                )

        cards = [self._normalize_card(item, idx) for idx, item in enumerate(candidates or [])]
        cards = [c for c in cards if c.get("eventStatus") != "행사종료"]

        if open_only:
            cards = [c for c in cards if c.get("eventStatus") == "행사참여모집중"]

        if region:
            cards = [
                c for c in cards
                if self._match_region(c.get("region", ""), region.get("name", ""), region.get("alias"))
            ]

        cards = cards[:6]

        if not cards:
            return (
                "조건에 맞는 행사를 아직 찾지 못했어요. 지역이나 키워드를 조금 더 구체적으로 말씀해 주세요.",
                [],
            )

        if region and open_only:
            answer = f"{region['alias']} 기준으로 지금 신청 가능한 행사를 먼저 골라봤어요. 카드에서 바로 상세 페이지로 이동할 수 있어요."
        elif region:
            answer = f"{region['alias']} 기준으로 행사를 먼저 골라봤어요. 카드에서 바로 상세 페이지로 이동할 수 있어요."
        elif open_only:
            answer = "지금 신청 가능한 행사 위주로 골라봤어요. 카드에서 상세 페이지로 바로 이동할 수 있어요."
        else:
            answer = "조건에 맞는 행사를 먼저 골라봤어요. 카드에서 바로 상세 페이지로 이동할 수 있어요."

        return answer, cards