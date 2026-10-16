"""ChatModel backed by DeepSeek through LangChain and a one-node LangGraph."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from openai import APITimeoutError, OpenAIError

from app.application.errors import ChatModelFailed, ChatModelNotConfigured, ChatModelTimeout
from app.application.ports import ChatModel
from app.domain.conversation import Turn
from app.infrastructure.config import Settings

logger = logging.getLogger(__name__)


class DeepSeekChatModel:
    def __init__(self, llm: Any) -> None:
        self._llm = llm

        async def call_model(state: MessagesState) -> dict[str, list[BaseMessage]]:
            return {"messages": [await llm.ainvoke(state["messages"])]}

        builder = StateGraph(MessagesState)
        builder.add_node("call_model", call_model)
        builder.add_edge(START, "call_model")
        builder.add_edge("call_model", END)
        self._graph = builder.compile()

    async def reply(self, system_prompt: str, history: Sequence[Turn], message: str) -> str:
        messages: list[BaseMessage] = [SystemMessage(content=system_prompt)]
        for turn in history:
            messages += [HumanMessage(content=turn.message), AIMessage(content=turn.reply)]
        messages.append(HumanMessage(content=message))
        try:
            result = (await self._graph.ainvoke({"messages": messages}))["messages"][-1]
        except APITimeoutError as exc:
            raise ChatModelTimeout from exc
        except OpenAIError as exc:
            raise ChatModelFailed from exc

        self._log_usage(result)
        if not isinstance(result.content, str) or not result.content.strip():
            raise ChatModelFailed("Empty model response")
        return result.content.strip()

    async def aclose(self) -> None:
        client = getattr(self._llm, "root_async_client", None)
        if client is not None:
            await client.close()

    @staticmethod
    def _log_usage(result: BaseMessage) -> None:
        usage = getattr(result, "usage_metadata", None) or {}
        logger.info(
            "input_tokens=%s cached_tokens=%s output_tokens=%s",
            usage.get("input_tokens"),
            usage.get("input_token_details", {}).get("cache_read"),
            usage.get("output_tokens"),
        )


class UnconfiguredChatModel:
    async def reply(self, system_prompt: str, history: Sequence[Turn], message: str) -> str:
        raise ChatModelNotConfigured

    async def aclose(self) -> None:
        pass


def build_chat_model(settings: Settings) -> ChatModel:
    if not settings.deepseek_api_key:
        logger.warning("DEEPSEEK_API_KEY is not set: chat will answer 503")
        return UnconfiguredChatModel()
    return DeepSeekChatModel(
        ChatOpenAI(
            model=settings.deepseek_model,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            max_tokens=settings.deepseek_max_tokens,
            timeout=settings.deepseek_timeout_seconds,
            max_retries=0,
        )
    )
