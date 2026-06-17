import customtkinter as ctk

from services.goal_service import GoalService
from ui.colors import COLORS
from ui.widgets import create_labeled_entry


class GoalPage:

    def __init__(self, parent):
        self.parent = parent
        self.build()

    def build(self):
        ctk.CTkLabel(
            self.parent,
            text="🎯 План чтения",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLORS["text_main"],
        ).pack(pady=20)

        form = ctk.CTkFrame(self.parent, fg_color=COLORS["bg_card"])
        form.pack(fill="x", padx=30, pady=10)

        self.pages_var = ctk.StringVar()
        self.days_var = ctk.StringVar()

        fields = ctk.CTkFrame(form, fg_color="transparent")
        fields.pack(fill="x", padx=0, pady=(15, 15))

        create_labeled_entry(
            fields,
            label="Осталось страниц",
            textvariable=self.pages_var,
            placeholder="Например: 320",
        )
        create_labeled_entry(
            fields,
            label="Дней до дедлайна",
            textvariable=self.days_var,
            placeholder="Например: 14",
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
            value = GoalService.pages_per_day(
                int(self.pages_var.get()),
                int(self.days_var.get()),
            )

            self.result.configure(
                text=f"Нужно читать {value} стр./день",
                text_color=COLORS["accent"],
            )

        except ValueError:
            self.result.configure(
                text="Количество дней должно быть больше 0",
                text_color=COLORS["error"],
            )
        except TypeError:
            self.result.configure(
                text="Введите корректные числа",
                text_color=COLORS["error"],
            )
