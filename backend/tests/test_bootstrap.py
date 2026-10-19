import logging
import subprocess
import sys
import unittest
from pathlib import Path

from fakes import build_test_app
from fastapi.testclient import TestClient

from app.infrastructure.config import Settings

BACKEND_DIR = Path(__file__).resolve().parents[1]
IMPORT_ONLY = (
    "import logging\n"
    "import app.main\n"
    "print(logging.getLogger('app').level, len(logging.getLogger().handlers))\n"
)


class BootstrapTests(unittest.TestCase):
    def test_importing_the_app_does_not_touch_logging(self) -> None:
        result = subprocess.run(
            [sys.executable, "-c", IMPORT_ONLY],
            cwd=BACKEND_DIR,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(result.stdout.strip(), "0 0", result.stderr)

    def test_building_the_app_does_not_touch_logging(self) -> None:
        before = logging.getLogger("app").level
        build_test_app(Settings(context_secret="s"))
        self.assertEqual(logging.getLogger("app").level, before)

    def test_lifespan_applies_the_configured_log_level(self) -> None:
        root, app_logger = logging.getLogger(), logging.getLogger("app")
        saved_level, saved_handlers = app_logger.level, root.handlers[:]
        try:
            with TestClient(build_test_app(Settings(context_secret="s", log_level="WARNING"))):
                pass
            self.assertEqual(app_logger.level, logging.WARNING)
        finally:
            app_logger.setLevel(saved_level)
            root.handlers[:] = saved_handlers

    def test_settings_are_available_on_app_state(self) -> None:
        settings = Settings(context_secret="s")
        app = build_test_app(settings)
        self.assertIs(app.state.settings, settings)
