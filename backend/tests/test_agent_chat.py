import dataclasses
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.main import app, settings

# The session cookie is Secure by default, so the client must use an https base URL.
BASE_URL = "https://testserver"


class AgentChatTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, base_url=BASE_URL)
        self.settings = patch(
            "app.main.settings", dataclasses.replace(settings, deepseek_api_key="test-key")
        )
        self.settings.start()
        self.addCleanup(self.settings.stop)

    def test_agent_chat_keeps_history_in_the_server_session(self) -> None:
        model = SimpleNamespace(
            ainvoke=AsyncMock(
                side_effect=[
                    AIMessage(content="Мы с дочкой идём в школу пешком."),
                    AIMessage(content="Да, можно гулять в сквере."),
                ]
            )
        )
        with patch("app.main.ChatOpenAI", return_value=model):
            with TestClient(app, base_url=BASE_URL) as client:
                self.assertEqual(client.post("/api/session").status_code, 204)
                first = client.post(
                    "/api/agents/marina/chat",
                    json={"message": "Как устроен обычный учебный день?", "question_id": "school"},
                )
                second = client.post(
                    "/api/agents/marina/chat",
                    json={"message": "Можно ли после школы погулять рядом?"},
                )
                history = client.get("/api/agents/marina/history")
                other_agent_history = client.get("/api/agents/anton/history")
                client.delete("/api/session")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.json(), {"reply": "Да, можно гулять в сквере."})
        messages = model.ainvoke.await_args.args[0]
        self.assertIsInstance(messages[0], SystemMessage)
        self.assertEqual(
            [(type(m), m.content) for m in messages[1:]],
            [
                (HumanMessage, "Как устроен обычный учебный день?"),
                (AIMessage, "Мы с дочкой идём в школу пешком."),
                (HumanMessage, "Можно ли после школы погулять рядом?"),
            ],
        )
        self.assertEqual(
            history.json(),
            {
                "turns": [
                    {
                        "message": "Как устроен обычный учебный день?",
                        "reply": "Мы с дочкой идём в школу пешком.",
                        "question_id": "school",
                    },
                    {
                        "message": "Можно ли после школы погулять рядом?",
                        "reply": "Да, можно гулять в сквере.",
                        "question_id": None,
                    },
                ]
            },
        )
        self.assertEqual(other_agent_history.json(), {"turns": []})

    def test_agent_chat_requires_a_session(self) -> None:
        with TestClient(app, base_url=BASE_URL) as client:
            response = client.post("/api/agents/anton/chat", json={"message": "Привет"})
        self.assertEqual(response.status_code, 401)

    def test_agent_chat_rejects_client_supplied_history(self) -> None:
        response = self.client.post(
            "/api/agents/anton/chat",
            json={"message": "Привет", "history": []},
        )
        self.assertEqual(response.status_code, 422)

    def test_agent_chat_rejects_blank_or_oversized_messages(self) -> None:
        for message in ("   ", "а" * 501):
            with self.subTest(message_length=len(message)):
                response = self.client.post("/api/agents/anton/chat", json={"message": message})
                self.assertEqual(response.status_code, 422)

    def test_agent_chat_rejects_unknown_agent_ids(self) -> None:
        response = self.client.post("/api/agents/unknown/chat", json={"message": "Привет"})
        self.assertEqual(response.status_code, 422)

    def test_model_is_created_once_for_the_application_lifespan(self) -> None:
        model = SimpleNamespace(
            ainvoke=AsyncMock(return_value=AIMessage(content="Привет!")),
            root_async_client=SimpleNamespace(close=AsyncMock()),
        )
        with patch("app.main.ChatOpenAI", return_value=model) as model_factory:
            with TestClient(app, base_url=BASE_URL) as client:
                self.assertEqual(client.post("/api/session").status_code, 204)
                for agent_id in ("anton", "marina"):
                    response = client.post(
                        f"/api/agents/{agent_id}/chat", json={"message": "Привет"}
                    )
                    self.assertEqual(response.status_code, 200)
                client.delete("/api/session")

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
