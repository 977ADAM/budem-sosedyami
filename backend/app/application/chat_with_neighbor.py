"""Use case: the user writes to a neighbor and continues the conversation."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.errors import NeighborNotFound
from app.application.ports import ChatModel, ConversationCodec, NeighborRepository
from app.application.prompt import build_system_prompt
from app.domain.conversation import Turn


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
        reply = await self._model.reply(build_system_prompt(neighbor), conversation.turns, message)
        updated = conversation.with_turn(Turn(message=message, reply=reply))
        return ChatResult(reply=reply, context=self._codec.seal(updated))
