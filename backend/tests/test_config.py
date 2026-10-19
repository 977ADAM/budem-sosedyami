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
        self.assertEqual(settings.max_retries, 0)
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

    def test_invalid_numeric_settings_fail_with_the_environment_variable_name(self) -> None:
        cases = [
            ("DEEPSEEK_MAX_TOKENS", "0"),
            ("DEEPSEEK_MAX_TOKENS", "-1"),
            ("DEEPSEEK_MAX_TOKENS", "abc"),
            ("DEEPSEEK_TIMEOUT_SECONDS", "0"),
            ("DEEPSEEK_TIMEOUT_SECONDS", "-0.1"),
            ("DEEPSEEK_TIMEOUT_SECONDS", "nan"),
            ("DEEPSEEK_TIMEOUT_SECONDS", "inf"),
            ("DEEPSEEK_TIMEOUT_SECONDS", "abc"),
            ("CONTEXT_TTL_SECONDS", "0"),
            ("CONTEXT_TTL_SECONDS", "-1"),
            ("CONTEXT_TTL_SECONDS", "abc"),
            ("MAX_RETRIES", "-1"),
            ("MAX_RETRIES", "1"),
            ("MAX_RETRIES", "abc"),
        ]
        for name, value in cases:
            with self.subTest(name=name, value=value):
                with self.assertRaisesRegex(ValueError, name):
                    self.load(**{name: value})

    def test_zero_retries_and_small_positive_values_are_allowed(self) -> None:
        settings = self.load(
            MAX_RETRIES="0", DEEPSEEK_TIMEOUT_SECONDS="0.1",
            DEEPSEEK_MAX_TOKENS="1", CONTEXT_TTL_SECONDS="1",
        )
        self.assertEqual(settings.max_retries, 0)
        self.assertEqual(settings.deepseek_timeout_seconds, 0.1)
        self.assertEqual(settings.deepseek_max_tokens, 1)
        self.assertEqual(settings.context_ttl_seconds, 1)

    def test_direct_settings_construction_is_validated(self) -> None:
        for kwargs, name in [
            ({"deepseek_max_tokens": 0}, "DEEPSEEK_MAX_TOKENS"),
            ({"deepseek_timeout_seconds": float("nan")}, "DEEPSEEK_TIMEOUT_SECONDS"),
            ({"context_ttl_seconds": -1}, "CONTEXT_TTL_SECONDS"),
            ({"max_retries": -1}, "MAX_RETRIES"),
        ]:
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, name):
                    Settings(**kwargs)

    def test_invalid_rate_limits_fail_at_startup(self) -> None:
        for value in ["", "20/minut", "abc", "0/minute", "-1/minute", "1/0 minute"]:
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "RATE_LIMIT"):
                    self.load(RATE_LIMIT=value)
                with self.assertRaisesRegex(ValueError, "RATE_LIMIT"):
                    Settings(rate_limit=value)

    def test_supported_rate_limit_formats_are_allowed(self) -> None:
        for value in ["20/minute", "1/second", "100 per 5 minutes", "10/minute;100/hour"]:
            with self.subTest(value=value):
                self.assertEqual(self.load(RATE_LIMIT=value).rate_limit, value)
