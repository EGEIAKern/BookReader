import customtkinter as ctk
from tkinter import filedialog, messagebox

from services.export_service import ExportService
from ui.colors import COLORS
from ui.dialogs import AddBookDialog, EditBookDialog, SetPageDialog
from ui.widgets import create_labeled_entry


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

        status_color = COLORS["success"] if book.progress >= 100 else COLORS["text_muted"]
        ctk.CTkLabel(
            card,
            text=f"{book.current_page} / {book.total_pages} страниц",
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

        ctk.CTkButton(
            buttons,
            text="✏️ Прогресс",
            width=110,
            command=lambda i=index: self.set_page(i),
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

    def edit_book(self, index):
        dialog = EditBookDialog(
            self.parent.winfo_toplevel(),
            self.books[index],
        )
        self.parent.wait_window(dialog)

        if dialog.result:
            old_page = self.books[index].current_page
            updated = dialog.result
            self._record_reading(updated.current_page - old_page)
            self.books[index] = updated
            self._save()
            self.refresh()

    def set_page(self, index):
        book = self.books[index]
        dialog = SetPageDialog(self.parent.winfo_toplevel(), book)
        self.parent.wait_window(dialog)

        if dialog.result is not None:
            old_page = book.current_page
            book.current_page = dialog.result
            self._record_reading(book.current_page - old_page)
            self._save()
            self.refresh()

    def add_page(self, index):
        book = self.books[index]

        if book.current_page < book.total_pages:
            book.current_page += 1
            self._record_reading(1)
            self._save()
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
