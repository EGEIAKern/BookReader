import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from storage.paths import get_data_dir

SYNC_CONFIG_FILE = get_data_dir() / "sync_config.json"

PROVIDER_NONE = "none"
PROVIDER_FOLDER = "folder"
PROVIDER_WEBDAV = "webdav"

DEFAULT_REMOTE_FILE = "book_tracker_sync.json"


@dataclass
class SyncConfig:
    provider: str = PROVIDER_NONE
    remote_file: str = DEFAULT_REMOTE_FILE
    folder_path: str = ""
    webdav_url: str = ""
    webdav_username: str = ""
    webdav_password: str = ""
    last_sync_at: str = ""

    def is_configured(self) -> bool:
        if self.provider == PROVIDER_FOLDER:
            return bool(self.folder_path.strip())
        if self.provider == PROVIDER_WEBDAV:
            return bool(
                self.webdav_url.strip()
                and self.webdav_username.strip()
            )
        return False

    def provider_label(self) -> str:
        labels = {
            PROVIDER_NONE: "не настроено",
            PROVIDER_FOLDER: "папка облака",
            PROVIDER_WEBDAV: "WebDAV",
        }
        return labels.get(self.provider, self.provider)


def _apply_env_overrides(config: SyncConfig) -> SyncConfig:
    if folder := os.environ.get("BOOK_TRACKER_SYNC_FOLDER", "").strip():
        config.provider = PROVIDER_FOLDER
        config.folder_path = folder

    if url := os.environ.get("BOOK_TRACKER_WEBDAV_URL", "").strip():
        config.provider = PROVIDER_WEBDAV
        config.webdav_url = url
    if user := os.environ.get("BOOK_TRACKER_WEBDAV_USER", "").strip():
        config.webdav_username = user
    if password := os.environ.get("BOOK_TRACKER_WEBDAV_PASSWORD"):
        config.webdav_password = password

    if remote_file := os.environ.get("BOOK_TRACKER_SYNC_FILE", "").strip():
        config.remote_file = remote_file

    return config


def load_sync_config(config_file: Optional[Path] = None) -> SyncConfig:
    path = config_file or SYNC_CONFIG_FILE
    if not path.exists():
        return _apply_env_overrides(SyncConfig())

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _apply_env_overrides(SyncConfig())

    if not isinstance(data, dict):
        return _apply_env_overrides(SyncConfig())

    config = SyncConfig(
        provider=str(data.get("provider", PROVIDER_NONE)),
        remote_file=str(data.get("remote_file", DEFAULT_REMOTE_FILE) or DEFAULT_REMOTE_FILE),
        folder_path=str(data.get("folder_path", "")),
        webdav_url=str(data.get("webdav_url", "")),
        webdav_username=str(data.get("webdav_username", "")),
        webdav_password=str(data.get("webdav_password", "")),
        last_sync_at=str(data.get("last_sync_at", "")),
    )
    return _apply_env_overrides(config)


def save_sync_config(config: SyncConfig, config_file: Optional[Path] = None) -> None:
    path = config_file or SYNC_CONFIG_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(config), ensure_ascii=False, indent=4),
        encoding="utf-8",
    )
