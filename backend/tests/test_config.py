import os
import unittest
from unittest.mock import patch

from app.infrastructure.config import Settings, load_settings


class LoadSettingsTests(unittest.TestCase):
    def load(self, **env: str) -> Settings:
        with patch.dict(os.environ, env, clear=True), patch("app.infrastructure.config.load_dotenv"):
            return load_settings()

    def test_defaults_are_used_without_environment(self) -> None:
        settings = self.load()
        self.assertEqual(settings.deepseek_model, "deepseek-flash")
        self.assertEqual(settings.deepseek_max_tokens, 1000)
        self.assertEqual(settings.deepseek_timeout_seconds, 30.0)

    def test_deepseek_timeout_comes_from_the_environment(self) -> None:
        settings = self.load(DEEPSEEK_TIMEOUT_SECONDS="12.5")
        self.assertEqual(settings.deepseek_timeout_seconds, 12.5)

    def test_model_and_limit_still_come_from_the_environment(self) -> None:
        settings = self.load(DEEPSEEK_MODEL="deepseek-chat", DEEPSEEK_MAX_TOKENS="777")
        self.assertEqual(settings.deepseek_model, "deepseek-chat")
        self.assertEqual(settings.deepseek_max_tokens, 777)
