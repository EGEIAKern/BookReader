from models.book import Book
from services.reading_log_service import ReadingLogService
from services.statistics_service import StatisticsService

from cli.display import clear_screen, horizontal_bar, pause, print_header


class StatisticsScreen:
    CHART_DAYS = StatisticsService.READING_CHART_DAYS

    def __init__(self, books: list[Book], reading_log: dict[str, int]):
        self.books = books
        self.reading_log = reading_log

    def run(self) -> None:
        clear_screen()
        print_header("📊 Статистика чтения")

        stats = StatisticsService.compute_stats(self.books)
        print(
            f"\n  Книг: {stats['total_books']}   "
            f"Страниц: {stats['total_pages']}   "
            f"Прочитано: {stats['read_pages']}   "
            f"Завершено: {stats['completed']}"
        )
        print(f"\n  Общий прогресс: {stats['percent']}%")
        print(f"  {horizontal_bar(stats['percent'], 100, width=30)}")

        self._reading_chart()
        self._books_chart()
        pause("\nEnter — в меню")

    def _reading_chart(self) -> None:
        series = ReadingLogService.get_daily_series(
            self.reading_log,
            days=self.CHART_DAYS,
        )
        total = ReadingLogService.total_pages(series)
        average = ReadingLogService.average_pages(series)

        print(f"\n  📈 Чтение за {self.CHART_DAYS} дней: {total} стр., ~{average} стр./день")

        if total == 0:
            print("  Отмечайте прогресс в библиотеке — здесь появится график.")
            return

        max_pages = max(item["pages"] for item in series) or 1
        print()
        for item in series:
            bar = horizontal_bar(item["pages"], max_pages, width=16)
            pages_label = f"{item['pages']:>3} стр."
            print(f"  {item['label']}  {bar}  {pages_label}")

    def _books_chart(self) -> None:
        if not self.books:
            print("\n  Добавьте книги, чтобы увидеть прогресс по каждой.")
            return

        print("\n  📚 Прогресс по книгам:")
        print()
        for book in self.books:
            label = StatisticsService.format_book_label(book)
            bar = horizontal_bar(book.progress, 100, width=18)
            print(f"  {label}\n      {bar}  {book.progress}%")
