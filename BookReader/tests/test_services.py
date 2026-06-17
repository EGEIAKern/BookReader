import math
import tempfile
import unittest
from pathlib import Path

from models.book import Book
from services.calculator_service import CalculatorService
from services.export_service import ExportService
from services.goal_service import GoalService
from services.percent_service import PercentService
from services.reading_service import ReadingService


class ReadingServiceTests(unittest.TestCase):

    def test_calculate_progress(self):
        self.assertEqual(ReadingService.calculate_progress(200, 50), 25.0)

    def test_rejects_zero_total_pages(self):
        with self.assertRaises(ValueError):
            ReadingService.calculate_progress(0, 10)


class PercentServiceTests(unittest.TestCase):

    def test_calculate_pages(self):
        self.assertEqual(PercentService.calculate_pages(500, 25), 125)

    def test_rejects_invalid_percent(self):
        with self.assertRaises(ValueError):
            PercentService.calculate_pages(100, 101)


class GoalServiceTests(unittest.TestCase):

    def test_pages_per_day_rounds_up(self):
        self.assertEqual(GoalService.pages_per_day(100, 30), math.ceil(100 / 30))

    def test_rejects_zero_days(self):
        with self.assertRaises(ValueError):
            GoalService.pages_per_day(100, 0)


class CalculatorServiceTests(unittest.TestCase):

    def test_basic_operations(self):
        self.assertEqual(CalculatorService.calculate(10, 3, "+"), 13)
        self.assertEqual(CalculatorService.calculate(10, 3, "-"), 7)
        self.assertEqual(CalculatorService.calculate(10, 3, "*"), 30)
        self.assertAlmostEqual(CalculatorService.calculate(10, 4, "/"), 2.5)

    def test_division_by_zero(self):
        with self.assertRaises(ZeroDivisionError):
            CalculatorService.calculate(1, 0, "/")

    def test_unknown_operator(self):
        with self.assertRaises(ValueError):
            CalculatorService.calculate(1, 2, "%")


class ExportServiceTests(unittest.TestCase):

    def test_export_creates_xlsx(self):
        books = [Book("Test Book", "Author", 100, 40)]
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "library"
            saved_path = ExportService.export_books_to_excel(books, file_path)
            self.assertEqual(saved_path.suffix, ".xlsx")
            self.assertTrue(saved_path.exists())
            self.assertGreater(saved_path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
