import customtkinter as ctk
from tkinter import messagebox

from storage.storage import load_books, save_books
from storage.reading_log import load_reading_log, save_reading_log
from services.reading_log_service import ReadingLogService

from ui.library_page import LibraryPage
from ui.statistics_page import StatisticsPage

from ui.pages.reading_page import ReadingPage
from ui.pages.goal_page import GoalPage
from ui.pages.percent_page import PercentPage
from ui.pages.calculator_page import CalculatorPage
from ui.sync_page import SyncPage

from ui.colors import COLORS


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class BookTrackerApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("📚 Book Tracker Pro")
        self.geometry("1300x850")
        self.minsize(900, 600)

        self.books = load_books()
        self.reading_log = load_reading_log()
        self.books_dirty = False
        self.reading_log_dirty = False
        self._stats_frame = None
        self._stats_page = None
        self._stats_dirty = True

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.active_button = None
        self.configure(fg_color=COLORS["bg_main"])
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.create_sidebar()
        self.create_main()

        self.show_library()

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self,
            width=260,
            corner_radius=0,
            fg_color=COLORS["bg_sidebar"],
        )
        self.sidebar.grid(row=0, column=0, sticky="ns")

        ctk.CTkLabel(
            self.sidebar,
            text="📚 Book Tracker",
            text_color=COLORS["accent"],
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(pady=30)

        self.btn_library = self.create_nav_button("📚 Библиотека", self.show_library)
        self.btn_stats = self.create_nav_button("📊 Статистика", self.show_statistics)
        self.btn_reading = self.create_nav_button("📖 Прогресс", self.show_reading)
        self.btn_goal = self.create_nav_button("🎯 План чтения", self.show_goal)
        self.btn_percent = self.create_nav_button("📊 Страницы по %", self.show_percent)
        self.btn_calc = self.create_nav_button("🧮 Калькулятор", self.show_calculator)
        self.btn_sync = self.create_nav_button("☁️ Облако", self.show_sync)

        self.books_count_label = ctk.CTkLabel(
            self.sidebar,
            text=f"Книг: {len(self.books)}",
            text_color=COLORS["text_muted"],
            font=ctk.CTkFont(size=12),
        )
        self.books_count_label.pack(side="bottom", pady=20)

    def create_nav_button(self, text, command):
        btn = ctk.CTkButton(
            self.sidebar,
            text=text,
            height=45,
            anchor="w",
            fg_color="transparent",
            hover_color=COLORS["bg_card"],
            text_color=COLORS["text_main"],
            command=command,
        )
        btn.pack(fill="x", padx=15, pady=5)
        return btn

    def create_main(self):
        self.main = ctk.CTkFrame(self, fg_color="transparent")
        self.main.grid(row=0, column=1, sticky="nsew")

    def clear_main(self, keep_stats=False):
        for widget in self.main.winfo_children():
            if keep_stats and widget is self._stats_frame:
                widget.pack_forget()
                continue
            widget.destroy()

    def invalidate_stats(self):
        self._stats_dirty = True

    def activate(self, button):
        if self.active_button:
            self.active_button.configure(fg_color="transparent")

        self.active_button = button
        button.configure(fg_color=COLORS["accent"])

    def update_sidebar_counter(self):
        self.books_count_label.configure(text=f"Книг: {len(self.books)}")
        self.invalidate_stats()

    def persist_books(self, show_error: bool = True) -> bool:
        self.books_dirty = True
        try:
            save_books(self.books)
            self.books_dirty = False
            return True
        except OSError as error:
            if show_error:
                messagebox.showerror(
                    "Ошибка сохранения",
                    f"Не удалось сохранить библиотеку:\n{error}",
                )
            return False

    def record_reading(self, pages: int) -> None:
        ReadingLogService.record_pages(self.reading_log, pages)
        self.reading_log_dirty = True
        self.invalidate_stats()
        try:
            save_reading_log(self.reading_log)
            self.reading_log_dirty = False
        except OSError:
            pass

    def persist_reading_log(self, show_error: bool = True) -> bool:
        self.reading_log_dirty = True
        try:
            save_reading_log(self.reading_log)
            self.reading_log_dirty = False
            return True
        except OSError as error:
            if show_error:
                messagebox.showerror(
                    "Ошибка сохранения",
                    f"Не удалось сохранить журнал чтения:\n{error}",
                )
            return False

    def on_close(self):
        if self.books_dirty or self.reading_log_dirty:
            answer = messagebox.askyesnocancel(
                "Несохранённые изменения",
                "Есть несохранённые изменения.\n"
                "Сохранить перед выходом?",
            )
            if answer is None:
                return
            if answer:
                if self.books_dirty and not self.persist_books():
                    return
                if self.reading_log_dirty and not self.persist_reading_log():
                    return
        self.destroy()

    def show_library(self):
        self.activate(self.btn_library)
        self.clear_main(keep_stats=True)
        LibraryPage(
            self.main,
            self.books,
            on_books_changed=self.update_sidebar_counter,
            on_persist=self.persist_books,
            on_record_reading=self.record_reading,
        )

    def show_statistics(self):
        self.activate(self.btn_stats)
        self.clear_main(keep_stats=True)

        if self._stats_frame is None:
            self._stats_frame = ctk.CTkFrame(self.main, fg_color="transparent")
            self._stats_page = StatisticsPage(
                self._stats_frame,
                self.books,
                self.reading_log,
            )
            self._stats_dirty = False
        elif self._stats_dirty:
            self._stats_page.refresh(self.books, self.reading_log)
            self._stats_dirty = False

        self._stats_frame.pack(fill="both", expand=True)

    def show_reading(self):
        self.activate(self.btn_reading)
        self.clear_main(keep_stats=True)
        ReadingPage(self.main)

    def show_goal(self):
        self.activate(self.btn_goal)
        self.clear_main(keep_stats=True)
        GoalPage(self.main)

    def show_percent(self):
        self.activate(self.btn_percent)
        self.clear_main(keep_stats=True)
        PercentPage(self.main)

    def show_calculator(self):
        self.activate(self.btn_calc)
        self.clear_main(keep_stats=True)
        CalculatorPage(self.main)

    def show_sync(self):
        self.activate(self.btn_sync)
        self.clear_main(keep_stats=True)
        SyncPage(
            self.main,
            self.books,
            self.reading_log,
            on_sync_complete=self.update_sidebar_counter,
            on_persist_books=self.persist_books,
            on_persist_reading_log=self.persist_reading_log,
        ).pack(fill="both", expand=True)


if __name__ == "__main__":
    app = BookTrackerApp()
    app.mainloop()
