import os
import unittest
from unittest.mock import patch

from config import DEFAULT_LANGUAGE, DEFAULT_RECEIVER, load_config


class LoadConfigTest(unittest.TestCase):
    def setUp(self):
        self.base_env = {
            "ZOTERO_KEY": "test-zotero-key",
            "SMTP_SERVER": "smtp.example.com",
            "SMTP_PORT": "587",
            "SENDER": "bot@example.com",
            "SENDER_PASSWORD": "secret",
        }

    def test_defaults_and_runtime_zotero_id_resolution(self):
        with patch.dict(os.environ, self.base_env, clear=True):
            with patch("config._resolve_zotero_user_id", return_value="14776285") as mock_resolve:
                config = load_config([])

        self.assertEqual(config.zotero_id, "14776285")
        self.assertEqual(config.receiver, DEFAULT_RECEIVER)
        self.assertEqual(config.language, DEFAULT_LANGUAGE)
        self.assertEqual(config.max_paper_num, 5)
        mock_resolve.assert_called_once_with("test-zotero-key")

    def test_use_llm_api_requires_api_key(self):
        env = dict(self.base_env)
        env["USE_LLM_API"] = "true"
        with patch.dict(os.environ, env, clear=True):
            with patch("config._resolve_zotero_user_id", return_value="14776285"):
                with self.assertRaisesRegex(ValueError, "OPENAI_API_KEY"):
                    load_config([])

    def test_cli_zotero_id_skips_runtime_resolution(self):
        with patch.dict(os.environ, self.base_env, clear=True):
            with patch("config._resolve_zotero_user_id") as mock_resolve:
                config = load_config(["--zotero_id", "12345678"])

        self.assertEqual(config.zotero_id, "12345678")
        mock_resolve.assert_not_called()


if __name__ == "__main__":
    unittest.main()
