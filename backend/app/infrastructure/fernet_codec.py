"""Conversation sealed with Fernet: the client can neither read nor forge the history."""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import zlib

from cryptography.fernet import Fernet, InvalidToken

from app.domain.conversation import Conversation, Turn

logger = logging.getLogger(__name__)


class FernetConversationCodec:
    def __init__(self, secret: str, ttl_seconds: int) -> None:
        self._fernet = Fernet(base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest()))
        self._ttl_seconds = ttl_seconds

    def seal(self, conversation: Conversation) -> str:
        payload = {
            "neighbor_id": conversation.neighbor_id,
            "turns": [[turn.message, turn.reply] for turn in conversation.turns],
        }
        raw = json.dumps(payload, ensure_ascii=False).encode()
        return self._fernet.encrypt(zlib.compress(raw)).decode()

    def unseal(self, token: str | None, neighbor_id: str) -> Conversation:
        empty = Conversation(neighbor_id)
        if not token:
            return empty
        try:
            raw = zlib.decompress(self._fernet.decrypt(token.encode(), ttl=self._ttl_seconds))
            payload = json.loads(raw)
            turns = tuple(Turn(message=message, reply=reply) for message, reply in payload["turns"])
        except (InvalidToken, ValueError, KeyError, TypeError, zlib.error):
            logger.info("Context rejected, starting a new conversation")
            return empty
        if payload.get("neighbor_id") != neighbor_id:
            return empty
        return Conversation(neighbor_id, turns)
