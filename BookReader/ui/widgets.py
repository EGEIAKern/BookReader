import webbrowser

import customtkinter as ctk

from ui.colors import COLORS


def create_labeled_entry(parent, label, textvariable=None, placeholder=""):
    """Поле ввода с видимой подписью над ним."""
    block = ctk.CTkFrame(parent, fg_color="transparent")
    block.pack(fill="x", padx=20, pady=(0, 12))

    ctk.CTkLabel(
        block,
        text=label,
        anchor="w",
        text_color=COLORS["text_muted"],
        font=ctk.CTkFont(size=13),
    ).pack(fill="x", pady=(0, 4))

    entry = ctk.CTkEntry(
        block,
        textvariable=textvariable,
        placeholder_text=placeholder or label,
        placeholder_text_color=COLORS["text_muted"],
        text_color=COLORS["text_main"],
        fg_color=COLORS["bg_main"],
        border_color=COLORS["bg_card"],
    )
    entry.pack(fill="x")

    return entry


def create_link_button(parent, url, text="🛒 Открыть на маркетплейсе"):
    """Кнопка-ссылка для перехода на маркетплейс."""
    if not url:
        return None

    button = ctk.CTkButton(
        parent,
        text=text,
        anchor="w",
        height=28,
        fg_color="transparent",
        hover_color=COLORS["bg_main"],
        text_color=COLORS["accent"],
        font=ctk.CTkFont(size=13, underline=True),
        command=lambda: webbrowser.open(url),
    )
    button.pack(anchor="w", pady=(0, 4))
    return button
