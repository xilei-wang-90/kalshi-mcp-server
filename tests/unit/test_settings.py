import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from kalshi_mcp.settings import load_settings


class SettingsTests(unittest.TestCase):
    def test_load_settings_reads_api_credentials_from_dotenv(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dotenv_path = Path(temp_dir) / ".env"
            dotenv_path.write_text(
                "\n".join(
                    [
                        "KALSHI_API_KEY_ID=test-id",
                        "KALSHI_API_KEY_PATH=/tmp/kalshi-test.pem",
                    ]
                ),
                encoding="utf-8",
            )

            with patch.dict(os.environ, {}, clear=True), patch(
                "kalshi_mcp.settings.Path.cwd",
                return_value=Path(temp_dir),
            ):
                settings = load_settings()

        self.assertEqual("test-id", settings.api_key_id)
        self.assertEqual("/tmp/kalshi-test.pem", settings.api_key_path)

    def test_environment_variables_override_dotenv(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dotenv_path = Path(temp_dir) / ".env"
            dotenv_path.write_text(
                "\n".join(
                    [
                        "KALSHI_API_KEY_ID=dotenv-id",
                        "KALSHI_API_KEY_PATH=/tmp/dotenv.pem",
                    ]
                ),
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {
                    "KALSHI_API_KEY_ID": "env-id",
                    "KALSHI_API_KEY_PATH": "/tmp/env.pem",
                },
                clear=True,
            ), patch(
                "kalshi_mcp.settings.Path.cwd",
                return_value=Path(temp_dir),
            ):
                settings = load_settings()

        self.assertEqual("env-id", settings.api_key_id)
        self.assertEqual("/tmp/env.pem", settings.api_key_path)


if __name__ == "__main__":
    unittest.main()
