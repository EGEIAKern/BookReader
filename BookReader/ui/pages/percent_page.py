import customtkinter as ctk

from services.percent_service import PercentService
from ui.colors import COLORS
from ui.widgets import create_labeled_entry


class PercentPage:

    def __init__(self, parent):
        self.parent = parent
        self.build()

    def build(self):
        ctk.CTkLabel(
            self.parent,
            text="📊 Страницы по проценту",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLORS["text_main"],
        ).pack(pady=20)

        form = ctk.CTkFrame(self.parent, fg_color=COLORS["bg_card"])
        form.pack(fill="x", padx=30, pady=10)

        self.total_var = ctk.StringVar()
        self.percent_var = ctk.StringVar()

        fields = ctk.CTkFrame(form, fg_color="transparent")
        fields.pack(fill="x", padx=0, pady=(15, 15))

        create_labeled_entry(
            fields,
            label="Всего страниц в книге",
            textvariable=self.total_var,
            placeholder="Например: 500",
        )
        create_labeled_entry(
            fields,
            label="Процент прочтения",
            textvariable=self.percent_var,
            placeholder="От 0 до 100",
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

    def calculate(self):
        try:
            pages = PercentService.calculate_pages(
                int(self.total_var.get()),
                float(self.percent_var.get()),
            )

            self.result.configure(
                text=f"Это {pages} страниц",
                text_color=COLORS["accent"],
            )

        except ValueError:
            self.result.configure(
                text="Страниц > 0, процент от 0 до 100",
                text_color=COLORS["error"],
            )
        except TypeError:
            self.result.configure(
                text="Введите корректные числа",
                text_color=COLORS["error"],
            )
