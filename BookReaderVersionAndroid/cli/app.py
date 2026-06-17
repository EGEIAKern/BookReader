from storage.paths import get_data_dir
from storage.reading_log import load_reading_log, save_reading_log
from storage.storage import load_books, save_books

from cli.display import clear_screen, ensure_utf8_stdout, pause, print_header
from cli.library import LibraryScreen
from cli.statistics import StatisticsScreen
from cli.tools import ToolsScreen


class BookTrackerApp:

    def __init__(self):
        self.books = load_books()
        self.reading_log = load_reading_log()

    def run(self) -> None:
        ensure_utf8_stdout()

        while True:
            clear_screen()
            print_header("📚 Book Tracker (Termux)")
            print(f"\n  Книг в библиотеке: {len(self.books)}")
            print(f"  Данные: {get_data_dir()}")
            print(
                "\n  1. Библиотека\n"
                "  2. Статистика\n"
                "  3. Инструменты\n"
                "  0. Выход"
            )

            try:
                choice = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if choice in {"0", "q", "exit", "выход"}:
                if self._confirm_exit():
                    break
                continue
            if choice == "1":
                LibraryScreen(self.books, self.reading_log).run()
            elif choice == "2":
                StatisticsScreen(self.books, self.reading_log).run()
            elif choice == "3":
                ToolsScreen().run()
            else:
                pause("Неизвестная команда. Enter...")

    def _confirm_exit(self) -> bool:
        try:
            save_books(self.books)
            save_reading_log(self.reading_log)
        except OSError:
            pass
        return True
