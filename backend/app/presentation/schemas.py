"""HTTP request and response bodies."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.conversation import MAX_MESSAGE_LENGTH

MAX_CONTEXT_LENGTH = 300_000
EXAMPLE_CONTEXT = "gAAAAABn3k…"


class ChatRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [
            {"message": "Где вы гуляете после школы?"},
            {"message": "А в выходные?", "context": EXAMPLE_CONTEXT},
        ]},
    )
    message: str = Field(
        min_length=1, max_length=MAX_MESSAGE_LENGTH, description="Сообщение пользователя"
    )
    context: str | None = Field(
        default=None,
        max_length=MAX_CONTEXT_LENGTH,
        description="`context` из предыдущего ответа. Без него начинается новый разговор.",
    )

    @field_validator("message")
    @classmethod
    def trim_message(cls, message: str) -> str:
        message = message.strip()
        if not message:
            raise ValueError("Message must not be blank")
        return message


class ChatResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [
        {"reply": "Во дворе есть место, где дети играют…", "context": EXAMPLE_CONTEXT},
    ]})
    reply: str = Field(description="Ответ соседа")
    context: str = Field(description="Передайте в следующем запросе, чтобы продолжить разговор")


class ErrorResponse(BaseModel):
    detail: str = Field(description="Текст ошибки, который можно показать пользователю")
