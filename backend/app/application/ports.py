"""What the use cases need from the outside world; implemented in infrastructure."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from app.domain.conversation import Conversation, Turn
from app.domain.neighbor import Neighbor


class NeighborRepository(Protocol):
    def get(self, neighbor_id: str) -> Neighbor | None: ...


class ChatModel(Protocol):
    async def reply(self, system_prompt: str, history: Sequence[Turn], message: str) -> str:
        """Raises ChatModelNotConfigured, ChatModelTimeout or ChatModelFailed."""
        ...

    async def aclose(self) -> None: ...


class ConversationCodec(Protocol):
    """Packs a conversation into an opaque token that the client sends back."""

    def seal(self, conversation: Conversation) -> str: ...

    def unseal(self, token: str | None, neighbor_id: str) -> Conversation:
        """Returns an empty conversation for a missing, expired, forged or foreign token."""
        ...
