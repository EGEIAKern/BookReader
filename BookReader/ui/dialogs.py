import customtkinter as ctk
from tkinter import messagebox

from models.book import Book
from ui.colors import COLORS


def _parse_int(value: str, field_name: str) -> int:
    text = value.strip()
    if not text:
        raise ValueError(f"Введите значение для поля «{field_name}»")
    try:
        return int(text)
    except ValueError as error:
        raise ValueError(f"«{field_name}» должно быть целым числом") from error


class _BookFormDialog(ctk.CTkToplevel):

    def __init__(self, parent, title, submit_text, book=None):
        super().__init__(parent)

        self.result = None
        self._book = book

        self.title(title)
        self.geometry("420x420")
        self.configure(fg_color=COLORS["bg_main"])

        self.grab_set()
        self.focus()

        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(pady=20)

        self.title_var = ctk.StringVar(value=book.title if book else "")
        self.author_var = ctk.StringVar(value=book.author if book else "")
        self.pages_var = ctk.StringVar(
            value=str(book.total_pages) if book else ""
        )
        self.current_var = ctk.StringVar(
            value=str(book.current_page) if book else "0"
        )

        self.create_field("Название", self.title_var)
        self.create_field("Автор", self.author_var)
        self.create_field("Всего страниц", self.pages_var)
        self.create_field("Текущая страница", self.current_var)

        ctk.CTkButton(
            self,
            text=submit_text,
            command=self.save,
            height=40,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
        ).pack(pady=20)

    def create_field(self, text, variable):
        ctk.CTkLabel(
            self,
            text=text,
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", padx=20)

        ctk.CTkEntry(
            self,
            textvariable=variable,
            placeholder_text=text,
            placeholder_text_color=COLORS["text_muted"],
            text_color=COLORS["text_main"],
            fg_color=COLORS["bg_card"],
        ).pack(fill="x", padx=20, pady=(0, 10))

    def save(self):
        try:
            title = self.title_var.get().strip()
            author = self.author_var.get().strip()
            total_pages = _parse_int(self.pages_var.get(), "Всего страниц")
            current_page = _parse_int(self.current_var.get(), "Текущая страница")

            if not title:
                raise ValueError("Введите название")

            if total_pages <= 0:
                raise ValueError("Количество страниц должно быть больше 0")

            self.result = Book(
                title=title,
                author=author,
                total_pages=total_pages,
                current_page=current_page,
            )
            self.destroy()

        except ValueError as error:
            messagebox.showerror("Ошибка", str(error))


class AddBookDialog(_BookFormDialog):

    def __init__(self, parent):
        super().__init__(parent, "Добавить книгу", "Сохранить")


class EditBookDialog(_BookFormDialog):

    def __init__(self, parent, book):
        super().__init__(parent, "Редактировать книгу", "Сохранить", book=book)


class SetPageDialog(ctk.CTkToplevel):

    def __init__(self, parent, book):
        super().__init__(parent)

        self.result = None
        self._book = book

        self.title("Обновить прогресс")
        self.geometry("360x220")
        self.configure(fg_color=COLORS["bg_main"])

        self.grab_set()
        self.focus()

        ctk.CTkLabel(
            self,
            text=f"{book.title}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            self,
            text=f"Текущая страница (из {book.total_pages})",
            text_color=COLORS["text_muted"],
        ).pack(pady=(0, 10))

        self.page_var = ctk.StringVar(value=str(book.current_page))

        ctk.CTkEntry(
            self,
            textvariable=self.page_var,
            fg_color=COLORS["bg_card"],
        ).pack(fill="x", padx=20)

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(pady=20)

        ctk.CTkButton(
            buttons,
            text="Сохранить",
            command=self.save,
            width=120,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            buttons,
            text="Отмена",
            command=self.destroy,
            width=120,
            fg_color=COLORS["bg_card"],
        ).pack(side="left", padx=5)

    def save(self):
        try:
            page = _parse_int(self.page_var.get(), "Текущая страница")
            self.result = min(page, self._book.total_pages)
            self.destroy()

        except ValueError as error:
            messagebox.showerror("Ошибка", str(error))
