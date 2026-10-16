from collections.abc import Sequence

from app.domain.conversation import Turn


class FakeChatModel:
    def __init__(self, reply: str = "Ответ") -> None:
        self.reply_text = reply
        self.error: Exception | None = None
        self.calls: list[tuple[str, list[Turn], str]] = []
        self.closed = False

    async def reply(self, system_prompt: str, history: Sequence[Turn], message: str) -> str:
        self.calls.append((system_prompt, list(history), message))
        if self.error is not None:
            raise self.error
        return self.reply_text

    async def aclose(self) -> None:
        self.closed = True

    @property
    def last_dialog(self) -> list[str]:
        _, history, message = self.calls[-1]
        return [text for turn in history for text in (turn.message, turn.reply)] + [message]
