import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from openai import APIConnectionError, APITimeoutError

from app.application.errors import ChatModelFailed, ChatModelNotConfigured, ChatModelTimeout
from app.domain.conversation import Turn
from app.infrastructure.config import Settings
from app.infrastructure.deepseek import DeepSeekChatModel, UnconfiguredChatModel, build_chat_model


class DeepSeekChatModelTests(unittest.IsolatedAsyncioTestCase):
    def llm(self, **kwargs) -> SimpleNamespace:
        return SimpleNamespace(ainvoke=AsyncMock(**kwargs))

    async def test_sends_system_prompt_history_and_message_in_order(self) -> None:
        llm = self.llm(return_value=AIMessage(content="  Ответ  "))
        model = DeepSeekChatModel(llm)

        reply = await model.reply("Ты — Антон", [Turn("Привет", "Здравствуйте")], "Где кофе?")

        self.assertEqual(reply, "Ответ")
        messages = llm.ainvoke.await_args.args[0]
        self.assertEqual(
            [(type(m), m.content) for m in messages],
            [
                (SystemMessage, "Ты — Антон"),
                (HumanMessage, "Привет"),
                (AIMessage, "Здравствуйте"),
                (HumanMessage, "Где кофе?"),
            ],
        )

    async def test_provider_failures_become_application_errors(self) -> None:
        cases = [
            (APITimeoutError(request=None), ChatModelTimeout),
            (APIConnectionError(request=None), ChatModelFailed),
        ]
        for error, expected in cases:
            with self.subTest(expected.__name__):
                model = DeepSeekChatModel(self.llm(side_effect=error))
                with self.assertRaises(expected):
                    await model.reply("system", [], "Привет")

    async def test_empty_reply_is_a_failure(self) -> None:
        model = DeepSeekChatModel(self.llm(return_value=AIMessage(content="   ")))
        with self.assertRaises(ChatModelFailed):
            await model.reply("system", [], "Привет")

    async def test_aclose_closes_the_http_client(self) -> None:
        llm = self.llm()
        llm.root_async_client = SimpleNamespace(close=AsyncMock())
        await DeepSeekChatModel(llm).aclose()
        llm.root_async_client.close.assert_awaited_once()

    async def test_missing_api_key_gives_an_unconfigured_model(self) -> None:
        model = build_chat_model(Settings(deepseek_api_key=""))
        self.assertIsInstance(model, UnconfiguredChatModel)
        with self.assertRaises(ChatModelNotConfigured):
            await model.reply("system", [], "Привет")

    def test_api_key_gives_a_deepseek_model_with_limited_output(self) -> None:
        model = build_chat_model(Settings(deepseek_api_key="key", deepseek_max_tokens=123))
        self.assertIsInstance(model, DeepSeekChatModel)
        self.assertEqual(model._llm.max_tokens, 123)
