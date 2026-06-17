import json
import tempfile
import unittest
from pathlib import Path

from models.book import Book
from storage.storage import load_books, save_books


class StorageTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temp_dir.name) / "books.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_empty_when_file_missing(self):
        self.assertEqual(load_books(self.data_file), [])

    def test_save_and_load_roundtrip(self):
        books = [
            Book("Dune", "Herbert", 688, 200),
            Book("Foundation", "Asimov", 255, 255),
        ]
        save_books(books, self.data_file)
        loaded = load_books(self.data_file)

        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0].title, "Dune")
        self.assertEqual(loaded[1].progress, 100.0)

    def test_load_invalid_json_returns_empty_list(self):
        self.data_file.write_text("{not json", encoding="utf-8")
        self.assertEqual(load_books(self.data_file), [])

    def test_load_skips_invalid_entries(self):
        payload = [
            {"title": "Valid", "author": "Author", "total_pages": 100, "current_page": 10},
            {"title": "Broken", "total_pages": "not-a-number"},
            "not a dict",
        ]
        self.data_file.write_text(json.dumps(payload), encoding="utf-8")
        loaded = load_books(self.data_file)

        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].title, "Valid")

    def test_save_creates_parent_directory(self):
        nested_file = Path(self.temp_dir.name) / "nested" / "books.json"
        save_books([Book("Test", "Author", 50, 0)], nested_file)
        self.assertTrue(nested_file.exists())


if __name__ == "__main__":
    unittest.main()
