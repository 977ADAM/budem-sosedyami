"""HTTP routes; the handlers only translate between HTTP and the use case."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path

from app.presentation.deps import AgentServiceDep, check_rate_limit
from app.presentation.schemas import ChatRequest, ChatResponse, ErrorResponse

router = APIRouter()


@router.get("/health", include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post(
    "/api/agents/{agent_id}/chat",
    response_model=ChatResponse,
    summary="Написать соседу",
    dependencies=[Depends(check_rate_limit)],
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
async def chat(
    chat_request: ChatRequest,
    agent_service: AgentServiceDep,
    agent_id: str = Path(description="ID соседа"),
) -> ChatResponse:
    result = await agent_service(agent_id, chat_request.message, chat_request.context)
    return ChatResponse(reply=result.reply, context=result.context)
