import unittest

from fakes import FakeChatModel
from fastapi.testclient import TestClient

from app.application.errors import ChatModelFailed
from app.infrastructure.config import Settings
from app.main import create_app

SETTINGS = Settings(context_secret="secret", rate_limit="1000/minute")
SECRET_TEXT = "Мой адрес Ленина 5"


class LoggingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = FakeChatModel(reply="Понятно")
        self.client = TestClient(create_app(SETTINGS, self.model))

    def test_every_response_has_a_request_id(self) -> None:
        generated = self.client.post("/api/agents/anton/chat", json={"message": "Привет"})
        self.assertRegex(generated.headers["X-Request-ID"], r"^[0-9a-f]{12}$")

        echoed = self.client.post(
            "/api/agents/anton/chat", json={"message": "Привет"}, headers={"X-Request-ID": "front-42"}
        )
        self.assertEqual(echoed.headers["X-Request-ID"], "front-42")

        unsafe = self.client.post(
            "/api/agents/anton/chat", json={"message": "Привет"}, headers={"X-Request-ID": "a b\nc"}
        )
        self.assertNotEqual(unsafe.headers["X-Request-ID"], "a b\nc")

    def test_access_log_has_method_path_status_and_duration(self) -> None:
        with self.assertLogs("app.http", level="INFO") as logs:
            self.client.post("/api/agents/anton/chat", json={"message": "Привет"})
        self.assertRegex(logs.output[-1], r"POST /api/agents/anton/chat 200 \d+ms client=")

    def test_chat_log_has_sizes_but_never_the_conversation_text(self) -> None:
        with self.assertLogs("app", level="DEBUG") as logs:
            first = self.client.post("/api/agents/marina/chat", json={"message": SECRET_TEXT})
            self.client.post(
                "/api/agents/marina/chat",
                json={"message": SECRET_TEXT, "context": first.json()["context"]},
            )
        output = "\n".join(logs.output)
        self.assertIn("conversation=new history_turns=0", output)
        self.assertIn("conversation=continued history_turns=1", output)
        self.assertNotIn(SECRET_TEXT, output)
        self.assertNotIn("Понятно", output)

    def test_rejected_context_is_explained(self) -> None:
        with self.assertLogs("app", level="INFO") as logs:
            self.client.post("/api/agents/anton/chat", json={"message": "Hi", "context": "garbage"})
        self.assertIn("invalid signature", "\n".join(logs.output))

    def test_errors_are_logged_with_their_status(self) -> None:
        self.model.error = ChatModelFailed()
        with self.assertLogs("app", level="WARNING") as logs:
            self.client.post("/api/agents/anton/chat", json={"message": "Hi"})
            self.client.post("/api/agents/anton/chat", json={"message": "   "})
        output = "\n".join(logs.output)
        self.assertIn("ERROR:app.presentation.errors:ChatModelFailed -> 502", output)
        self.assertIn("Invalid request: body.message:value_error", output)
