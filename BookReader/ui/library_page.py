import customtkinter as ctk
from tkinter import filedialog, messagebox

from models.work import WORK_STATUS_LABELS
from services.export_service import ExportService
from ui.colors import COLORS
from ui.dialogs import (
    AddBookDialog,
    BookReviewDialog,
    EditBookDialog,
    ManageWorksDialog,
    SetPageDialog,
)
from ui.widgets import create_labeled_entry, create_link_button


WORK_STATUS_COLORS = {
    "planned": COLORS["text_muted"],
    "reading": COLORS["accent"],
    "finished": COLORS["success"],
    "skipped": COLORS["error"],
}


class LibraryPage:

    def __init__(
        self,
        parent,
        books,
        on_books_changed=None,
        on_persist=None,
        on_record_reading=None,
    ):
        self.parent = parent
        self.books = books
        self.on_books_changed = on_books_changed
        self.on_persist = on_persist
        self.on_record_reading = on_record_reading
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.render_books())
        self.build()

    def build(self):
        header = ctk.CTkFrame(self.parent, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            header,
            text="📚 Библиотека книг",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLORS["text_main"],
        ).pack(side="left")

        self.count_label = ctk.CTkLabel(
            header,
            text=f"{len(self.books)} книг",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_muted"],
        )
        self.count_label.pack(side="right", padx=10)

        toolbar = ctk.CTkFrame(self.parent, fg_color=COLORS["bg_card"])
        toolbar.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(
            toolbar,
            text="➕ Добавить книгу",
            command=self.add_book,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
        ).pack(side="left", padx=10, pady=10)

        ctk.CTkButton(
            toolbar,
            text="📥 Экспорт в Excel",
            command=self.export_to_excel,
            fg_color=COLORS["bg_main"],
            hover_color=COLORS["accent_hover"],
        ).pack(side="left", padx=4, pady=10)

        search_block = ctk.CTkFrame(toolbar, fg_color="transparent")
        search_block.pack(side="right", padx=10, pady=5)

        create_labeled_entry(
            search_block,
            label="Поиск",
            textvariable=self.search_var,
            placeholder="Название или автор",
        )

        self.list_frame = ctk.CTkScrollableFrame(
            self.parent,
            fg_color="transparent",
        )
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.render_books()

    def filtered_books(self):
        query = self.search_var.get().strip().lower()

        if not query:
            return list(enumerate(self.books))

        return [
            (index, book)
            for index, book in enumerate(self.books)
            if query in book.title.lower() or query in book.author.lower()
        ]

    def render_books(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        items = self.filtered_books()

        if not self.books:
            ctk.CTkLabel(
                self.list_frame,
                text="Список книг пуст\nНажмите «Добавить книгу», чтобы начать",
                text_color=COLORS["text_muted"],
                justify="center",
            ).pack(pady=40)
            return

        if not items:
            ctk.CTkLabel(
                self.list_frame,
                text="Ничего не найдено",
                text_color=COLORS["text_muted"],
            ).pack(pady=40)
            return

        for index, book in items:
            self.render_book_card(index, book)

    def render_works_summary(self, parent, book):
        works_frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_main"], corner_radius=8)
        works_frame.pack(fill="x", pady=(8, 0))

        header = ctk.CTkFrame(works_frame, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(8, 4))

        finished = sum(1 for work in book.active_works if work.is_finished)
        total_active = len(book.active_works)

        ctk.CTkLabel(
            header,
            text=f"📖 Произведения: {finished}/{total_active} прочитано",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(side="left")

        for work in book.works:
            row = ctk.CTkFrame(works_frame, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=2)

            status_color = WORK_STATUS_COLORS.get(work.status, COLORS["text_muted"])
            status_label = WORK_STATUS_LABELS.get(work.status, work.status)

            if work.counts_toward_progress:
                pages_text = f"{work.current_page}/{work.total_pages} стр."
            else:
                pages_text = f"{work.total_pages} стр."

            ctk.CTkLabel(
                row,
                text=f"• {work.title}",
                anchor="w",
                text_color=COLORS["text_main"] if work.counts_toward_progress else COLORS["text_muted"],
                font=ctk.CTkFont(size=12),
            ).pack(side="left")

            ctk.CTkLabel(
                row,
                text=f"{pages_text} · {status_label}",
                text_color=status_color,
                font=ctk.CTkFont(size=11),
            ).pack(side="right")

        ctk.CTkLabel(works_frame, text="").pack(pady=2)

    def render_book_card(self, index, book):
        card = ctk.CTkFrame(self.list_frame, fg_color=COLORS["bg_card"])
        card.pack(fill="x", padx=10, pady=8)

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(fill="x", padx=15, pady=(12, 5))

        ctk.CTkLabel(
            info,
            text=book.title,
            anchor="w",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_main"],
        ).pack(anchor="w")

        author_text = book.author or "Автор не указан"
        ctk.CTkLabel(
            info,
            text=author_text,
            anchor="w",
            text_color=COLORS["text_muted"],
        ).pack(anchor="w")

        if book.description:
            ctk.CTkLabel(
                info,
                text=book.description,
                anchor="w",
                justify="left",
                wraplength=520,
                text_color=COLORS["text_muted"],
                font=ctk.CTkFont(size=13),
            ).pack(anchor="w", pady=(4, 0))

        if book.marketplace_url:
            create_link_button(info, book.marketplace_url)

        if book.has_works:
            self.render_works_summary(info, book)

        if book.review:
            review_frame = ctk.CTkFrame(info, fg_color=COLORS["bg_main"], corner_radius=8)
            review_frame.pack(fill="x", pady=(8, 0))

            ctk.CTkLabel(
                review_frame,
                text="💬 Моё мнение",
                anchor="w",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=COLORS["success"],
            ).pack(anchor="w", padx=10, pady=(8, 2))

            ctk.CTkLabel(
                review_frame,
                text=book.review,
                anchor="w",
                justify="left",
                wraplength=500,
                text_color=COLORS["text_main"],
                font=ctk.CTkFont(size=13),
            ).pack(anchor="w", padx=10, pady=(0, 8))

        if book.has_works:
            pages_text = (
                f"{book.effective_current_page} / {book.progress_total_pages} стр."
            )
            if (
                book.total_pages > 0
                and book.allocated_pages != book.total_pages
            ):
                pages_text += f" · произведения: {book.allocated_pages} стр."
        else:
            pages_text = f"{book.current_page} / {book.total_pages} страниц"

        status_color = COLORS["success"] if book.is_finished else COLORS["text_muted"]
        ctk.CTkLabel(
            card,
            text=pages_text,
            text_color=status_color,
        ).pack(anchor="w", padx=15)

        progress = ctk.CTkProgressBar(
            card,
            progress_color=COLORS["accent"],
            fg_color=COLORS["bg_main"],
        )
        progress.pack(fill="x", padx=15, pady=8)
        progress.set(book.progress / 100)

        ctk.CTkLabel(
            card,
            text=f"{book.progress}%",
            text_color=COLORS["accent"],
        ).pack(anchor="w", padx=15, pady=(0, 5))

        buttons = ctk.CTkFrame(card, fg_color="transparent")
        buttons.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkButton(
            buttons,
            text="➕ Страница",
            width=110,
            command=lambda i=index: self.add_page(i),
            fg_color=COLORS["bg_main"],
            hover_color=COLORS["accent_hover"],
        ).pack(side="left", padx=4)

        progress_command = (
            (lambda i=index: self.manage_works(i))
            if book.has_works
            else (lambda i=index: self.set_page(i))
        )
        progress_label = "📖 Произведения" if book.has_works else "✏️ Прогресс"

        ctk.CTkButton(
            buttons,
            text=progress_label,
            width=110,
            command=progress_command,
            fg_color=COLORS["bg_main"],
            hover_color=COLORS["accent_hover"],
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            buttons,
            text="📝 Изменить",
            width=110,
            command=lambda i=index: self.edit_book(i),
            fg_color=COLORS["bg_main"],
            hover_color=COLORS["accent_hover"],
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            buttons,
            text="🗑 Удалить",
            width=110,
            command=lambda i=index: self.delete_book(i),
            fg_color=COLORS["error"],
            hover_color="#e06b88",
        ).pack(side="left", padx=4)

    def export_to_excel(self):
        if not self.books:
            messagebox.showinfo(
                "Экспорт",
                "Нет данных для экспорта. Добавьте книги в библиотеку.",
            )
            return

        file_path = filedialog.asksaveasfilename(
            parent=self.parent.winfo_toplevel(),
            title="Сохранить Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx"), ("Все файлы", "*.*")],
            initialfile="book_tracker_library.xlsx",
        )

        if not file_path:
            return

        try:
            saved_path = ExportService.export_books_to_excel(self.books, file_path)
        except OSError as error:
            messagebox.showerror("Ошибка экспорта", f"Не удалось сохранить файл:\n{error}")
            return

        messagebox.showinfo(
            "Экспорт",
            f"Данные сохранены:\n{saved_path}",
        )

    def _save(self) -> bool:
        if self.on_persist:
            return self.on_persist()
        from storage.storage import save_books

        save_books(self.books)
        return True

    def _record_reading(self, pages: int) -> None:
        if pages > 0 and self.on_record_reading:
            self.on_record_reading(pages)

    def _prompt_review_if_completed(self, index, was_finished: bool) -> None:
        book = self.books[index]
        if book.is_finished and not was_finished and not book.review:
            dialog = BookReviewDialog(self.parent.winfo_toplevel(), book)
            self.parent.wait_window(dialog)
            if dialog.result:
                book.review = dialog.result
                self._save()

    def manage_works(self, index):
        book = self.books[index]
        was_finished = book.is_finished
        old_page = book.effective_current_page

        dialog = ManageWorksDialog(self.parent.winfo_toplevel(), book)
        self.parent.wait_window(dialog)

        if dialog.changed:
            pages_delta = book.effective_current_page - old_page
            self._record_reading(pages_delta)
            self._save()
            self.refresh()
            self._prompt_review_if_completed(index, was_finished)
            self.refresh()

    def add_book(self):
        dialog = AddBookDialog(self.parent.winfo_toplevel())
        self.parent.wait_window(dialog)

        if dialog.result:
            book = dialog.result
            if book.current_page > 0:
                self._record_reading(book.current_page)
            self.books.append(book)
            self._save()
            self.refresh()
            if book.is_finished and not book.review:
                self._prompt_review_if_completed(len(self.books) - 1, was_finished=False)
                self.refresh()

    def edit_book(self, index):
        dialog = EditBookDialog(
            self.parent.winfo_toplevel(),
            self.books[index],
        )
        self.parent.wait_window(dialog)

        if dialog.result:
            was_finished = self.books[index].is_finished
            old_page = self.books[index].effective_current_page
            updated = dialog.result
            self._record_reading(updated.effective_current_page - old_page)
            self.books[index] = updated
            self._save()
            self.refresh()
            self._prompt_review_if_completed(index, was_finished)
            self.refresh()

    def set_page(self, index):
        book = self.books[index]
        was_finished = book.is_finished
        dialog = SetPageDialog(self.parent.winfo_toplevel(), book)
        self.parent.wait_window(dialog)

        if dialog.result is not None:
            old_page = book.current_page
            book.current_page = dialog.result
            self._record_reading(book.current_page - old_page)
            self._save()
            self.refresh()
            self._prompt_review_if_completed(index, was_finished)
            self.refresh()

    def add_page(self, index):
        book = self.books[index]
        was_finished = book.is_finished

        if book.has_works:
            added = book.add_work_page(1)
            if added > 0:
                self._record_reading(added)
                self._save()
                self.refresh()
                self._prompt_review_if_completed(index, was_finished)
                self.refresh()
            return

        if book.current_page < book.total_pages:
            book.current_page += 1
            self._record_reading(1)
            self._save()
            self.refresh()
            self._prompt_review_if_completed(index, was_finished)
            self.refresh()

    def delete_book(self, index):
        book = self.books[index]

        if not messagebox.askyesno(
            "Удалить книгу",
            f"Удалить «{book.title}» из библиотеки?",
        ):
            return

        self.books.pop(index)
        self._save()
        self.refresh()

    def refresh(self):
        self.count_label.configure(text=f"{len(self.books)} книг")
        self.render_books()
        if self.on_books_changed:
            self.on_books_changed()
