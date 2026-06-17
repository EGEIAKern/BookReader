import unittest

from models.book import Book
from models.work import Work
from services.sync_service import (
    merge_book_pair,
    merge_books,
    merge_reading_logs,
    parse_sync_bundle,
    serialize_sync_bundle,
    build_sync_bundle,
)


class SyncServiceTests(unittest.TestCase):

    def test_merge_books_adds_remote_only(self):
        local = [Book("Local", "Author", 100, 10)]
        remote = [Book("Remote", "Other", 200, 0)]

        merged, added, updated = merge_books(local, remote)

        self.assertEqual(len(merged), 2)
        self.assertEqual(added, 1)
        self.assertEqual(updated, 0)

    def test_merge_books_keeps_higher_progress(self):
        local = [Book("Dune", "Herbert", 688, 100)]
        remote = [Book("Dune", "Herbert", 688, 250)]

        merged, added, updated = merge_books(local, remote)

        self.assertEqual(len(merged), 1)
        self.assertEqual(added, 0)
        self.assertEqual(updated, 1)
        self.assertEqual(merged[0].current_page, 250)

    def test_merge_reading_logs_sums_days(self):
        local = {"2026-06-16": 10, "2026-06-17": 5}
        remote = {"2026-06-16": 7, "2026-06-18": 12}

        merged = merge_reading_logs(local, remote)

        self.assertEqual(merged["2026-06-16"], 17)
        self.assertEqual(merged["2026-06-17"], 5)
        self.assertEqual(merged["2026-06-18"], 12)

    def test_sync_bundle_roundtrip(self):
        books = [Book("Title", "Author", 120, 30)]
        log = {"2026-06-17": 15}
        bundle = build_sync_bundle(books, log, device_id="test-device")

        raw = serialize_sync_bundle(bundle)
        restored_books, restored_log = parse_sync_bundle(raw)

        self.assertEqual(len(restored_books), 1)
        self.assertEqual(restored_books[0].title, "Title")
        self.assertEqual(restored_log["2026-06-17"], 15)


if __name__ == "__main__":
    unittest.main()
