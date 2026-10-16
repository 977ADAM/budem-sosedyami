from __future__ import annotations

import logging
import time
from collections.abc import Sequence

from langchain_core.messages import AIMessage, AnyMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_deepseek import ChatDeepSeek
from openai import APITimeoutError, OpenAIError
from pydantic import SecretStr

from app.application.errors import ChatModelFailed, ChatModelNotConfigured, ChatModelTimeout
from app.application.ports import ChatModel
from app.domain.conversation import Turn
from app.infrastructure.config import Settings

logger = logging.getLogger(__name__)


class DeepSeekChatModel:
    def __init__(self, llm: ChatDeepSeek) -> None:
        self._llm = llm

    async def reply(self, system_prompt: str, history: Sequence[Turn], message: str) -> str:
        messages: list[AnyMessage] = [SystemMessage(content=system_prompt)]
        for turn in history:
            messages += [HumanMessage(content=turn.message), AIMessage(content=turn.reply)]
        messages.append(HumanMessage(content=message))
        started = time.perf_counter()
        try:
            result = await self._llm.ainvoke(messages)
        except APITimeoutError as exc:
            logger.error("DeepSeek timed out after %.0fms", self._elapsed_ms(started))
            raise ChatModelTimeout from exc
        except OpenAIError as exc:
            logger.error(
                "DeepSeek failed after %.0fms: %s status=%s %s",
                self._elapsed_ms(started),
                type(exc).__name__,
                getattr(exc, "status_code", "-"),
                exc,
            )
            raise ChatModelFailed from exc

        self._log_usage(result, self._elapsed_ms(started), len(messages))
        if not isinstance(result.content, str) or not result.content.strip():
            logger.error("DeepSeek returned an empty reply")
            raise ChatModelFailed("Empty model response")
        return result.content.strip()

    async def aclose(self) -> None:
        client = getattr(self._llm, "root_async_client", None)
        if client is not None:
            await client.close()

    @staticmethod
    def _elapsed_ms(started: float) -> float:
        return (time.perf_counter() - started) * 1000

    @staticmethod
    def _log_usage(result: BaseMessage, elapsed_ms: float, sent_messages: int) -> None:
        usage = getattr(result, "usage_metadata", None) or {}
        metadata = getattr(result, "response_metadata", None) or {}
        logger.info(
            "DeepSeek replied in %.0fms model=%s messages=%d input_tokens=%s cached_tokens=%s "
            "output_tokens=%s finish_reason=%s",
            elapsed_ms,
            metadata.get("model_name", "-"),
            sent_messages,
            usage.get("input_tokens"),
            usage.get("input_token_details", {}).get("cache_read"),
            usage.get("output_tokens"),
            metadata.get("finish_reason", "-"),
        )
        if metadata.get("finish_reason") == "length":
            logger.warning("DeepSeek reply was cut off by DEEPSEEK_MAX_TOKENS")


class UnconfiguredChatModel:
    async def reply(self, system_prompt: str, history: Sequence[Turn], message: str) -> str:
        raise ChatModelNotConfigured

    async def aclose(self) -> None:
        pass


def build_chat_model(settings: Settings) -> ChatModel:

    if not settings.deepseek_api_key:
        logger.warning("DEEPSEEK_API_KEY не задан: чат будет отвечать с кодом 503")
        return UnconfiguredChatModel()

    return DeepSeekChatModel(
        ChatDeepSeek(
            model = str(settings.deepseek_model), # type: ignore[call-arg]
            api_key = SecretStr(settings.deepseek_api_key),
            max_tokens = settings.deepseek_max_tokens,
            timeout = settings.deepseek_timeout_seconds,
            max_retries = settings.max_retries
        )
    )
