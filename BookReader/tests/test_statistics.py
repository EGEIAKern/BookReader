import unittest

from models.book import Book
from ui.statistics_page import StatisticsPage


def _stats_page(books):
    page = object.__new__(StatisticsPage)
    page.books = books
    return page


class StatisticsPageTests(unittest.TestCase):

    def test_compute_stats_empty(self):
        stats = _stats_page([]).compute_stats()
        self.assertEqual(stats["total_books"], 0)
        self.assertEqual(stats["percent"], 0)

    def test_compute_stats_with_books(self):
        books = [
            Book("A", "Author A", 100, 50),
            Book("B", "Author B", 200, 200),
        ]
        stats = _stats_page(books).compute_stats()

        self.assertEqual(stats["total_books"], 2)
        self.assertEqual(stats["total_pages"], 300)
        self.assertEqual(stats["read_pages"], 250)
        self.assertEqual(stats["completed"], 1)
        self.assertEqual(stats["percent"], 83.3)

    def test_shorten_title(self):
        short = StatisticsPage.shorten_title("Short title", max_length=20)
        long = StatisticsPage.shorten_title("Very long book title here", max_length=10)
        self.assertEqual(short, "Short title")
        self.assertTrue(long.endswith("…"))
        self.assertLessEqual(len(long), 10)

    def test_bar_height_scales_down_for_many_books(self):
        few = StatisticsPage.bar_height_for_count(2)
        many = StatisticsPage.bar_height_for_count(20)
        self.assertGreater(few, many)
        self.assertLessEqual(few, 0.65)
        self.assertGreaterEqual(many, 0.22)

    def test_format_chart_label_includes_author(self):
        label = _stats_page([]).format_chart_label(Book("1984", "Orwell", 300, 0))
        self.assertIn("1984", label)
        self.assertIn("Orwell", label)


if __name__ == "__main__":
    unittest.main()
