import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app


class AgentChatTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.api_key = patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"})
        self.api_key.start()
        self.addCleanup(self.api_key.stop)

    def test_agent_chat_accepts_free_text_and_request_local_history(self) -> None:
        model = SimpleNamespace(
            ainvoke=AsyncMock(return_value=SimpleNamespace(content="Да, можно гулять в сквере."))
        )
        with patch("app.main.ChatOpenAI", return_value=model):
            with TestClient(app) as client:
                response = client.post(
                "/api/agents/marina/chat",
                json={
                    "message": "Можно ли после школы погулять рядом?",
                    "history": [
                        {
                            "message": "Как устроен обычный учебный день?",
                            "reply": "Мы с дочкой идём в школу пешком по спокойной улице.",
                        }
                    ],
                },
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"reply": "Да, можно гулять в сквере."})
        messages = model.ainvoke.await_args.args[0]
        self.assertEqual(messages[1], ("user", "Как устроен обычный учебный день?"))
        self.assertEqual(
            messages[2], ("assistant", "Мы с дочкой идём в школу пешком по спокойной улице.")
        )
        self.assertEqual(messages[3], ("user", "Можно ли после школы погулять рядом?"))

    def test_agent_chat_rejects_blank_or_oversized_messages(self) -> None:
        for message in ("   ", "а" * 501):
            with self.subTest(message_length=len(message)):
                response = self.client.post(
                    "/api/agents/anton/chat",
                    json={"message": message, "history": []},
                )
                self.assertEqual(response.status_code, 422)

    def test_agent_chat_rejects_unknown_agent_ids(self) -> None:
        response = self.client.post(
            "/api/agents/unknown/chat",
            json={"message": "Привет", "history": []},
        )
        self.assertEqual(response.status_code, 422)

    def test_model_is_created_once_for_the_application_lifespan(self) -> None:
        model = SimpleNamespace(
            ainvoke=AsyncMock(return_value=SimpleNamespace(content="Привет!")),
            root_async_client=SimpleNamespace(close=AsyncMock()),
        )
        with patch("app.main.ChatOpenAI", return_value=model) as model_factory:
            with TestClient(app) as client:
                for agent_id in ("anton", "marina"):
                    response = client.post(
                        f"/api/agents/{agent_id}/chat",
                        json={"message": "Привет", "history": []},
                    )
                    self.assertEqual(response.status_code, 200)

        model_factory.assert_called_once()
        model.root_async_client.close.assert_awaited_once()

    def test_cors_allows_local_frontend_origins(self) -> None:
        for origin in ("http://127.0.0.1:3000", "http://127.0.0.1:5173"):
            with self.subTest(origin=origin):
                response = self.client.options(
                    "/api/agents/marina/chat",
                    headers={
                        "Origin": origin,
                        "Access-Control-Request-Method": "POST",
                        "Access-Control-Request-Headers": "content-type",
                    },
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers["access-control-allow-origin"], origin)

    def test_cors_rejects_unlisted_origins(self) -> None:
        for origin in ("http://localhost:3000", "http://localhost:5173", "http://example.com"):
            with self.subTest(origin=origin):
                response = self.client.options(
                    "/api/agents/marina/chat",
                    headers={
                        "Origin": origin,
                        "Access-Control-Request-Method": "POST",
                    },
                )
                self.assertNotIn("access-control-allow-origin", response.headers)


if __name__ == "__main__":
    unittest.main()
