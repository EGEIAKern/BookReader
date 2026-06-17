import unittest

from models.book import Book
from models.progress import calc_progress
from models.work import Work, WORK_STATUS_FINISHED, WORK_STATUS_SKIPPED


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
        book = Book(
            "1984",
            "Orwell",
            328,
            120,
            description="Dystopian novel",
            marketplace_url="https://example.com/book",
            review="Great read",
        )
        restored = Book.from_dict(book.to_dict())
        self.assertEqual(restored.title, book.title)
        self.assertEqual(restored.author, book.author)
        self.assertEqual(restored.total_pages, book.total_pages)
        self.assertEqual(restored.current_page, book.current_page)
        self.assertEqual(restored.description, book.description)
        self.assertEqual(restored.marketplace_url, book.marketplace_url)
        self.assertEqual(restored.review, book.review)

    def test_optional_fields_default_empty(self):
        book = Book("Title", "Author", 100, 0)
        self.assertEqual(book.description, "")
        self.assertEqual(book.marketplace_url, "")
        self.assertEqual(book.review, "")
        self.assertEqual(book.works, [])

    def test_marketplace_url_normalized(self):
        book = Book("Title", "Author", 100, 0, marketplace_url="ozon.ru/product/123")
        self.assertEqual(book.marketplace_url, "https://ozon.ru/product/123")

    def test_is_finished(self):
        book = Book("Title", "Author", 100, 100)
        self.assertTrue(book.is_finished)
        book.current_page = 50
        self.assertFalse(book.is_finished)

    def test_calc_progress_clamps_current_page(self):
        self.assertEqual(calc_progress(100, 200), 100.0)
        self.assertEqual(calc_progress(100, -5), 0.0)
        self.assertEqual(calc_progress(0, 10), 0.0)

    def test_book_with_works_progress(self):
        book = Book(
            "Anthology",
            "Author",
            300,
            works=[
                Work("Story A", 100, 100, WORK_STATUS_FINISHED),
                Work("Story B", 100, 50, "reading"),
                Work("Story C", 100, 0, WORK_STATUS_SKIPPED),
            ],
        )
        self.assertTrue(book.has_works)
        self.assertEqual(book.effective_total_pages, 200)
        self.assertEqual(book.effective_current_page, 150)
        self.assertEqual(book.progress_total_pages, 300)
        self.assertEqual(book.progress, 50.0)
        self.assertEqual(book.current_page, 150)
        self.assertFalse(book.is_finished)

    def test_book_with_works_uses_book_total_when_allocated_differs(self):
        book = Book(
            "Collection",
            "Author",
            509,
            works=[
                Work("Story", 508, 508, WORK_STATUS_FINISHED),
            ],
        )
        self.assertEqual(book.effective_current_page, 508)
        self.assertEqual(book.progress_total_pages, 509)
        self.assertAlmostEqual(book.progress, round(508 / 509 * 100, 1))
        self.assertTrue(book.is_finished)

    def test_book_finished_when_all_active_works_done(self):
        book = Book(
            "Anthology",
            "Author",
            200,
            works=[
                Work("Story A", 100, 100, WORK_STATUS_FINISHED),
                Work("Story B", 100, 100, WORK_STATUS_FINISHED),
            ],
        )
        self.assertTrue(book.is_finished)

    def test_add_work_page(self):
        book = Book(
            "Anthology",
            "Author",
            200,
            works=[
                Work("Story A", 100, 0, "planned"),
                Work("Story B", 100, 0, "planned"),
            ],
        )
        added = book.add_work_page(1)
        self.assertEqual(added, 1)
        self.assertEqual(book.works[0].current_page, 1)
        self.assertEqual(book.works[0].status, "reading")

    def test_validate_works_pages_limit(self):
        book = Book(
            "Anthology",
            "Author",
            100,
            works=[Work("Story A", 60, 0), Work("Story B", 50, 0)],
        )
        with self.assertRaises(ValueError):
            book.validate_works()

    def test_works_roundtrip_in_dict(self):
        book = Book(
            "Anthology",
            "Author",
            200,
            works=[Work("Story A", 100, 40, "reading")],
        )
        restored = Book.from_dict(book.to_dict())
        self.assertEqual(len(restored.works), 1)
        self.assertEqual(restored.works[0].title, "Story A")
        self.assertEqual(restored.works[0].current_page, 40)


class WorkTests(unittest.TestCase):

    def test_finished_status_sets_current_page(self):
        work = Work("Poem", 20, 0, WORK_STATUS_FINISHED)
        self.assertEqual(work.current_page, 20)
        self.assertTrue(work.is_finished)

    def test_skipped_does_not_count_toward_progress(self):
        work = Work("Poem", 20, 0, WORK_STATUS_SKIPPED)
        self.assertFalse(work.counts_toward_progress)
        self.assertEqual(work.progress, 0.0)


if __name__ == "__main__":
    unittest.main()
