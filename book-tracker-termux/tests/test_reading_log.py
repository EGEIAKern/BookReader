import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from services.reading_log_service import ReadingLogService
from storage.reading_log import load_reading_log, save_reading_log


class ReadingLogStorageTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temp_dir.name) / "reading_log.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_empty_when_file_missing(self):
        self.assertEqual(load_reading_log(self.data_file), {})

    def test_save_and_load_roundtrip(self):
        log = {"2026-06-16": 5, "2026-06-17": 15}
        save_reading_log(log, self.data_file)
        loaded = load_reading_log(self.data_file)

        self.assertEqual(loaded, log)

    def test_load_invalid_json_returns_empty_dict(self):
        self.data_file.write_text("{not json", encoding="utf-8")
        self.assertEqual(load_reading_log(self.data_file), {})


class ReadingLogServiceTests(unittest.TestCase):

    def test_record_pages_accumulates_for_same_day(self):
        log = {}
        ReadingLogService.record_pages(log, 5, day=date(2026, 6, 17))
        ReadingLogService.record_pages(log, 10, day=date(2026, 6, 17))

        self.assertEqual(log["2026-06-17"], 15)

    def test_record_pages_ignores_non_positive_values(self):
        log = {"2026-06-17": 5}
        ReadingLogService.record_pages(log, 0, day=date(2026, 6, 17))
        ReadingLogService.record_pages(log, -3, day=date(2026, 6, 17))

        self.assertEqual(log["2026-06-17"], 5)

    def test_get_daily_series_fills_missing_days_with_zero(self):
        log = {"2026-06-16": 5, "2026-06-17": 15}
        series = ReadingLogService.get_daily_series(
            log,
            days=3,
            end_day=date(2026, 6, 17),
        )

        self.assertEqual(len(series), 3)
        self.assertEqual(series[-2]["pages"], 5)
        self.assertEqual(series[-1]["pages"], 15)
        self.assertEqual(series[0]["pages"], 0)

    def test_total_and_average_pages(self):
        series = [
            {"pages": 5},
            {"pages": 15},
            {"pages": 0},
        ]

        self.assertEqual(ReadingLogService.total_pages(series), 20)
        self.assertEqual(ReadingLogService.average_pages(series), 6.7)


if __name__ == "__main__":
    unittest.main()
