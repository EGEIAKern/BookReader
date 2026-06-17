import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from storage.paths import get_data_dir


class PathsTests(unittest.TestCase):

    def test_default_data_dir_is_project_data(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("BOOK_TRACKER_DATA", None)
            os.environ.pop("PREFIX", None)
            data_dir = get_data_dir()
            self.assertTrue(str(data_dir).endswith("data"))

    def test_book_tracker_data_env_override(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            custom = Path(temp_dir) / "custom-data"
            with patch.dict(os.environ, {"BOOK_TRACKER_DATA": str(custom)}):
                self.assertEqual(get_data_dir(), custom)

    def test_termux_uses_home_directory(self):
        with patch.dict(
            os.environ,
            {"PREFIX": "/data/data/com.termux/files/usr"},
            clear=False,
        ):
            data_dir = get_data_dir()
            self.assertIn(".book-tracker", str(data_dir))


if __name__ == "__main__":
    unittest.main()
