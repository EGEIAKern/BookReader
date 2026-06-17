import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from models.book import Book
from models.work import Work, WORK_STATUS_FINISHED
from services.cloud_provider import CloudProviderError, build_cloud_provider
from storage.device_id import get_device_id
from storage.sync_config import SyncConfig, load_sync_config, save_sync_config

SYNC_SCHEMA_VERSION = 1


@dataclass
class SyncResult:
    success: bool
    message: str
    books_before: int = 0
    books_after: int = 0
    books_added: int = 0
    books_updated: int = 0
    remote_found: bool = False
    uploaded: bool = False


def _normalize_text(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def _authors_compatible(left: str, right: str) -> bool:
    a = _normalize_text(left)
    b = _normalize_text(right)
    if not a or not b:
        return not a and not b
    if a == b:
        return True
    if a in b or b in a:
        return True
    a_parts = a.split()
    b_parts = b.split()
    return bool(a_parts and b_parts and a_parts[-1] == b_parts[-1])


def books_match(left: Book, right: Book) -> bool:
    if _normalize_text(left.title) != _normalize_text(right.title):
        return False
    return _authors_compatible(left.author, right.author)


def _pick_author(left: str, right: str) -> str:
    left = (left or "").strip()
    right = (right or "").strip()
    if not left:
        return right
    if not right:
        return left
    return left if len(left) >= len(right) else right


def _work_key(work: Work) -> str:
    return work.title.strip().lower()


def _merge_works(primary: list[Work], secondary: list[Work]) -> list[Work]:
    merged: dict[str, Work] = {_work_key(work): work for work in primary}

    for work in secondary:
        key = _work_key(work)
        if key not in merged:
            merged[key] = work
            continue

        existing = merged[key]
        if work.current_page > existing.current_page:
            merged[key] = Work(
                title=work.title or existing.title,
                total_pages=max(existing.total_pages, work.total_pages),
                current_page=work.current_page,
                status=work.status,
            )
        elif work.current_page == existing.current_page:
            status = work.status
            if existing.status == WORK_STATUS_FINISHED:
                status = existing.status
            merged[key] = Work(
                title=existing.title or work.title,
                total_pages=max(existing.total_pages, work.total_pages),
                current_page=existing.current_page,
                status=status,
            )

    return list(merged.values())


def merge_book_pair(left: Book, right: Book) -> Book:
    if right.effective_current_page > left.effective_current_page:
        primary, secondary = right, left
    else:
        primary, secondary = left, right

    works: list[Work] = []
    if primary.has_works or secondary.has_works:
        works = _merge_works(
            list(primary.works),
            list(secondary.works),
        )

    current_page = primary.current_page
    if works:
        current_page = 0

    return Book(
        title=primary.title or secondary.title,
        author=_pick_author(primary.author, secondary.author),
        total_pages=max(left.total_pages, right.total_pages),
        current_page=current_page,
        description=primary.description or secondary.description,
        marketplace_url=primary.marketplace_url or secondary.marketplace_url,
        review=primary.review or secondary.review,
        works=works,
    )


def _book_changed(before: Book, after: Book) -> bool:
    return (
        after.effective_current_page != before.effective_current_page
        or after.review != before.review
        or after.description != before.description
        or len(after.works) != len(before.works)
        or after.author != before.author
    )


def merge_books(local: list[Book], remote: list[Book]) -> tuple[list[Book], int, int]:
    merged: list[Book] = []
    added = 0
    updated = 0

    def upsert(book: Book, *, from_remote: bool) -> None:
        nonlocal added, updated
        for index, existing in enumerate(merged):
            if not books_match(existing, book):
                continue
            before = existing
            merged[index] = merge_book_pair(existing, book)
            if _book_changed(before, merged[index]):
                updated += 1
            return

        merged.append(book)
        if from_remote:
            added += 1

    for book in local:
        upsert(book, from_remote=False)
    for book in remote:
        upsert(book, from_remote=True)

    return merged, added, updated


def merge_reading_logs(
    local: dict[str, int],
    remote: dict[str, int],
) -> dict[str, int]:
    merged = dict(local)
    for day, pages in remote.items():
        if pages <= 0:
            continue
        merged[day] = merged.get(day, 0) + pages
    return merged


def build_sync_bundle(
    books: list[Book],
    reading_log: dict[str, int],
    *,
    device_id: str | None = None,
) -> dict:
    return {
        "schema_version": SYNC_SCHEMA_VERSION,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "device_id": device_id or get_device_id(),
        "books": [book.to_dict() for book in books],
        "reading_log": reading_log,
    }


def parse_sync_bundle(raw: str) -> tuple[list[Book], dict[str, int]]:
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Неверный формат файла синхронизации")

    books_data = data.get("books", [])
    log_data = data.get("reading_log", {})

    books: list[Book] = []
    if isinstance(books_data, list):
        for item in books_data:
            if isinstance(item, dict):
                try:
                    books.append(Book.from_dict(item))
                except (TypeError, ValueError):
                    continue

    reading_log: dict[str, int] = {}
    if isinstance(log_data, dict):
        for key, value in log_data.items():
            if not isinstance(key, str):
                continue
            try:
                pages = int(value)
            except (TypeError, ValueError):
                continue
            if pages > 0:
                reading_log[key] = pages

    return books, reading_log


def serialize_sync_bundle(bundle: dict) -> str:
    return json.dumps(bundle, ensure_ascii=False, indent=2)


class SyncService:

    @staticmethod
    def sync(
        books: list[Book],
        reading_log: dict[str, int],
        config: Optional[SyncConfig] = None,
    ) -> SyncResult:
        config = config or load_sync_config()
        books_before = len(books)

        if not config.is_configured():
            return SyncResult(
                success=False,
                message="Сначала настройте облако.",
                books_before=books_before,
                books_after=books_before,
            )

        try:
            provider = build_cloud_provider(config)
        except CloudProviderError as error:
            return SyncResult(
                success=False,
                message=str(error),
                books_before=books_before,
                books_after=books_before,
            )

        remote_raw: str | None
        try:
            remote_raw = provider.download()
        except CloudProviderError as error:
            return SyncResult(
                success=False,
                message=str(error),
                books_before=books_before,
                books_after=books_before,
            )

        remote_found = remote_raw is not None
        remote_books: list[Book] = []
        remote_log: dict[str, int] = {}

        if remote_raw:
            try:
                remote_books, remote_log = parse_sync_bundle(remote_raw)
            except (json.JSONDecodeError, ValueError) as error:
                return SyncResult(
                    success=False,
                    message=f"Файл в облаке повреждён: {error}",
                    books_before=books_before,
                    books_after=books_before,
                    remote_found=True,
                )

        merged_books, added, updated = merge_books(books, remote_books)
        merged_log = merge_reading_logs(reading_log, remote_log)

        books[:] = merged_books
        reading_log.clear()
        reading_log.update(merged_log)

        bundle = build_sync_bundle(merged_books, merged_log)
        payload = serialize_sync_bundle(bundle)

        try:
            provider.upload(payload)
        except CloudProviderError as error:
            return SyncResult(
                success=False,
                message=f"Данные объединены локально, но загрузка не удалась: {error}",
                books_before=books_before,
                books_after=len(books),
                books_added=added,
                books_updated=updated,
                remote_found=remote_found,
            )

        config.last_sync_at = bundle["updated_at"]
        save_sync_config(config)

        parts = ["Синхронизация завершена."]
        if remote_found:
            if added or updated:
                details = []
                if added:
                    details.append(f"+{added} книг")
                if updated:
                    details.append(f"обновлено {updated}")
                parts.append("Из облака: " + ", ".join(details) + ".")
            else:
                parts.append("Облако уже было актуальным.")
        else:
            parts.append("Создан новый файл в облаке.")

        return SyncResult(
            success=True,
            message=" ".join(parts),
            books_before=books_before,
            books_after=len(books),
            books_added=added,
            books_updated=updated,
            remote_found=remote_found,
            uploaded=True,
        )

    @staticmethod
    def test_connection(config: Optional[SyncConfig] = None) -> tuple[bool, str]:
        config = config or load_sync_config()
        if not config.is_configured():
            return False, "Облако не настроено"

        try:
            provider = build_cloud_provider(config)
            provider.download()
        except CloudProviderError as error:
            return False, str(error)

        return True, "Подключение успешно"
