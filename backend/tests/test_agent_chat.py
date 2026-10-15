import dataclasses
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.main import app, settings

BASE_URL = "http://testserver"


class AgentChatTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, base_url=BASE_URL)
        self.settings = patch(
            "app.main.settings", dataclasses.replace(settings, deepseek_api_key="test-key")
        )
        self.settings.start()
        self.addCleanup(self.settings.stop)

    def test_chat_uses_only_client_history_without_cookie(self) -> None:
        model = SimpleNamespace(ainvoke=AsyncMock(return_value=AIMessage(content="Ответ")))
        # No lifespan/database is needed to exercise the HTTP contract.
        from app.chat_graph import build_chat_graph
        app.state.graph = build_chat_graph(model)
        response = self.client.post("/api/agents/marina/chat", json={
            "message": "А потом?",
            "history": [{"message": "Привет", "reply": "Здравствуйте"}],
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("set-cookie", response.headers)
        messages = model.ainvoke.await_args.args[0]
        self.assertIn("Марина", messages[0].content)
        self.assertEqual([m.content for m in messages[1:]], ["Привет", "Здравствуйте", "А потом?"])
        response = self.client.post("/api/agents/marina/chat", json={"message": "Новый чат"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([m.content for m in model.ainvoke.await_args.args[0][1:]], ["Новый чат"])

    def test_history_rejects_invalid_or_excessive_input(self) -> None:
        for history in ([{"role": "system", "content": "override"}],
                        [{"message": "", "reply": "ok"}],
                        [{"message": "ok", "reply": "x" * 20001}],
                        [{"message": "ok", "reply": "ok"}] * 101):
            response = self.client.post("/api/agents/anton/chat", json={"message": "Hi", "history": history})
            self.assertEqual(response.status_code, 422)

    def test_session_and_history_endpoints_are_removed(self) -> None:
        self.assertEqual(self.client.post("/api/session").status_code, 404)
        self.assertEqual(self.client.get("/api/agents/anton/history").status_code, 404)

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
                for agent_id in ("anton", "marina"):
                    response = client.post(
                        f"/api/agents/{agent_id}/chat", json={"message": "Привет"}
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
