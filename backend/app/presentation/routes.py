"""HTTP routes; the handlers only translate between HTTP and the use case."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request
from slowapi import Limiter

from app.application.agent_service import ChatWithNeighbor
from app.presentation.schemas import ChatRequest, ChatResponse, ErrorResponse


def get_chat_with_neighbor(request: Request) -> ChatWithNeighbor:
    """The use case is wired in `main.create_app`; a missing one is a wiring bug."""
    use_case = getattr(request.app.state, "chat_with_neighbor", None)
    if not isinstance(use_case, ChatWithNeighbor):
        raise RuntimeError("chat_with_neighbor is not configured")
    return use_case


ChatWithNeighborDep = Annotated[ChatWithNeighbor, Depends(get_chat_with_neighbor)]


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
                500: "Непредвиденная ошибка сервера",
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
        chat_with_neighbor: ChatWithNeighborDep,
        agent_id: str = Path(description=f"ID соседа: {', '.join(neighbor_ids)}"),
    ) -> ChatResponse:
        result = await chat_with_neighbor(agent_id, chat_request.message, chat_request.context)
        return ChatResponse(reply=result.reply, context=result.context)

    return router
