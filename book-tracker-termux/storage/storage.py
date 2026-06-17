import json
import os
import tempfile
from pathlib import Path
from typing import Optional

from models.book import Book
from storage.paths import get_data_dir

DATA_FILE = get_data_dir() / "books.json"


def load_books(data_file: Optional[Path] = None) -> list[Book]:
    path = data_file or DATA_FILE
    if not path.exists():
        return []

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        return []

    if not isinstance(data, list):
        return []

    books = []
    for item in data:
        if not isinstance(item, dict):
            continue
        try:
            books.append(Book.from_dict(item))
        except (TypeError, ValueError):
            continue
    return books


def save_books(books: list[Book], data_file: Optional[Path] = None) -> None:
    path = data_file or DATA_FILE
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = json.dumps(
        [book.to_dict() for book in books],
        ensure_ascii=False,
        indent=4,
    )

    fd, tmp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=".books_",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            file.write(payload)
            file.flush()
            os.fsync(file.fileno())
        os.replace(tmp_path, path)
    except OSError:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
