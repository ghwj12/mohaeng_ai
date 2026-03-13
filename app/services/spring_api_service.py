from __future__ import annotations
from typing import Any
import httpx
from app.core.config import settings


class SpringApiService:
    def __init__(self) -> None:
        self.base_url = settings.SPRING_API_BASE_URL.rstrip("/")
        self.timeout = httpx.Timeout(20.0, connect=10.0)

    def _headers(self, authorization: str | None = None) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if authorization:
            headers["Authorization"] = authorization
        return headers

    async def _get(
        self,
        path: str,
        *,
        authorization: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            res = await client.get(path, headers=self._headers(authorization), params=params)
            res.raise_for_status()
            return res.json()

    async def search_events(
        self,
        *,
        keyword: str | None = None,
        region_id: int | None = None,
        hide_closed: bool = True,
        event_status: str | None = None,
        page: int = 0,
        size: int = 12,
    ) -> list[dict]:
        params: dict[str, Any] = {
            "page": page,
            "size": size,
            "hideClosed": str(hide_closed).lower(),
        }
        if keyword:
            params["keyword"] = keyword
        if region_id:
            params["regionId"] = region_id
        if event_status:
            params["eventStatus"] = event_status

        data = await self._get("/api/events/search", params=params)

        # 다양한 응답 형태 방어
        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            if isinstance(data.get("content"), list):
                return data["content"]
            if isinstance(data.get("items"), list):
                return data["items"]
            if isinstance(data.get("list"), list):
                return data["list"]
            if isinstance(data.get("data"), list):
                return data["data"]
            if isinstance(data.get("data"), dict):
                nested = data["data"]
                if isinstance(nested.get("content"), list):
                    return nested["content"]
                if isinstance(nested.get("items"), list):
                    return nested["items"]

        return []

    async def recommend_events(self, authorization: str | None = None) -> list[dict]:
        data = await self._get("/api/events/recommend", authorization=authorization)

        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            if isinstance(data.get("content"), list):
                return data["content"]
            if isinstance(data.get("items"), list):
                return data["items"]
            if isinstance(data.get("list"), list):
                return data["list"]
            if isinstance(data.get("data"), list):
                return data["data"]

        return []

    async def get_my_inquiries(self, authorization: str) -> dict:
        data = await self._get(
            "/api/eventInquiry/mypage",
            authorization=authorization,
            params={"tab": "ALL", "page": 0, "size": 5},
        )
        return data if isinstance(data, dict) else {}