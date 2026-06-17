from models.book import Book


class StatisticsService:
    READING_CHART_DAYS = 14

    @staticmethod
    def compute_stats(books: list[Book]) -> dict:
        total_books = len(books)
        total_pages = sum(book.total_pages for book in books)
        read_pages = sum(book.current_page for book in books)
        completed = sum(1 for book in books if book.progress >= 100)

        percent = 0.0
        if total_pages:
            percent = round(read_pages / total_pages * 100, 1)

        return {
            "total_books": total_books,
            "total_pages": total_pages,
            "read_pages": read_pages,
            "completed": completed,
            "percent": percent,
        }

    @staticmethod
    def shorten_title(title: str, max_length: int = 18) -> str:
        if len(title) <= max_length:
            return title
        return title[: max_length - 1] + "…"

    @staticmethod
    def format_book_label(book: Book, max_title: int = 28, max_author: int = 18) -> str:
        title = StatisticsService.shorten_title(book.title, max_title)
        if book.author:
            author = StatisticsService.shorten_title(book.author, max_author)
            return f"{title} — {author}"
        return title
