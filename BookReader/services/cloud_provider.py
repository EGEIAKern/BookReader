import base64
import io
import os
import tempfile
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from pathlib import Path

from storage.sync_config import (
    PROVIDER_FOLDER,
    PROVIDER_GOOGLE_DRIVE,
    PROVIDER_WEBDAV,
    SyncConfig,
)


class CloudProviderError(Exception):
    pass


class CloudProvider(ABC):

    @abstractmethod
    def download(self) -> str | None:
        """Return remote JSON text or None if the remote file does not exist."""

    @abstractmethod
    def upload(self, content: str) -> None:
        """Upload JSON text to the remote storage."""


class FolderCloudProvider(CloudProvider):

    def __init__(self, folder_path: str, remote_file: str):
        self.folder = Path(folder_path).expanduser()
        self.remote_file = remote_file or "book_tracker_sync.json"

    @property
    def remote_path(self) -> Path:
        return self.folder / self.remote_file

    def download(self) -> str | None:
        path = self.remote_path
        if not path.exists():
            return None
        try:
            return path.read_text(encoding="utf-8")
        except OSError as error:
            raise CloudProviderError(f"Не удалось прочитать {path}: {error}") from error

    def upload(self, content: str) -> None:
        path = self.remote_path
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp_path = tempfile.mkstemp(
                dir=path.parent,
                prefix=".sync_",
                suffix=".tmp",
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as file:
                    file.write(content)
                    file.flush()
                    os.fsync(file.fileno())
                os.replace(tmp_path, path)
            except OSError:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                raise
        except OSError as error:
            raise CloudProviderError(f"Не удалось сохранить {path}: {error}") from error


class WebDavCloudProvider(CloudProvider):

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        remote_file: str,
    ):
        self.base_url = base_url.rstrip("/") + "/"
        self.username = username
        self.password = password
        self.remote_file = remote_file.lstrip("/") or "book_tracker_sync.json"

    @property
    def remote_url(self) -> str:
        return self.base_url + self.remote_file

    def _auth_header(self) -> str:
        token = base64.b64encode(
            f"{self.username}:{self.password}".encode("utf-8")
        ).decode("ascii")
        return f"Basic {token}"

    def _request(self, method: str, url: str, data: bytes | None = None) -> bytes:
        request = urllib.request.Request(url, data=data, method=method)
        request.add_header("Authorization", self._auth_header())
        if data is not None:
            request.add_header("Content-Type", "application/json; charset=utf-8")

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            if method == "GET" and error.code in {404, 410}:
                return b""
            raise CloudProviderError(
                f"WebDAV {method} {url}: HTTP {error.code}"
            ) from error
        except urllib.error.URLError as error:
            raise CloudProviderError(f"WebDAV недоступен: {error.reason}") from error

    def download(self) -> str | None:
        payload = self._request("GET", self.remote_url)
        if not payload:
            return None
        return payload.decode("utf-8")

    def upload(self, content: str) -> None:
        self._request("PUT", self.remote_url, content.encode("utf-8"))


class GoogleDriveCloudProvider(CloudProvider):

    def __init__(
        self,
        credentials,
        remote_file: str,
        folder_id: str = "",
    ):
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaInMemoryUpload

        self._MediaInMemoryUpload = MediaInMemoryUpload
        self.service = build("drive", "v3", credentials=credentials, cache_discovery=False)
        self.remote_file = remote_file or "book_tracker_sync.json"
        self.folder_id = folder_id.strip()

    def _escape_query_value(self, value: str) -> str:
        return value.replace("\\", "\\\\").replace("'", "\\'")

    def _find_file_id(self) -> str | None:
        query = (
            f"name='{self._escape_query_value(self.remote_file)}' "
            "and trashed=false"
        )
        if self.folder_id:
            query += f" and '{self._escape_query_value(self.folder_id)}' in parents"

        response = (
            self.service.files()
            .list(
                q=query,
                spaces="drive",
                fields="files(id, name)",
                pageSize=1,
            )
            .execute()
        )
        files = response.get("files", [])
        if not files:
            return None
        return files[0]["id"]

    def download(self) -> str | None:
        file_id = self._find_file_id()
        if not file_id:
            return None

        from googleapiclient.http import MediaIoBaseDownload

        request = self.service.files().get_media(fileId=file_id)
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

        payload = buffer.getvalue()
        if not payload:
            return None
        return payload.decode("utf-8")

    def upload(self, content: str) -> None:
        media = self._MediaInMemoryUpload(
            content.encode("utf-8"),
            mimetype="application/json",
            resumable=False,
        )
        file_id = self._find_file_id()
        if file_id:
            self.service.files().update(
                fileId=file_id,
                media_body=media,
            ).execute()
            return

        metadata: dict[str, object] = {"name": self.remote_file}
        if self.folder_id:
            metadata["parents"] = [self.folder_id]
        self.service.files().create(
            body=metadata,
            media_body=media,
            fields="id",
        ).execute()


def build_cloud_provider(config: SyncConfig) -> CloudProvider:
    if config.provider == PROVIDER_FOLDER:
        if not config.folder_path.strip():
            raise CloudProviderError("Не указана папка синхронизации")
        return FolderCloudProvider(config.folder_path, config.remote_file)

    if config.provider == PROVIDER_WEBDAV:
        if not config.webdav_url.strip():
            raise CloudProviderError("Не указан URL WebDAV")
        if not config.webdav_username.strip():
            raise CloudProviderError("Не указан логин WebDAV")
        return WebDavCloudProvider(
            config.webdav_url,
            config.webdav_username,
            config.webdav_password,
            config.remote_file,
        )

    if config.provider == PROVIDER_GOOGLE_DRIVE:
        from services.google_auth import load_google_credentials

        if not config.google_client_secrets.strip():
            raise CloudProviderError("Укажите файл OAuth-клиента Google")
        credentials = load_google_credentials(
            config.google_client_secrets,
            config.google_token_path,
        )
        if credentials is None:
            raise CloudProviderError(
                "Google Drive не подключён. Нажмите «Подключить Google»."
            )
        return GoogleDriveCloudProvider(
            credentials,
            config.remote_file,
            config.google_folder_id,
        )

    raise CloudProviderError("Облако не настроено")
