import os
from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_data_dir() -> Path:
    if env_path := os.environ.get("BOOK_TRACKER_DATA"):
        return Path(env_path)
    return get_project_root() / "data"
