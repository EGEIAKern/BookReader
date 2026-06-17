import customtkinter as ctk
from tkinter import messagebox
from typing import Optional

from models.book import Book, normalize_url
from models.work import WORK_STATUS_LABELS, WORK_STATUSES, Work
from ui.colors import COLORS


def _parse_int(value: str, field_name: str) -> int:
    text = value.strip()
    if not text:
        raise ValueError(f"Введите значение для поля «{field_name}»")
    try:
        return int(text)
    except ValueError as error:
        raise ValueError(f"«{field_name}» должно быть целым числом") from error


class _WorksEditorFrame(ctk.CTkFrame):

    def __init__(self, parent, book_total_pages: int = 0, works=None, on_change=None):
        super().__init__(parent, fg_color="transparent")
        self._book_total_pages = book_total_pages
        self._rows: list[dict] = []
        self._on_change = on_change

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(0, 6))

        ctk.CTkLabel(
            header,
            text="Произведения в книге",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_main"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Добавьте рассказы, стихи и другие части сборника. "
                 "Сумма страниц не должна превышать общее число страниц книги.",
            text_color=COLORS["text_muted"],
            wraplength=400,
            justify="left",
            font=ctk.CTkFont(size=12),
        ).pack(anchor="w", pady=(2, 0))

        self.rows_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.rows_frame.pack(fill="x")

        self.summary_label = ctk.CTkLabel(
            self,
            text="",
            text_color=COLORS["text_muted"],
            font=ctk.CTkFont(size=12),
        )
        self.summary_label.pack(anchor="w", padx=10, pady=(4, 6))

        ctk.CTkButton(
            self,
            text="➕ Добавить произведение",
            command=self.add_row,
            height=32,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["accent_hover"],
        ).pack(anchor="w", padx=10, pady=(0, 8))

        for work in works or []:
            self.add_row(work, notify=False)
        if works:
            self._update_summary()

    def set_book_total_pages(self, total_pages: int) -> None:
        self._book_total_pages = max(int(total_pages), 0)
        self._update_summary()

    def add_row(self, work: Optional[Work] = None, notify: bool = True) -> None:
        row_frame = ctk.CTkFrame(self.rows_frame, fg_color=COLORS["bg_card"], corner_radius=8)
        row_frame.pack(fill="x", padx=10, pady=4)

        title_var = ctk.StringVar(value=work.title if work else "")
        pages_var = ctk.StringVar(value=str(work.total_pages) if work else "")
        progress_var = ctk.StringVar(
            value=str(work.current_page) if work else "0"
        )
        status_var = ctk.StringVar(
            value=WORK_STATUS_LABELS.get(work.status if work else "planned", "Буду читать")
        )

        top = ctk.CTkFrame(row_frame, fg_color="transparent")
        top.pack(fill="x", padx=8, pady=(8, 4))

        ctk.CTkEntry(
            top,
            textvariable=title_var,
            placeholder_text="Название произведения",
            placeholder_text_color=COLORS["text_muted"],
            text_color=COLORS["text_main"],
            fg_color=COLORS["bg_main"],
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            top,
            text="✕",
            width=32,
            height=28,
            command=lambda: self.remove_row(row_data),
            fg_color=COLORS["error"],
            hover_color="#e06b88",
        ).pack(side="right")

        bottom = ctk.CTkFrame(row_frame, fg_color="transparent")
        bottom.pack(fill="x", padx=8, pady=(0, 8))

        ctk.CTkEntry(
            bottom,
            textvariable=pages_var,
            width=70,
            placeholder_text="Всего",
            placeholder_text_color=COLORS["text_muted"],
            text_color=COLORS["text_main"],
            fg_color=COLORS["bg_main"],
        ).pack(side="left", padx=(0, 6))

        ctk.CTkEntry(
            bottom,
            textvariable=progress_var,
            width=70,
            placeholder_text="Прочит.",
            placeholder_text_color=COLORS["text_muted"],
            text_color=COLORS["text_main"],
            fg_color=COLORS["bg_main"],
        ).pack(side="left", padx=(0, 8))

        ctk.CTkOptionMenu(
            bottom,
            variable=status_var,
            values=list(WORK_STATUS_LABELS.values()),
            fg_color=COLORS["bg_main"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_card"],
            text_color=COLORS["text_main"],
            width=160,
        ).pack(side="left")

        row_data = {
            "frame": row_frame,
            "title_var": title_var,
            "pages_var": pages_var,
            "progress_var": progress_var,
            "status_var": status_var,
        }
        pages_var.trace_add("write", lambda *_: self._notify_change())
        self._rows.append(row_data)
        if notify:
            self._notify_change()

    def remove_row(self, row_data: dict) -> None:
        if row_data in self._rows:
            self._rows.remove(row_data)
            row_data["frame"].destroy()
            self._notify_change()

    def _notify_change(self) -> None:
        self._update_summary()
        if self._on_change:
            self._on_change()

    def _update_summary(self) -> None:
        allocated = 0
        for row in self._rows:
            try:
                allocated += int(row["pages_var"].get().strip() or "0")
            except ValueError:
                continue

        if self._book_total_pages > 0:
            color = COLORS["error"] if allocated > self._book_total_pages else COLORS["text_muted"]
            self.summary_label.configure(
                text=f"Распределено: {allocated} / {self._book_total_pages} стр.",
                text_color=color,
            )
        else:
            self.summary_label.configure(
                text=f"Распределено: {allocated} стр.",
                text_color=COLORS["text_muted"],
            )

    def _label_to_status(self, label: str) -> str:
        for status, status_label in WORK_STATUS_LABELS.items():
            if status_label == label:
                return status
        return "planned"

    def get_works(self) -> list[Work]:
        works = []
        for row in self._rows:
            title = row["title_var"].get().strip()
            pages_text = row["pages_var"].get().strip()
            if not title and not pages_text:
                continue
            total_pages = _parse_int(pages_text or "0", "Страниц произведения")
            progress_text = row["progress_var"].get().strip()
            try:
                current_page = int(progress_text) if progress_text else 0
            except ValueError as error:
                raise ValueError(
                    f"«Прочитано» для «{title or 'произведения'}» должно быть целым числом"
                ) from error
            status = self._label_to_status(row["status_var"].get())
            work = Work(
                title=title,
                total_pages=total_pages,
                current_page=current_page,
                status=status,
            )
            works.append(work)
        return works

    def has_works(self) -> bool:
        return bool(self._rows)


class _BookFormDialog(ctk.CTkToplevel):

    def __init__(self, parent, title, submit_text, book=None, show_review=False):
        super().__init__(parent)

        self.result = None
        self._book = book
        self._show_review = show_review

        self.title(title)
        self.geometry("480x700")
        self.minsize(440, 620)
        self.configure(fg_color=COLORS["bg_main"])

        self.grab_set()
        self.focus()

        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(pady=(20, 10))

        form = ctk.CTkScrollableFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=10)

        self.title_var = ctk.StringVar(value=book.title if book else "")
        self.author_var = ctk.StringVar(value=book.author if book else "")
        self.pages_var = ctk.StringVar(
            value=str(book.total_pages) if book else ""
        )
        self.current_var = ctk.StringVar(
            value=str(book.current_page) if book else "0"
        )
        self.marketplace_var = ctk.StringVar(
            value=book.marketplace_url if book else ""
        )

        self.create_field(form, "Название", self.title_var)
        self.create_field(form, "Автор", self.author_var)
        self.create_field(form, "Всего страниц", self.pages_var)
        self.current_page_block = ctk.CTkFrame(form, fg_color="transparent")
        self.current_page_block.pack(fill="x")
        self.create_field(self.current_page_block, "Текущая страница", self.current_var)
        self.pages_var.trace_add("write", self._on_total_pages_changed)

        self.create_field(
            form,
            "Ссылка на маркетплейс (необязательно)",
            self.marketplace_var,
            placeholder="https://...",
        )
        self.description_box = self.create_text_field(
            form,
            "Описание (необязательно)",
            book.description if book else "",
        )

        self.works_editor = None
        self.works_editor = _WorksEditorFrame(
            form,
            book_total_pages=book.total_pages if book else 0,
            works=book.works if book else None,
            on_change=self._update_current_page_visibility,
        )
        self.works_editor.pack(fill="x", pady=(0, 8))

        self.review_box = None
        if show_review:
            self.review_box = self.create_text_field(
                form,
                "Мнение о книге (необязательно)",
                book.review if book else "",
            )

        self._update_current_page_visibility()

        ctk.CTkButton(
            self,
            text=submit_text,
            command=self.save,
            height=40,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
        ).pack(pady=16)

    def _on_total_pages_changed(self, *_args) -> None:
        if self.works_editor is None:
            return
        try:
            total_pages = int(self.pages_var.get().strip() or "0")
        except ValueError:
            total_pages = 0
        self.works_editor.set_book_total_pages(total_pages)

    def _update_current_page_visibility(self) -> None:
        if self.works_editor is None:
            return
        if self.works_editor.has_works():
            self.current_page_block.pack_forget()
        else:
            self.current_page_block.pack(fill="x")

    def create_field(self, parent, text, variable, placeholder=None):
        ctk.CTkLabel(
            parent,
            text=text,
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", padx=10)

        ctk.CTkEntry(
            parent,
            textvariable=variable,
            placeholder_text=placeholder or text,
            placeholder_text_color=COLORS["text_muted"],
            text_color=COLORS["text_main"],
            fg_color=COLORS["bg_card"],
        ).pack(fill="x", padx=10, pady=(0, 10))

    def create_text_field(self, parent, label, initial_text=""):
        ctk.CTkLabel(
            parent,
            text=label,
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", padx=10)

        box = ctk.CTkTextbox(
            parent,
            height=80,
            fg_color=COLORS["bg_card"],
            text_color=COLORS["text_main"],
        )
        box.pack(fill="x", padx=10, pady=(0, 10))
        if initial_text:
            box.insert("1.0", initial_text)
        return box

    def _get_textbox_value(self, box) -> str:
        return box.get("1.0", "end-1c").strip()

    def save(self):
        try:
            title = self.title_var.get().strip()
            author = self.author_var.get().strip()
            total_pages = _parse_int(self.pages_var.get(), "Всего страниц")
            description = self._get_textbox_value(self.description_box)
            review = (
                self._get_textbox_value(self.review_box)
                if self.review_box is not None
                else (self._book.review if self._book else "")
            )
            marketplace_url = normalize_url(self.marketplace_var.get())
            works = self.works_editor.get_works()

            if not title:
                raise ValueError("Введите название")

            if total_pages <= 0:
                raise ValueError("Количество страниц должно быть больше 0")

            if works:
                current_page = 0
            else:
                current_page = _parse_int(self.current_var.get(), "Текущая страница")

            book = Book(
                title=title,
                author=author,
                total_pages=total_pages,
                current_page=current_page,
                description=description,
                marketplace_url=marketplace_url,
                review=review,
                works=works,
            )
            book.validate_works()
            self.result = book
            self.destroy()

        except ValueError as error:
            messagebox.showerror("Ошибка", str(error))


class AddBookDialog(_BookFormDialog):

    def __init__(self, parent):
        super().__init__(parent, "Добавить книгу", "Сохранить")


class EditBookDialog(_BookFormDialog):

    def __init__(self, parent, book):
        super().__init__(
            parent,
            "Редактировать книгу",
            "Сохранить",
            book=book,
            show_review=True,
        )


class ManageWorksDialog(ctk.CTkToplevel):

    STATUS_COLORS = {
        "planned": COLORS["text_muted"],
        "reading": COLORS["accent"],
        "finished": COLORS["success"],
        "skipped": COLORS["error"],
    }

    def __init__(self, parent, book):
        super().__init__(parent)

        self.book = book
        self.changed = False

        self.title("Произведения")
        self.geometry("520x560")
        self.minsize(480, 420)
        self.configure(fg_color=COLORS["bg_main"])

        self.grab_set()
        self.focus()

        ctk.CTkLabel(
            self,
            text=book.title,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["accent"],
            wraplength=460,
        ).pack(pady=(16, 4))

        ctk.CTkLabel(
            self,
            text=f"Прогресс книги: {book.progress}% · "
                 f"{book.effective_current_page} / {book.progress_total_pages} стр.",
            text_color=COLORS["text_muted"],
        ).pack(pady=(0, 10))

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        self._render_works()

        ctk.CTkButton(
            self,
            text="Готово",
            command=self.destroy,
            height=36,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
        ).pack(pady=(0, 16))

    def _render_works(self) -> None:
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        if not self.book.works:
            ctk.CTkLabel(
                self.list_frame,
                text="Произведения не добавлены.\nИспользуйте «Изменить» для настройки.",
                text_color=COLORS["text_muted"],
                justify="center",
            ).pack(pady=20)
            return

        for index, work in enumerate(self.book.works):
            self._render_work_row(index, work)

    def _render_work_row(self, index: int, work: Work) -> None:
        card = ctk.CTkFrame(self.list_frame, fg_color=COLORS["bg_card"], corner_radius=8)
        card.pack(fill="x", pady=6)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 4))

        ctk.CTkLabel(
            header,
            text=work.title,
            anchor="w",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_main"],
        ).pack(side="left", anchor="w")

        status_color = self.STATUS_COLORS.get(work.status, COLORS["text_muted"])
        ctk.CTkLabel(
            header,
            text=WORK_STATUS_LABELS.get(work.status, work.status),
            text_color=status_color,
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="right")

        if work.counts_toward_progress:
            progress_text = f"{work.current_page} / {work.total_pages} стр. · {work.progress}%"
        else:
            progress_text = f"{work.total_pages} стр. · пропущено"

        ctk.CTkLabel(
            card,
            text=progress_text,
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", padx=10)

        if work.counts_toward_progress:
            progress = ctk.CTkProgressBar(
                card,
                progress_color=COLORS["accent"],
                fg_color=COLORS["bg_main"],
                height=8,
            )
            progress.pack(fill="x", padx=10, pady=6)
            progress.set(work.progress / 100)

        controls = ctk.CTkFrame(card, fg_color="transparent")
        controls.pack(fill="x", padx=8, pady=(0, 10))

        status_var = ctk.StringVar(value=WORK_STATUS_LABELS[work.status])

        def on_status_change(choice, work_index=index):
            new_status = next(
                (key for key, label in WORK_STATUS_LABELS.items() if label == choice),
                "planned",
            )
            self._apply_status(work_index, new_status)

        ctk.CTkOptionMenu(
            controls,
            variable=status_var,
            values=list(WORK_STATUS_LABELS.values()),
            command=on_status_change,
            fg_color=COLORS["bg_main"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_card"],
            text_color=COLORS["text_main"],
            width=150,
        ).pack(side="left", padx=2)

        if work.counts_toward_progress:
            if not work.is_finished:
                ctk.CTkButton(
                    controls,
                    text="➕ Стр.",
                    width=70,
                    command=lambda i=index: self._add_page(i),
                    fg_color=COLORS["bg_main"],
                    hover_color=COLORS["accent_hover"],
                ).pack(side="left", padx=2)

            ctk.CTkButton(
                controls,
                text="✏️ Стр.",
                width=70,
                command=lambda i=index: self._set_page(i),
                fg_color=COLORS["bg_main"],
                hover_color=COLORS["accent_hover"],
            ).pack(side="left", padx=2)

    def _apply_status(self, index: int, status: str) -> None:
        work = self.book.works[index]
        work.set_status(status)
        self.book.sync_from_works()
        self.changed = True
        self._render_works()

    def _add_page(self, index: int) -> None:
        work = self.book.works[index]
        if work.current_page < work.total_pages:
            if work.status != "reading" and work.current_page == 0:
                work.set_status("reading")
            work.current_page += 1
            if work.current_page >= work.total_pages:
                work.set_status("finished")
            self.book.sync_from_works()
            self.changed = True
            self._render_works()

    def _set_page(self, index: int) -> None:
        work = self.book.works[index]
        dialog = SetWorkPageDialog(self, work)
        self.wait_window(dialog)
        if dialog.result is not None:
            work.current_page = dialog.result
            if work.current_page >= work.total_pages and work.total_pages > 0:
                work.set_status("finished")
            elif work.current_page > 0:
                if work.status in ("planned", "finished"):
                    work.set_status("reading")
            elif work.status == "finished":
                work.set_status("planned")
            self.book.sync_from_works()
            self.changed = True
            self._render_works()


class SetWorkPageDialog(ctk.CTkToplevel):

    def __init__(self, parent, work: Work):
        super().__init__(parent)

        self.result = None
        self._work = work

        self.title("Прогресс произведения")
        self.geometry("360x220")
        self.configure(fg_color=COLORS["bg_main"])

        self.grab_set()
        self.focus()

        ctk.CTkLabel(
            self,
            text=work.title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["accent"],
            wraplength=320,
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            self,
            text=f"Текущая страница (из {work.total_pages})",
            text_color=COLORS["text_muted"],
        ).pack(pady=(0, 10))

        self.page_var = ctk.StringVar(value=str(work.current_page))

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
            self.result = min(page, self._work.total_pages)
            self.destroy()
        except ValueError as error:
            messagebox.showerror("Ошибка", str(error))


class BookReviewDialog(ctk.CTkToplevel):

    def __init__(self, parent, book):
        super().__init__(parent)

        self.result = None
        self._book = book

        self.title("Книга прочитана")
        self.geometry("440x340")
        self.configure(fg_color=COLORS["bg_main"])

        self.grab_set()
        self.focus()

        ctk.CTkLabel(
            self,
            text="🎉 Поздравляем!",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["success"],
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            self,
            text=f"Вы дочитали «{book.title}»",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS["accent"],
            wraplength=380,
        ).pack(pady=(0, 5))

        ctk.CTkLabel(
            self,
            text="Хотите оставить мнение о книге? Это необязательно.",
            text_color=COLORS["text_muted"],
            wraplength=380,
        ).pack(pady=(0, 10))

        self.review_box = ctk.CTkTextbox(
            self,
            height=120,
            fg_color=COLORS["bg_card"],
            text_color=COLORS["text_main"],
        )
        self.review_box.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        if book.review:
            self.review_box.insert("1.0", book.review)

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(pady=(0, 16))

        ctk.CTkButton(
            buttons,
            text="Сохранить мнение",
            command=self.save,
            width=150,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            buttons,
            text="Пропустить",
            command=self.skip,
            width=120,
            fg_color=COLORS["bg_card"],
        ).pack(side="left", padx=5)

    def save(self):
        self.result = self.review_box.get("1.0", "end-1c").strip()
        self.destroy()

    def skip(self):
        self.result = None
        self.destroy()


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
