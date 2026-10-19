import tomllib
import unittest
from pathlib import Path

from fakes import build_test_app

from app.infrastructure.config import Settings

BACKEND_DIR = Path(__file__).resolve().parents[1]


class VersionTests(unittest.TestCase):
    def setUp(self) -> None:
        pyproject = tomllib.loads(
            (BACKEND_DIR / "pyproject.toml").read_text(encoding="utf-8")
        )
        self.version = str(pyproject["project"]["version"])

    def test_release_version_is_semver(self) -> None:
        self.assertRegex(self.version, r"^\d+\.\d+\.\d+$")

    def test_openapi_version_comes_from_pyproject(self) -> None:
        app = build_test_app(Settings(context_secret="s"))
        self.assertEqual(app.version, self.version)

    def test_main_has_no_hardcoded_version(self) -> None:
        source = (BACKEND_DIR / "app" / "main.py").read_text(encoding="utf-8")
        self.assertNotRegex(source, r'version="\d+\.\d+\.\d+"')
        self.assertIn("_project_version()", source)
