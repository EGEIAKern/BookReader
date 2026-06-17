import customtkinter as ctk

from services.calculator_service import CalculatorService
from ui.colors import COLORS


class CalculatorPage:

    def __init__(self, parent):
        self.parent = parent
        self.build()

    def build(self):
        ctk.CTkLabel(
            self.parent,
            text="🧮 Калькулятор",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLORS["text_main"],
        ).pack(pady=20)

        self.v1 = ctk.StringVar()
        self.v2 = ctk.StringVar()
        self.op = ctk.StringVar(value="+")

        frame = ctk.CTkFrame(self.parent, fg_color=COLORS["bg_card"])
        frame.pack(pady=20, padx=30, fill="x")
        frame.grid_columnconfigure((0, 2), weight=1)

        self._labeled_entry(frame, "Первое число", self.v1, 0, 0)
        self._labeled_entry(frame, "Второе число", self.v2, 0, 2)

        op_block = ctk.CTkFrame(frame, fg_color="transparent")
        op_block.grid(row=0, column=1, padx=10, pady=15, sticky="n")

        ctk.CTkLabel(
            op_block,
            text="Операция",
            text_color=COLORS["text_muted"],
            font=ctk.CTkFont(size=13),
        ).pack(pady=(0, 4))

        ctk.CTkOptionMenu(
            op_block,
            variable=self.op,
            values=["+", "-", "*", "/"],
            width=80,
            fg_color=COLORS["bg_main"],
        ).pack()

        ctk.CTkButton(
            self.parent,
            text="Вычислить",
            command=self.calculate,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
        ).pack(pady=15)

        self.result = ctk.CTkLabel(
            self.parent,
            text="Результат: —",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["accent"],
        )
        self.result.pack()

    def _labeled_entry(self, parent, label, variable, row, column):
        block = ctk.CTkFrame(parent, fg_color="transparent")
        block.grid(row=row, column=column, padx=10, pady=15, sticky="ew")

        ctk.CTkLabel(
            block,
            text=label,
            text_color=COLORS["text_muted"],
            font=ctk.CTkFont(size=13),
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkEntry(
            block,
            textvariable=variable,
            placeholder_text="0",
            placeholder_text_color=COLORS["text_muted"],
            text_color=COLORS["text_main"],
            fg_color=COLORS["bg_main"],
        ).pack(fill="x")

    def calculate(self):
        try:
            result = CalculatorService.calculate(
                float(self.v1.get()),
                float(self.v2.get()),
                self.op.get(),
            )

            self.result.configure(
                text=f"= {result:g}",
                text_color=COLORS["accent"],
            )

        except ZeroDivisionError:
            self.result.configure(
                text="Деление на ноль невозможно",
                text_color=COLORS["error"],
            )
        except (TypeError, ValueError):
            self.result.configure(
                text="Введите корректные числа",
                text_color=COLORS["error"],
            )
