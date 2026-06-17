from pathlib import Path

from models.book import Book
from services.export_service import export_books_to_csv, export_books_to_excel
from services.reading_log_service import ReadingLogService
from storage.storage import save_books

from cli.display import (
    ask_float,
    ask_int,
    ask_text,
    ask_yes_no,
    clear_screen,
    horizontal_bar,
    pause,
    print_error,
    print_header,
    print_success,
    progress_bar,
)


class LibraryScreen:

    def __init__(self, books: list[Book], reading_log: dict[str, int]):
        self.books = books
        self.reading_log = reading_log

    def run(self) -> None:
        while True:
            clear_screen()
            print_header(f"📚 Библиотека ({len(self.books)} книг)")
            self._list_books()

            choice = input(
                "\n[a] добавить  [n] номер книги  [s] поиск  [e] экспорт  [0] назад\n> "
            ).strip().lower()

            if choice in {"0", "q", "назад"}:
                return
            if choice in {"a", "д", "add"}:
                self._add_book()
                continue
            if choice in {"s", "п", "search"}:
                self._search()
                continue
            if choice in {"e", "э", "export"}:
                self._export()
                continue
            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(self.books):
                    self._book_menu(index)
                else:
                    print_error("Неверный номер")
                    pause()
                continue

            print_error("Неизвестная команда")
            pause()

    def _list_books(self, items: list[tuple[int, Book]] | None = None) -> None:
        rows = items if items is not None else list(enumerate(self.books))

        if not rows:
            print("\n  Список пуст. Добавьте первую книгу.")
            return

        print()
        for display_index, (book_index, book) in enumerate(rows, start=1):
            author = book.author or "автор не указан"
            status = "✓" if book.progress >= 100 else " "
            print(
                f"  {display_index:>2}. [{status}] {book.title}\n"
                f"      {author} · {book.current_page}/{book.total_pages} стр. "
                f"({book.progress}%)\n"
                f"      {progress_bar(book.progress)}"
            )

    def _search(self) -> None:
        query = ask_text("\nПоиск (название или автор)")
        if query is None:
            return
        query = query.lower()
        found = [
            (index, book)
            for index, book in enumerate(self.books)
            if query in book.title.lower() or query in book.author.lower()
        ]
        clear_screen()
        print_header("🔍 Результаты поиска")
        self._list_books(found)
        pause()

    def _add_book(self) -> None:
        print_header("➕ Новая книга")
        title = ask_text("Название", required=True)
        if title is None:
            pause()
            return
        author = ask_text("Автор") or ""
        total = ask_int("Всего страниц", min_value=1)
        if total is None:
            pause()
            return
        current = ask_int("Уже прочитано", min_value=0, max_value=total) or 0

        book = Book(title, author, total, current)
        if current > 0:
            ReadingLogService.record_pages(self.reading_log, current)
        self.books.append(book)
        self._save()
        print_success(f"«{book.title}» добавлена")
        pause()

    def _book_menu(self, index: int) -> None:
        book = self.books[index]
        while True:
            clear_screen()
            print_header(f"📖 {book.title}")
            author = book.author or "автор не указан"
            print(f"\n  Автор: {author}")
            print(f"  Прогресс: {book.current_page}/{book.total_pages} ({book.progress}%)")
            print(f"  {progress_bar(book.progress)}")

            choice = input(
                "\n[+] +1 стр.  [p] прогресс  [e] изменить  [d] удалить  [0] назад\n> "
            ).strip().lower()

            if choice in {"0", "q"}:
                return
            if choice in {"+", "п", "plus"}:
                self._add_page(index)
            elif choice in {"p", "пр"}:
                self._set_page(index)
            elif choice in {"e", "и"}:
                self._edit_book(index)
            elif choice in {"d", "у"}:
                self._delete_book(index)
                return
            else:
                print_error("Неизвестная команда")
                pause()

    def _add_page(self, index: int) -> None:
        book = self.books[index]
        if book.current_page >= book.total_pages:
            print_error("Книга уже прочитана")
            pause()
            return
        old_page = book.current_page
        book.current_page += 1
        ReadingLogService.record_pages(self.reading_log, book.current_page - old_page)
        self._save()
        print_success(f"Страница {book.current_page}/{book.total_pages}")
        pause()

    def _set_page(self, index: int) -> None:
        book = self.books[index]
        page = ask_int(
            f"Текущая страница (0–{book.total_pages})",
            min_value=0,
            max_value=book.total_pages,
        )
        if page is None:
            pause()
            return
        old_page = book.current_page
        book.current_page = page
        delta = book.current_page - old_page
        if delta > 0:
            ReadingLogService.record_pages(self.reading_log, delta)
        self._save()
        print_success(f"Прогресс: {book.progress}%")
        pause()

    def _edit_book(self, index: int) -> None:
        book = self.books[index]
        print_header("✏️ Изменить книгу")
        title = ask_text("Название", required=False) or book.title
        author = ask_text("Автор", required=False)
        if author is None:
            author = book.author
        total = ask_int("Всего страниц", min_value=1)
        if total is None:
            pause()
            return
        current = ask_int(
            "Текущая страница",
            min_value=0,
            max_value=total,
        )
        if current is None:
            pause()
            return

        old_page = book.current_page
        updated = Book(title, author, total, current)
        delta = updated.current_page - old_page
        if delta > 0:
            ReadingLogService.record_pages(self.reading_log, delta)
        self.books[index] = updated
        self._save()
        print_success("Книга обновлена")
        pause()

    def _delete_book(self, index: int) -> None:
        book = self.books[index]
        if not ask_yes_no(f"Удалить «{book.title}»?"):
            return
        self.books.pop(index)
        self._save()
        print_success("Книга удалена")
        pause()

    def _export(self) -> None:
        if not self.books:
            print_error("Нет книг для экспорта")
            pause()
            return

        print_header("📥 Экспорт")
        print("  1. CSV (без зависимостей)")
        print("  2. Excel (нужен openpyxl)")
        print("  0. Назад")
        choice = ask_int("Формат", min_value=0, max_value=2)
        if not choice:
            return

        default_name = "book_tracker_library.csv" if choice == 1 else "book_tracker_library.xlsx"
        path_str = ask_text(f"Путь к файлу [{default_name}]") or default_name
        path = Path(path_str).expanduser()

        try:
            if choice == 1:
                saved = export_books_to_csv(self.books, path)
            else:
                saved = export_books_to_excel(self.books, path)
        except (OSError, ImportError) as error:
            print_error(str(error))
            pause()
            return

        print_success(f"Сохранено: {saved}")
        pause()

    def _save(self) -> None:
        save_books(self.books)
        from storage.reading_log import save_reading_log

        save_reading_log(self.reading_log)
