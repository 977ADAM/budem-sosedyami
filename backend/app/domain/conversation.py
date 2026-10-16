"""A conversation with one neighbor and the rules for how much of it is remembered."""

from __future__ import annotations

from dataclasses import dataclass

MAX_MESSAGE_LENGTH = 500
MAX_TURNS = 30


@dataclass(frozen=True, slots=True)
class Turn:
    message: str
    reply: str


@dataclass(frozen=True, slots=True)
class Conversation:
    neighbor_id: str
    turns: tuple[Turn, ...] = ()

    def with_turn(self, turn: Turn) -> Conversation:
        """Forgets old turns in blocks, so the start of the conversation stays the same
        for many requests in a row (the model provider caches that prefix)."""
        turns = (*self.turns, turn)
        if len(turns) > MAX_TURNS:
            turns = turns[-(MAX_TURNS // 2):]
        return Conversation(self.neighbor_id, turns)
