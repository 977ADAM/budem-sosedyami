import json
import unittest
from unittest.mock import patch

import httpx2 as httpx
from openai import AsyncOpenAI

from app.application.errors import ChatModelFailed, ChatModelNotConfigured, ChatModelTimeout
from app.domain.conversation import Turn
from app.infrastructure.config import Settings
from app.infrastructure.deepseek import DeepSeekChatModel, UnconfiguredChatModel, build_chat_model


class DeepSeekChatModelTests(unittest.IsolatedAsyncioTestCase):
    def model(self, handler):
        client = AsyncOpenAI(
            api_key="key", base_url="https://api.deepseek.com", max_retries=0,
            _strict_response_validation=True,
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        )
        self.addAsyncCleanup(client.close)
        return DeepSeekChatModel(client, model="deepseek-chat", max_tokens=123)

    def response(self, content="  Ответ  ", finish_reason="stop", usage=None):
        return httpx.Response(200, json={
            "id": "chat-1", "object": "chat.completion", "created": 1,
            "model": "deepseek-chat",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": content},
                         "finish_reason": finish_reason}],
            "usage": usage,
        })

    async def test_sends_system_prompt_history_and_message_in_order(self):
        requests = []

        def handler(request):
            requests.append(request)
            return self.response()

        reply = await self.model(handler).reply(
            "Ты — Антон", [Turn("Привет", "Здравствуйте")], "Где кофе?"
        )
        self.assertEqual(reply, "Ответ")
        self.assertEqual(str(requests[0].url), "https://api.deepseek.com/chat/completions")
        self.assertEqual(json.loads(requests[0].content), {
            "model": "deepseek-chat", "max_tokens": 123,
            "messages": [
                {"role": "system", "content": "Ты — Антон"},
                {"role": "user", "content": "Привет"},
                {"role": "assistant", "content": "Здравствуйте"},
                {"role": "user", "content": "Где кофе?"},
            ],
        })

    async def test_provider_failures_become_application_errors(self):
        for error, expected in [
            (httpx.ReadTimeout("timeout"), ChatModelTimeout),
            (httpx.ConnectError("offline"), ChatModelFailed),
        ]:
            with self.subTest(expected.__name__):
                def handler(request, error=error):
                    raise error
                with self.assertRaises(expected):
                    await self.model(handler).reply("system", [], "Привет")

    async def test_http_error_is_a_failure(self):
        model = self.model(lambda request: httpx.Response(500, json={"error": "failed"}))
        with self.assertRaises(ChatModelFailed):
            await model.reply("system", [], "Привет")

    async def test_empty_reply_is_a_failure(self):
        for content in ["   ", None]:
            with self.subTest(content=content):
                model = self.model(lambda request, content=content: self.response(content))
                with self.assertRaises(ChatModelFailed):
                    await model.reply("system", [], "Привет")

    async def test_missing_choices_is_a_failure(self):
        model = self.model(lambda request: httpx.Response(200, json={
            "id": "chat-1", "object": "chat.completion", "created": 1,
            "model": "deepseek-chat", "choices": [],
        }))
        with self.assertRaises(ChatModelFailed):
            await model.reply("system", [], "Привет")

    async def test_logs_usage_and_truncation(self):
        model = self.model(lambda request: self.response(finish_reason="length", usage={
            "prompt_tokens": 20, "completion_tokens": 5, "total_tokens": 25,
            "prompt_cache_hit_tokens": 12,
        }))
        with self.assertLogs("app.infrastructure.deepseek", level="INFO") as logs:
            await model.reply("system", [], "Привет")
        output = "\n".join(logs.output)
        self.assertIn("input_tokens=20 cached_tokens=12 output_tokens=5 finish_reason=length", output)
        self.assertIn("cut off", output)

    async def test_aclose_closes_the_http_client(self):
        model = self.model(lambda request: self.response())
        await model.aclose()
        self.assertTrue(model._client.is_closed())

    async def test_missing_api_key_gives_an_unconfigured_model(self):
        model = build_chat_model(Settings(deepseek_api_key=""))
        self.assertIsInstance(model, UnconfiguredChatModel)
        with self.assertRaises(ChatModelNotConfigured):
            await model.reply("system", [], "Привет")

    async def test_configures_client_timeout_and_retries(self):
        model = build_chat_model(Settings(
            deepseek_api_key="key", deepseek_timeout_seconds=12.5, max_retries=0,
        ))
        self.addAsyncCleanup(model.aclose)
        self.assertIsInstance(model._client, AsyncOpenAI)
        self.assertEqual(str(model._client.base_url).rstrip("/"), "https://api.deepseek.com")
        self.assertEqual(model._client.timeout, 12.5)
        self.assertEqual(model._client.max_retries, 0)

    async def test_provider_errors_are_not_retried_with_default_settings(self):
        for failure in [429, 500, "timeout", "connection"]:
            with self.subTest(failure=failure):
                requests = []

                def handler(request, requests=requests, failure=failure):
                    requests.append(request)
                    if failure == "timeout":
                        raise httpx.ReadTimeout("timeout")
                    if failure == "connection":
                        raise httpx.ConnectError("offline")
                    return httpx.Response(failure, json={"error": {"message": "failed"}})

                def client_factory(**kwargs):
                    return AsyncOpenAI(
                        **kwargs,
                        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
                    )

                with patch("app.infrastructure.deepseek.AsyncOpenAI", side_effect=client_factory):
                    model = build_chat_model(Settings(deepseek_api_key="key"))
                self.addAsyncCleanup(model.aclose)
                expected = ChatModelTimeout if failure == "timeout" else ChatModelFailed
                with self.assertRaises(expected):
                    await model.reply("system", [], "Привет")
                self.assertEqual(len(requests), 1)

    async def test_malformed_provider_responses_are_failures(self):
        responses = [
            httpx.Response(200, text="broken JSON", headers={"content-type": "application/json"}),
            httpx.Response(200, json={}),
            httpx.Response(200, json={"choices": [{"message": None}]}),
        ]
        for response in responses:
            with self.subTest(body=response.text):
                model = self.model(lambda request, response=response: response)
                with self.assertRaises(ChatModelFailed):
                    await model.reply("system", [], "Привет")
