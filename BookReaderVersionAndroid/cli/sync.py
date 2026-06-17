from models.book import Book
from services.sync_service import SyncResult, SyncService
from storage.paths import get_data_dir
from storage.reading_log import save_reading_log
from storage.storage import save_books
from storage.sync_config import (
    DEFAULT_REMOTE_FILE,
    PROVIDER_FOLDER,
    PROVIDER_NONE,
    PROVIDER_WEBDAV,
    SyncConfig,
    load_sync_config,
    save_sync_config,
)

from cli.display import (
    ask_int,
    ask_text,
    ask_yes_no,
    clear_screen,
    pause,
    print_error,
    print_header,
    print_hint,
    print_key_value,
    print_section,
    print_success,
)


class SyncScreen:

    def __init__(self, books: list[Book], reading_log: dict[str, int]):
        self.books = books
        self.reading_log = reading_log

    def run(self) -> None:
        while True:
            config = load_sync_config()
            clear_screen()
            print_header("☁️ Облачная синхронизация")
            print_hint("Синхронизирует библиотеку и журнал чтения между ПК и телефоном.")
            print_section("Статус")
            print_key_value("Способ", config.provider_label())
            print_key_value("Файл", config.remote_file or DEFAULT_REMOTE_FILE)
            if config.provider == PROVIDER_FOLDER and config.folder_path:
                print_key_value("Папка", config.folder_path)
            elif config.provider == PROVIDER_WEBDAV and config.webdav_url:
                print_key_value("WebDAV", config.webdav_url)
            print_key_value("Последняя", _format_sync_time(config.last_sync_at))
            print_key_value("Книг", str(len(self.books)))
            print_key_value("Данные", str(get_data_dir()))

            print(
                "\n  1. Синхронизировать сейчас\n"
                "  2. Настройки облака\n"
                "  3. Проверить подключение\n"
                "  0. Назад"
            )

            choice = ask_int("\n  Пункт", min_value=0, max_value=3)
            if choice is None:
                continue
            if choice == 0:
                return
            if choice == 1:
                self._sync_now()
            elif choice == 2:
                self._configure()
            elif choice == 3:
                self._test_connection()

    def _sync_now(self) -> None:
        clear_screen()
        print_header("☁️ Синхронизация")
        print_hint("Скачиваем облако, объединяем с локальными данными и загружаем обратно.")

        result = SyncService.sync(self.books, self.reading_log)
        self._show_result(result)

        if result.success:
            try:
                save_books(self.books)
                save_reading_log(self.reading_log)
            except OSError as error:
                print_error(f"Не удалось сохранить локально: {error}")

        pause()

    def _test_connection(self) -> None:
        clear_screen()
        print_header("☁️ Проверка подключения")
        ok, message = SyncService.test_connection()
        if ok:
            print_success(message)
        else:
            print_error(message)
        pause()

    def _configure(self) -> None:
        config = load_sync_config()

        clear_screen()
        print_header("☁️ Настройки облака")
        print_section("Способ синхронизации")
        print("  1. Папка облака (Google Drive, Яндекс.Диск, Dropbox…)")
        print("  2. WebDAV (Яндекс.Диск, Nextcloud…)")
        print("  3. Отключить облако")
        print("  0. Назад")

        choice = ask_int("\n  Пункт", min_value=0, max_value=3)
        if choice is None or choice == 0:
            return

        if choice == 3:
            config.provider = PROVIDER_NONE
            save_sync_config(config)
            print_success("Облачная синхронизация отключена")
            pause()
            return

        if choice == 1:
            self._configure_folder(config)
        elif choice == 2:
            self._configure_webdav(config)

    def _configure_folder(self, config: SyncConfig) -> None:
        clear_screen()
        print_header("☁️ Папка облака")
        print_hint(
            "Укажите папку, которую облачный клиент синхронизирует на этом устройстве. "
            "На ПК и телефоне должна быть одна и та же облачная папка."
        )
        print_hint("Termux: например /storage/emulated/0/Download/BookTracker")

        folder = ask_text("Путь к папке", default=config.folder_path or None)
        if not folder:
            pause()
            return

        remote_file = ask_text(
            "Имя файла",
            default=config.remote_file or DEFAULT_REMOTE_FILE,
        ) or DEFAULT_REMOTE_FILE

        config.provider = PROVIDER_FOLDER
        config.folder_path = folder
        config.remote_file = remote_file
        save_sync_config(config)

        ok, message = SyncService.test_connection(config)
        if ok:
            print_success(f"Папка настроена. {message}")
        else:
            print_error(message)
        pause()

    def _configure_webdav(self, config: SyncConfig) -> None:
        clear_screen()
        print_header("☁️ WebDAV")
        print_hint("Яндекс.Диск: https://webdav.yandex.ru/")
        print_hint("Nextcloud: https://example.com/remote.php/dav/files/USER/")

        url = ask_text("URL WebDAV", default=config.webdav_url or None)
        if not url:
            pause()
            return

        username = ask_text("Логин", default=config.webdav_username or None)
        if not username:
            pause()
            return

        password = ask_text("Пароль приложения")
        if password is None:
            pause()
            return

        remote_file = ask_text(
            "Файл в облаке",
            default=config.remote_file or DEFAULT_REMOTE_FILE,
        ) or DEFAULT_REMOTE_FILE

        config.provider = PROVIDER_WEBDAV
        config.webdav_url = url
        config.webdav_username = username
        config.webdav_password = password
        config.remote_file = remote_file
        save_sync_config(config)

        ok, message = SyncService.test_connection(config)
        if ok:
            print_success(f"WebDAV настроен. {message}")
        else:
            print_error(message)
        pause()

    def _show_result(self, result: SyncResult) -> None:
        if result.success:
            print_success(result.message)
        else:
            print_error(result.message)

        print_section("Итог")
        print_key_value("Было книг", str(result.books_before))
        print_key_value("Стало книг", str(result.books_after))
        if result.books_added:
            print_key_value("Добавлено", str(result.books_added))
        if result.books_updated:
            print_key_value("Обновлено", str(result.books_updated))


def _format_sync_time(value: str) -> str:
    if not value:
        return "ещё не синхронизировали"
    try:
        from datetime import datetime

        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return moment.strftime("%d.%m.%Y %H:%M")
    except ValueError:
        return value
