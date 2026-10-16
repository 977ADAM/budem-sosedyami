"""HTTP routes; the handlers only translate between HTTP and the use case."""

from __future__ import annotations

from fastapi import APIRouter, Path, Request
from slowapi import Limiter

from app.application.chat_with_neighbor import ChatWithNeighbor
from app.presentation.schemas import ChatRequest, ChatResponse, ErrorResponse


def build_router(limiter: Limiter, rate_limit: str, neighbor_ids: tuple[str, ...]) -> APIRouter:
    router = APIRouter()

    @router.get("/health", include_in_schema=False)
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.post(
        "/api/agents/{agent_id}/chat",
        response_model=ChatResponse,
        summary="Написать соседу",
        responses={
            status: {"model": ErrorResponse, "description": description}
            for status, description in {
                422: "Пустое или слишком длинное сообщение, неизвестный сосед",
                429: "Слишком много сообщений с одного адреса",
                502: "Модель вернула ошибку",
                503: "Модель не настроена",
                504: "Модель не ответила вовремя",
            }.items()
        },
    )
    @limiter.limit(rate_limit)
    async def chat(
        request: Request,
        chat_request: ChatRequest,
        agent_id: str = Path(description=f"ID соседа: {', '.join(neighbor_ids)}"),
    ) -> ChatResponse:
        chat_with_neighbor: ChatWithNeighbor = request.app.state.chat_with_neighbor
        result = await chat_with_neighbor(agent_id, chat_request.message, chat_request.context)
        return ChatResponse(reply=result.reply, context=result.context)

    return router
