import unittest

from models.book import Book, calc_progress


class BookTests(unittest.TestCase):

    def test_progress_halfway(self):
        book = Book("Title", "Author", 200, 100)
        self.assertEqual(book.progress, 50.0)

    def test_progress_completed(self):
        book = Book("Title", "Author", 100, 150)
        self.assertEqual(book.current_page, 100)
        self.assertEqual(book.progress, 100.0)

    def test_progress_zero_pages(self):
        book = Book("Title", "Author", 0, 0)
        self.assertEqual(book.progress, 0.0)

    def test_negative_values_clamped(self):
        book = Book("Title", "Author", 100, -10)
        self.assertEqual(book.current_page, 0)

    def test_title_and_author_stripped(self):
        book = Book("  Title  ", "  Author  ", 100, 0)
        self.assertEqual(book.title, "Title")
        self.assertEqual(book.author, "Author")

    def test_to_dict_and_from_dict(self):
        book = Book("1984", "Orwell", 328, 120)
        restored = Book.from_dict(book.to_dict())
        self.assertEqual(restored.title, book.title)
        self.assertEqual(restored.author, book.author)
        self.assertEqual(restored.total_pages, book.total_pages)
        self.assertEqual(restored.current_page, book.current_page)

    def test_calc_progress_clamps_current_page(self):
        self.assertEqual(calc_progress(100, 200), 100.0)
        self.assertEqual(calc_progress(100, -5), 0.0)
        self.assertEqual(calc_progress(0, 10), 0.0)


if __name__ == "__main__":
    unittest.main()
