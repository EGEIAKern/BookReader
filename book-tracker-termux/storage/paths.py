import os
from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_data_dir() -> Path:
    """Каталог данных: BOOK_TRACKER_DATA, ~/.book-tracker (Termux), или ./data."""
    if env_path := os.environ.get("BOOK_TRACKER_DATA"):
        return Path(env_path)

    termux_prefix = os.environ.get("PREFIX", "")
    if termux_prefix.startswith("/data/data/com.termux"):
        return Path.home() / ".book-tracker" / "data"

    return get_project_root() / "data"
