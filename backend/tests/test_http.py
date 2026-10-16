import unittest

from fakes import FakeChatModel
from fastapi.testclient import TestClient

from app.application.errors import ChatModelFailed, ChatModelNotConfigured, ChatModelTimeout
from app.infrastructure.config import Settings
from app.main import create_app

SETTINGS = Settings(context_secret="secret", rate_limit="1000/minute")


class HttpApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = FakeChatModel()
        self.client = TestClient(create_app(SETTINGS, self.model))

    def send(self, agent_id: str, message: str, context: str | None = None):
        payload = {"message": message} if context is None else {"message": message, "context": context}
        return self.client.post(f"/api/agents/{agent_id}/chat", json=payload)

    def test_contract_returns_reply_and_context_without_cookies(self) -> None:
        first = self.send("marina", "  Привет  ")
        self.assertEqual(first.status_code, 200)
        self.assertNotIn("set-cookie", first.headers)
        self.assertEqual(set(first.json()), {"reply", "context"})

        self.send("marina", "А потом?", first.json()["context"])
        self.assertEqual(self.model.last_dialog, ["Привет", "Ответ", "А потом?"])

    def test_errors_return_a_readable_detail(self) -> None:
        cases = [
            ("anton", {"message": "   "}, 422, "Сообщение должно быть от 1 до 500 символов"),
            ("anton", {"message": "а" * 501}, 422, "Сообщение должно быть от 1 до 500 символов"),
            ("unknown", {"message": "Привет"}, 422, "Неизвестный сосед"),
            ("anton", {"message": "Hi", "context": "x" * 300_001}, 422, "Некорректный context"),
            ("anton", {"message": "Hi", "history": []}, 422, "Некорректный запрос"),
        ]
        for agent_id, payload, status, detail in cases:
            with self.subTest(agent_id=agent_id, payload=str(payload)[:40]):
                response = self.client.post(f"/api/agents/{agent_id}/chat", json=payload)
                self.assertEqual((response.status_code, response.json()), (status, {"detail": detail}))

    def test_model_errors_map_to_status_codes(self) -> None:
        cases = [
            (ChatModelNotConfigured(), 503, "Сосед сейчас недоступен: модель не настроена"),
            (ChatModelTimeout(), 504, "Сосед не ответил вовремя, попробуйте ещё раз"),
            (ChatModelFailed(), 502, "Сосед не смог ответить, попробуйте ещё раз"),
        ]
        for error, status, detail in cases:
            with self.subTest(status=status):
                self.model.error = error
                response = self.send("anton", "Привет")
                self.assertEqual((response.status_code, response.json()), (status, {"detail": detail}))

    def test_rate_limit_returns_a_readable_429(self) -> None:
        client = TestClient(create_app(Settings(context_secret="s", rate_limit="2/minute"), FakeChatModel()))
        statuses = [client.post("/api/agents/anton/chat", json={"message": "Hi"}).status_code for _ in range(3)]
        last = client.post("/api/agents/anton/chat", json={"message": "Hi"})
        self.assertEqual(statuses, [200, 200, 429])
        self.assertEqual(last.json(), {"detail": "Слишком много сообщений, подождите минуту"})

    def test_model_is_closed_on_shutdown(self) -> None:
        with TestClient(create_app(SETTINGS, self.model)):
            self.assertFalse(self.model.closed)
        self.assertTrue(self.model.closed)

    def test_cors_allows_only_configured_origins(self) -> None:
        for origin, allowed in (
            ("http://127.0.0.1:3000", True),
            ("http://localhost:3000", True),
            ("http://example.com", False),
        ):
            with self.subTest(origin=origin):
                response = self.client.options(
                    "/api/agents/marina/chat",
                    headers={
                        "Origin": origin,
                        "Access-Control-Request-Method": "POST",
                        "Access-Control-Request-Headers": "content-type",
                    },
                )
                self.assertEqual(response.headers.get("access-control-allow-origin") == origin, allowed)

    def test_openapi_documents_the_single_endpoint(self) -> None:
        schema = self.client.get("/openapi.json").json()
        self.assertEqual(list(schema["paths"]), ["/api/agents/{agent_id}/chat"])
