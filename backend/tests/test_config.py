import os
import unittest
from unittest.mock import patch

from langchain_deepseek.chat_models import DEFAULT_API_BASE

from app.infrastructure.config import Settings, load_settings
from app.infrastructure.deepseek import DeepSeekChatModel, build_chat_model


class LoadSettingsTests(unittest.TestCase):
    def load(self, **env: str) -> Settings:
        with patch.dict(os.environ, env, clear=True), patch("app.infrastructure.config.load_dotenv"):
            return load_settings()

    def build(self, **env: str) -> DeepSeekChatModel:
        with patch.dict(os.environ, env, clear=True), patch("app.infrastructure.config.load_dotenv"):
            model = build_chat_model(load_settings())
        self.assertIsInstance(model, DeepSeekChatModel)
        return model

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

    def test_standard_base_url_is_left_to_chatdeepseek(self) -> None:
        model = self.build(DEEPSEEK_API_KEY="key")
        self.assertEqual(model._llm.api_base, DEFAULT_API_BASE)
        self.assertNotIn("api_base", model._llm.model_fields_set)
