from app.schemas.chat_schema import ChatResponse, ChatCard
from app.services.gemini_service import GeminiService
from app.services.intent_service import IntentService
from app.services.rag_service import RagService
from app.services.recommendation_service import RecommendationService
from app.services.spring_api_service import SpringApiService


class ChatbotService:
    def __init__(self):
        self.gemini = GeminiService()
        self.intent = IntentService()
        self.rag = RagService()
        self.recommender = RecommendationService()
        self.spring = SpringApiService()

    async def chat(self, *, message: str, authorization: str | None = None, history: list[dict] | None = None) -> ChatResponse:
        try:
            intent = self.intent.detect(message)

            if intent == "refund":
                rag_answer = self.rag.answer(message)
                return ChatResponse(answer=rag_answer or "환불 규정을 찾지 못했어요.", cards=[], intent=intent)

            if intent == "my_inquiry":
                if not authorization:
                    return ChatResponse(
                        answer="문의 내역을 보려면 로그인이 필요해요. 로그인한 상태에서 다시 말씀해 주세요.",
                        cards=[],
                        intent=intent,
                    )

                try:
                    data = await self.spring.get_my_inquiries(authorization)
                    items = (
                        data.get("items")
                        or data.get("content")
                        or data.get("list")
                        or []
                    )

                    if not items:
                        return ChatResponse(
                            answer="현재 문의 내역이 없어요.",
                            cards=[],
                            intent=intent,
                        )

                    lines = ["최근 문의 내역이에요."]
                    for item in items[:3]:
                        title = item.get("eventTitle") or item.get("title") or "행사"
                        content = item.get("content") or item.get("inquiryContent") or "문의 내용"
                        status = item.get("status") or item.get("answerStatus") or "상태 확인 필요"
                        lines.append(f"- {title}: {content} ({status})")

                    return ChatResponse(
                        answer="\n".join(lines),
                        cards=[],
                        intent=intent,
                    )
                except Exception as e:
                    print("[MY_INQUIRY ERROR]", repr(e))
                    return ChatResponse(
                        answer="문의 내역을 불러오는 중 문제가 생겼어요. 잠시 후 다시 시도해 주세요.",
                        cards=[],
                        intent=intent,
                    )

            if intent == "my_inquiry":
                # 기존 코드 그대로
                ...

            if intent == "recommend":
                answer, cards = await self.recommender.recommend(message=message, authorization=authorization)
                return ChatResponse(answer=answer, cards=[ChatCard(**c) for c in cards], intent=intent)

            faq = self.rag.answer(message)
            context = faq or "MOHAENG는 행사 추천, 검색, 문의, 환불 안내를 지원하는 플랫폼입니다."
            reply = await self.gemini.generate(history or [], message, context=context)

            return ChatResponse(answer=reply, cards=[], intent="chat")

        except Exception as e:
            print("[CHATBOT ERROR]", repr(e))
            return ChatResponse(
                answer="지금은 챗봇 응답을 준비하는 중 문제가 생겼어요. 잠시 후 다시 시도해 주세요.",
                cards=[],
                intent="fallback",
            )