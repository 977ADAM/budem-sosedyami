"""Use case: the user writes to a neighbor and continues the conversation."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.application.errors import NeighborNotFound
from app.application.ports import ChatModel, ConversationCodec, NeighborRepository
from app.application.prompt import build_system_prompt
from app.domain.conversation import Turn

# Logs carry sizes and counts only: conversation text is personal data.
logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ChatResult:
    reply: str
    context: str


class ChatWithNeighbor:
    def __init__(
        self, neighbors: NeighborRepository, model: ChatModel, codec: ConversationCodec
    ) -> None:
        self._neighbors = neighbors
        self._model = model
        self._codec = codec

    async def __call__(self, neighbor_id: str, message: str, context: str | None) -> ChatResult:
        neighbor = self._neighbors.get(neighbor_id)
        if neighbor is None:
            raise NeighborNotFound(neighbor_id)
        conversation = self._codec.unseal(context, neighbor.id)
        if context and not conversation.turns:
            logger.info("neighbor=%s context not accepted, starting a new conversation", neighbor.id)

        reply = await self._model.reply(build_system_prompt(neighbor), conversation.turns, message)
        updated = conversation.with_turn(Turn(message=message, reply=reply))
        sealed = self._codec.seal(updated)

        logger.info(
            "neighbor=%s conversation=%s history_turns=%d message_chars=%d reply_chars=%d "
            "turns_after=%d trimmed=%s context_bytes=%d",
            neighbor.id,
            "continued" if conversation.turns else "new",
            len(conversation.turns),
            len(message),
            len(reply),
            len(updated.turns),
            len(updated.turns) <= len(conversation.turns),
            len(sealed),
        )
        return ChatResult(reply=reply, context=sealed)
