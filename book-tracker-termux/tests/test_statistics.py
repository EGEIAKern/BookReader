import unittest

from models.book import Book
from services.statistics_service import StatisticsService


class StatisticsServiceTests(unittest.TestCase):

    def test_compute_stats_empty(self):
        stats = StatisticsService.compute_stats([])
        self.assertEqual(stats["total_books"], 0)
        self.assertEqual(stats["percent"], 0)

    def test_compute_stats_with_books(self):
        books = [
            Book("A", "Author A", 100, 50),
            Book("B", "Author B", 200, 200),
        ]
        stats = StatisticsService.compute_stats(books)

        self.assertEqual(stats["total_books"], 2)
        self.assertEqual(stats["total_pages"], 300)
        self.assertEqual(stats["read_pages"], 250)
        self.assertEqual(stats["completed"], 1)
        self.assertEqual(stats["percent"], 83.3)

    def test_shorten_title(self):
        short = StatisticsService.shorten_title("Short title", max_length=20)
        long = StatisticsService.shorten_title("Very long book title here", max_length=10)
        self.assertEqual(short, "Short title")
        self.assertTrue(long.endswith("…"))
        self.assertLessEqual(len(long), 10)

    def test_format_book_label_includes_author(self):
        label = StatisticsService.format_book_label(Book("1984", "Orwell", 300, 0))
        self.assertIn("1984", label)
        self.assertIn("Orwell", label)


if __name__ == "__main__":
    unittest.main()
