import json
import uuid
from pathlib import Path

from storage.paths import get_data_dir

DEVICE_ID_FILE = get_data_dir() / "device_id.json"


def get_device_id() -> str:
    if DEVICE_ID_FILE.exists():
        try:
            data = json.loads(DEVICE_ID_FILE.read_text(encoding="utf-8"))
            device_id = str(data.get("device_id", "")).strip()
            if device_id:
                return device_id
        except (OSError, json.JSONDecodeError, TypeError):
            pass

    device_id = str(uuid.uuid4())
    DEVICE_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
    DEVICE_ID_FILE.write_text(
        json.dumps({"device_id": device_id}, ensure_ascii=False, indent=4),
        encoding="utf-8",
    )
    return device_id
