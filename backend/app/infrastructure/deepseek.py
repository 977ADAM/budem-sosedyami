from __future__ import annotations

import logging
import time
from collections.abc import Sequence

from openai import APITimeoutError, AsyncOpenAI, OpenAIError
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam

from app.application.errors import ChatModelFailed, ChatModelNotConfigured, ChatModelTimeout
from app.application.ports import ChatModel
from app.domain.conversation import Turn
from app.infrastructure.config import Settings

logger = logging.getLogger(__name__)


class DeepSeekChatModel:
    def __init__(self, client: AsyncOpenAI, *, model: str, max_tokens: int) -> None:
        self._client = client
        self._model = model
        self._max_tokens = max_tokens

    async def reply(self, system_prompt: str, history: Sequence[Turn], message: str) -> str:
        messages: list[ChatCompletionMessageParam] = [{"role": "system", "content": system_prompt}]
        for turn in history:
            messages += [
                {"role": "user", "content": turn.message},
                {"role": "assistant", "content": turn.reply},
            ]
        messages.append({"role": "user", "content": message})
        started = time.perf_counter()
        try:
            result = await self._client.chat.completions.create(
                model=self._model, messages=messages, max_tokens=self._max_tokens
            )
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
        content = result.choices[0].message.content if result.choices else None
        if not isinstance(content, str) or not content.strip():
            logger.error("DeepSeek returned an empty reply")
            raise ChatModelFailed("Empty model response")
        return content.strip()

    async def aclose(self) -> None:
        await self._client.close()

    @staticmethod
    def _elapsed_ms(started: float) -> float:
        return (time.perf_counter() - started) * 1000

    @staticmethod
    def _log_usage(result: ChatCompletion, elapsed_ms: float, sent_messages: int) -> None:
        usage = result.usage
        finish_reason = result.choices[0].finish_reason if result.choices else "-"
        logger.info(
            "DeepSeek replied in %.0fms model=%s messages=%d input_tokens=%s cached_tokens=%s "
            "output_tokens=%s finish_reason=%s",
            elapsed_ms,
            result.model,
            sent_messages,
            usage.prompt_tokens if usage else None,
            getattr(usage, "prompt_cache_hit_tokens", None),
            usage.completion_tokens if usage else None,
            finish_reason,
        )
        if finish_reason == "length":
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
        AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url="https://api.deepseek.com",
            timeout=settings.deepseek_timeout_seconds,
            max_retries=settings.max_retries,
        ),
        model=settings.deepseek_model,
        max_tokens=settings.deepseek_max_tokens,
    )
