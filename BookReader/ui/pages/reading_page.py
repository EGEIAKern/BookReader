import customtkinter as ctk

from services.reading_service import ReadingService
from ui.colors import COLORS
from ui.widgets import create_labeled_entry


class ReadingPage:

    def __init__(self, parent):
        self.parent = parent
        self.build()

    def build(self):
        ctk.CTkLabel(
            self.parent,
            text="📖 Прогресс чтения",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLORS["text_main"],
        ).pack(pady=20)

        form = ctk.CTkFrame(self.parent, fg_color=COLORS["bg_card"])
        form.pack(fill="x", padx=30, pady=10)

        self.total_var = ctk.StringVar()
        self.current_var = ctk.StringVar()

        fields = ctk.CTkFrame(form, fg_color="transparent")
        fields.pack(fill="x", padx=0, pady=(15, 15))

        create_labeled_entry(
            fields,
            label="Всего страниц в книге",
            textvariable=self.total_var,
            placeholder="Например: 450",
        )
        create_labeled_entry(
            fields,
            label="Уже прочитано страниц",
            textvariable=self.current_var,
            placeholder="Например: 120",
        )

        ctk.CTkButton(
            self.parent,
            text="Рассчитать",
            command=self.calculate,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
        ).pack(pady=20)

        self.result = ctk.CTkLabel(
            self.parent,
            text="",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["accent"],
        )
        self.result.pack()

        self.progress = ctk.CTkProgressBar(
            self.parent,
            progress_color=COLORS["accent"],
            fg_color=COLORS["bg_card"],
        )
        self.progress.pack(fill="x", padx=60, pady=20)
        self.progress.set(0)

    def calculate(self):
        try:
            percent = ReadingService.calculate_progress(
                int(self.total_var.get()),
                int(self.current_var.get()),
            )

            self.result.configure(
                text=f"{percent}% прочитано",
                text_color=COLORS["accent"],
            )
            self.progress.set(percent / 100)

        except ValueError:
            self.result.configure(
                text="Общее число страниц должно быть больше 0",
                text_color=COLORS["error"],
            )
        except TypeError:
            self.result.configure(
                text="Введите корректные числа",
                text_color=COLORS["error"],
            )
