import json
import os
import tempfile
from pathlib import Path
from typing import Optional

from storage.paths import get_data_dir

READING_LOG_FILE = get_data_dir() / "reading_log.json"


def load_reading_log(data_file: Optional[Path] = None) -> dict[str, int]:
    path = data_file or READING_LOG_FILE
    if not path.exists():
        return {}

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}

    if not isinstance(data, dict):
        return {}

    log: dict[str, int] = {}
    for key, value in data.items():
        if not isinstance(key, str):
            continue
        try:
            pages = int(value)
        except (TypeError, ValueError):
            continue
        if pages > 0:
            log[key] = pages
    return log


def save_reading_log(log: dict[str, int], data_file: Optional[Path] = None) -> None:
    path = data_file or READING_LOG_FILE
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = json.dumps(log, ensure_ascii=False, indent=4)

    fd, tmp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=".reading_log_",
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
