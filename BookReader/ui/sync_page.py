from datetime import datetime
from tkinter import filedialog, messagebox
import threading

import customtkinter as ctk

from services.cloud_provider import CloudProviderError
from services.google_auth import authorize_google_drive, is_google_drive_authorized
from services.sync_service import SyncService
from storage.paths import get_data_dir
from storage.sync_config import (
    DEFAULT_REMOTE_FILE,
    PROVIDER_FOLDER,
    PROVIDER_GOOGLE_DRIVE,
    PROVIDER_NONE,
    PROVIDER_WEBDAV,
    SyncConfig,
    load_sync_config,
    save_sync_config,
)
from ui.colors import COLORS


class SyncPage(ctk.CTkFrame):

    def __init__(
        self,
        parent,
        books,
        reading_log,
        *,
        on_sync_complete=None,
        on_persist_books=None,
        on_persist_reading_log=None,
    ):
        super().__init__(parent, fg_color="transparent")
        self.books = books
        self.reading_log = reading_log
        self.on_sync_complete = on_sync_complete
        self.on_persist_books = on_persist_books
        self.on_persist_reading_log = on_persist_reading_log

        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 12))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="☁️ Облачная синхронизация",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLORS["text_main"],
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text="Синхронизирует библиотеку и журнал чтения между ПК и телефоном.",
            text_color=COLORS["text_muted"],
            font=ctk.CTkFont(size=13),
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        body = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg_card"], corner_radius=12)
        body.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 24))
        body.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.status_label = ctk.CTkLabel(
            body,
            text="",
            justify="left",
            anchor="w",
            text_color=COLORS["text_muted"],
            font=ctk.CTkFont(size=13),
        )
        self.status_label.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 16))

        ctk.CTkLabel(body, text="Способ", text_color=COLORS["text_main"]).grid(
            row=1, column=0, sticky="w", padx=20, pady=8,
        )
        self.provider_var = ctk.StringVar(value="Отключено")
        self.provider_menu = ctk.CTkOptionMenu(
            body,
            variable=self.provider_var,
            values=["Отключено", "Папка облака", "WebDAV", "Google Drive"],
            command=self._on_provider_change,
            fg_color=COLORS["bg_main"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
        )
        self.provider_menu.grid(row=1, column=1, sticky="ew", padx=20, pady=8)

        self.folder_label = ctk.CTkLabel(body, text="Папка облака", text_color=COLORS["text_main"])
        self.folder_entry = ctk.CTkEntry(body, fg_color=COLORS["bg_main"])
        self.folder_button = ctk.CTkButton(
            body,
            text="Обзор…",
            width=90,
            command=self._browse_folder,
            fg_color=COLORS["bg_main"],
            hover_color=COLORS["accent_hover"],
        )

        self.webdav_url_label = ctk.CTkLabel(body, text="URL WebDAV", text_color=COLORS["text_main"])
        self.webdav_url_entry = ctk.CTkEntry(body, fg_color=COLORS["bg_main"])
        self.webdav_user_label = ctk.CTkLabel(body, text="Логин", text_color=COLORS["text_main"])
        self.webdav_user_entry = ctk.CTkEntry(body, fg_color=COLORS["bg_main"])
        self.webdav_pass_label = ctk.CTkLabel(body, text="Пароль", text_color=COLORS["text_main"])
        self.webdav_pass_entry = ctk.CTkEntry(body, show="*", fg_color=COLORS["bg_main"])

        self.google_secrets_label = ctk.CTkLabel(
            body,
            text="OAuth-клиент Google",
            text_color=COLORS["text_main"],
        )
        self.google_secrets_entry = ctk.CTkEntry(body, fg_color=COLORS["bg_main"])
        self.google_secrets_button = ctk.CTkButton(
            body,
            text="Обзор…",
            width=90,
            command=self._browse_google_secrets,
            fg_color=COLORS["bg_main"],
            hover_color=COLORS["accent_hover"],
        )
        self.google_connect_button = ctk.CTkButton(
            body,
            text="Подключить Google",
            command=self._connect_google,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["bg_main"],
        )
        self.google_status_label = ctk.CTkLabel(
            body,
            text="",
            text_color=COLORS["text_muted"],
            font=ctk.CTkFont(size=12),
        )
        self.google_folder_label = ctk.CTkLabel(
            body,
            text="ID папки Google Drive",
            text_color=COLORS["text_main"],
        )
        self.google_folder_entry = ctk.CTkEntry(body, fg_color=COLORS["bg_main"])
        self.google_folder_hint = ctk.CTkLabel(
            body,
            text="Необязательно. Оставьте пустым для корня «Мой диск».",
            text_color=COLORS["text_muted"],
            font=ctk.CTkFont(size=12),
        )

        ctk.CTkLabel(body, text="Имя файла", text_color=COLORS["text_main"]).grid(
            row=9, column=0, sticky="w", padx=20, pady=8,
        )
        self.remote_file_entry = ctk.CTkEntry(body, fg_color=COLORS["bg_main"])
        self.remote_file_entry.grid(row=9, column=1, sticky="ew", padx=20, pady=8)

        buttons = ctk.CTkFrame(body, fg_color="transparent")
        buttons.grid(row=10, column=0, columnspan=2, sticky="ew", padx=20, pady=(16, 20))
        buttons.grid_columnconfigure((0, 1, 2), weight=1)

        # Сохраняем кнопки, чтобы управлять их состоянием
        self.btn_save = ctk.CTkButton(
            buttons, text="Сохранить настройки", command=self._save_settings,
            fg_color=COLORS["bg_main"], hover_color=COLORS["accent_hover"],
        )
        self.btn_save.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.btn_test = ctk.CTkButton(
            buttons, text="Проверить", command=self._test_connection,
            fg_color=COLORS["bg_main"], hover_color=COLORS["accent_hover"],
        )
        self.btn_test.grid(row=0, column=1, sticky="ew", padx=6)

        self.btn_sync = ctk.CTkButton(
            buttons, text="Синхронизировать", command=self._sync_now,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            text_color=COLORS["bg_main"], font=ctk.CTkFont(weight="bold"),
        )
        self.btn_sync.grid(row=0, column=2, sticky="ew", padx=(6, 0))

        self._load_settings()
        self._refresh_status()

    def _provider_display_map(self) -> dict[str, str]:
        return {
            PROVIDER_NONE: "Отключено",
            PROVIDER_FOLDER: "Папка облака",
            PROVIDER_WEBDAV: "WebDAV",
            PROVIDER_GOOGLE_DRIVE: "Google Drive",
        }

    def _provider_from_display(self, label: str) -> str:
        reverse = {value: key for key, value in self._provider_display_map().items()}
        return reverse.get(label, PROVIDER_NONE)

    def _load_settings(self) -> None:
        config = load_sync_config()
        self.provider_var.set(self._provider_display_map().get(config.provider, "Отключено"))
        self.folder_entry.delete(0, "end")
        self.folder_entry.insert(0, config.folder_path)
        self.webdav_url_entry.delete(0, "end")
        self.webdav_url_entry.insert(0, config.webdav_url)
        self.webdav_user_entry.delete(0, "end")
        self.webdav_user_entry.insert(0, config.webdav_username)
        self.webdav_pass_entry.delete(0, "end")
        self.webdav_pass_entry.insert(0, config.webdav_password)
        self.google_secrets_entry.delete(0, "end")
        self.google_secrets_entry.insert(0, config.google_client_secrets)
        self.google_folder_entry.delete(0, "end")
        self.google_folder_entry.insert(0, config.google_folder_id)
        self.remote_file_entry.delete(0, "end")
        self.remote_file_entry.insert(0, config.remote_file or DEFAULT_REMOTE_FILE)
        self._on_provider_change(self.provider_var.get())
        self._refresh_google_status()

    def _collect_config(self) -> SyncConfig:
        provider = self._provider_from_display(self.provider_var.get())
        existing = load_sync_config()
        password = self.webdav_pass_entry.get().strip()
        if not password:
            password = existing.webdav_password

        return SyncConfig(
            provider=provider,
            remote_file=self.remote_file_entry.get().strip() or DEFAULT_REMOTE_FILE,
            folder_path=self.folder_entry.get().strip(),
            webdav_url=self.webdav_url_entry.get().strip(),
            webdav_username=self.webdav_user_entry.get().strip(),
            webdav_password=password,
            google_client_secrets=self.google_secrets_entry.get().strip(),
            google_token_path=existing.google_token_path,
            google_folder_id=self.google_folder_entry.get().strip(),
            last_sync_at=existing.last_sync_at,
        )

    def _on_provider_change(self, _value: str) -> None:
        provider = self._provider_from_display(self.provider_var.get())

        for widget in (
            self.folder_label, self.folder_entry, self.folder_button,
            self.webdav_url_label, self.webdav_url_entry,
            self.webdav_user_label, self.webdav_user_entry,
            self.webdav_pass_label, self.webdav_pass_entry,
            self.google_secrets_label, self.google_secrets_entry,
            self.google_secrets_button, self.google_connect_button,
            self.google_status_label, self.google_folder_label,
            self.google_folder_entry, self.google_folder_hint,
        ):
            widget.grid_remove()

        if provider == PROVIDER_FOLDER:
            self.folder_label.grid(row=2, column=0, sticky="w", padx=20, pady=8)
            self.folder_entry.grid(row=2, column=1, sticky="ew", padx=(20, 0), pady=8)
            self.folder_button.grid(row=2, column=1, sticky="e", padx=20, pady=8)
        elif provider == PROVIDER_WEBDAV:
            self.webdav_url_label.grid(row=3, column=0, sticky="w", padx=20, pady=8)
            self.webdav_url_entry.grid(row=3, column=1, sticky="ew", padx=20, pady=8)
            self.webdav_user_label.grid(row=4, column=0, sticky="w", padx=20, pady=8)
            self.webdav_user_entry.grid(row=4, column=1, sticky="ew", padx=20, pady=8)
            self.webdav_pass_label.grid(row=5, column=0, sticky="w", padx=20, pady=8)
            self.webdav_pass_entry.grid(row=5, column=1, sticky="ew", padx=20, pady=8)
        elif provider == PROVIDER_GOOGLE_DRIVE:
            self.google_secrets_label.grid(row=2, column=0, sticky="w", padx=20, pady=8)
            self.google_secrets_entry.grid(
                row=2, column=1, sticky="ew", padx=(20, 0), pady=8,
            )
            self.google_secrets_button.grid(row=2, column=1, sticky="e", padx=20, pady=8)
            self.google_connect_button.grid(row=3, column=1, sticky="w", padx=20, pady=8)
            self.google_status_label.grid(
                row=3, column=1, sticky="e", padx=20, pady=8,
            )
            self.google_folder_label.grid(row=4, column=0, sticky="w", padx=20, pady=8)
            self.google_folder_entry.grid(row=4, column=1, sticky="ew", padx=20, pady=8)
            self.google_folder_hint.grid(row=5, column=1, sticky="w", padx=20, pady=(0, 8))
            self._refresh_google_status()

    def _browse_folder(self) -> None:
        path = filedialog.askdirectory(title="Выберите папку облака")
        if path:
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, path)

    def _browse_google_secrets(self) -> None:
        path = filedialog.askopenfilename(
            title="Выберите OAuth-клиент Google",
            filetypes=[("JSON", "*.json"), ("Все файлы", "*.*")],
        )
        if path:
            self.google_secrets_entry.delete(0, "end")
            self.google_secrets_entry.insert(0, path)

    def _refresh_google_status(self) -> None:
        config = self._collect_config()
        if not config.google_client_secrets.strip():
            self.google_status_label.configure(text="Файл OAuth-клиента не выбран")
            return
        if is_google_drive_authorized(
            config.google_client_secrets,
            config.google_token_path,
        ):
            self.google_status_label.configure(text="Подключено")
        else:
            self.google_status_label.configure(text="Требуется авторизация")

    def _set_syncing_state(self, is_syncing: bool):
        """Блокирует кнопки и меняет текст, пока идет сетевая операция"""
        state = "disabled" if is_syncing else "normal"
        self.btn_save.configure(state=state)
        self.btn_test.configure(state=state)
        self.btn_sync.configure(state=state)

        if is_syncing:
            self.btn_sync.configure(text="⏳ Синхронизация...")
            self.status_label.configure(text="☁️ Идет обмен данными с облаком... Пожалуйста, подождите.")
        else:
            self.btn_sync.configure(text="Синхронизировать")
            self._refresh_status()

    def _sync_now(self) -> None:
        config = self._collect_config()
        save_sync_config(config)
        self._set_syncing_state(True)

        def _background_sync():
            # Переименовал в sync_result, чтобы не путаться
            sync_result = SyncService.sync(self.books, self.reading_log, config)
            # Возвращаемся в главный поток для безопасного обновления UI
            self.after(0, lambda: self._finish_sync(sync_result))

        threading.Thread(target=_background_sync, daemon=True).start()

    def _save_settings(self) -> None:
        """Сохраняет настройки синхронизации"""
        config = self._collect_config()
        save_sync_config(config)
        self._refresh_status()
        self._refresh_google_status()
        messagebox.showinfo("Настройки", "Настройки синхронизации сохранены.")

    def _finish_sync(self, sync_result):
        self._set_syncing_state(False)

        if sync_result.success or sync_result.books_after != sync_result.books_before:
            if self.on_persist_books:
                self.on_persist_books(show_error=False)
            if self.on_persist_reading_log:
                self.on_persist_reading_log(show_error=False)
            if self.on_sync_complete:
                self.on_sync_complete()

        if sync_result.success:
            messagebox.showinfo("Синхронизация", sync_result.message)
        else:
            messagebox.showerror("Синхронизация", sync_result.message)

    def _test_connection(self) -> None:
        config = self._collect_config()
        self.btn_test.configure(state="disabled", text="⏳ Проверка...")

        def _background_test():
            ok, message = SyncService.test_connection(config)
            self.after(0, lambda: self._finish_test(ok, message))

        threading.Thread(target=_background_test, daemon=True).start()

    def _finish_test(self, ok, message):
        self.btn_test.configure(state="normal", text="Проверить")
        if ok:
            messagebox.showinfo("Облако", message)
        else:
            messagebox.showerror("Облако", message)

    def _connect_google(self) -> None:
        config = self._collect_config()
        if not config.google_client_secrets.strip():
            messagebox.showerror(
                "Google Drive",
                "Сначала укажите файл OAuth-клиента Google (client_secret*.json).",
            )
            return

        save_sync_config(config)
        self.google_connect_button.configure(state="disabled", text="⏳ Ожидание браузера...")

        def _background_auth():
            try:
                authorize_google_drive(
                    config.google_client_secrets,
                    config.google_token_path,
                )
                self.after(0, self._on_auth_success)
            except Exception as error:
                self.after(0, lambda: self._on_auth_error(str(error)))

        threading.Thread(target=_background_auth, daemon=True).start()

    def _on_auth_success(self):
        self.google_connect_button.configure(state="normal", text="Подключить Google")
        self._refresh_google_status()
        self._refresh_status()
        messagebox.showinfo("Google Drive", "Аккаунт Google подключен. Теперь можно синхронизировать.")

    def _on_auth_error(self, error_msg):
        self.google_connect_button.configure(state="normal", text="Подключить Google")
        messagebox.showerror("Google Drive", error_msg)

    def _refresh_status(self) -> None:
        config = load_sync_config()
        last_sync = "ещё не синхронизировали"
        if config.last_sync_at:
            try:
                moment = datetime.fromisoformat(config.last_sync_at.replace("Z", "+00:00"))
                last_sync = moment.strftime("%d.%m.%Y %H:%M")
            except ValueError:
                last_sync = config.last_sync_at

        self.status_label.configure(
            text=(
                f"Способ: {config.provider_label()}\n"
                f"Последняя синхронизация: {last_sync}\n"
                f"Книг в библиотеке: {len(self.books)}\n"
                f"Локальные данные: {get_data_dir()}"
            )
        )
