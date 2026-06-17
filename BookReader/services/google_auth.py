from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from services.cloud_provider import CloudProviderError
from storage.paths import get_data_dir

GOOGLE_DRIVE_SCOPES = ("https://www.googleapis.com/auth/drive.file",)
DEFAULT_GOOGLE_TOKEN_FILE = "google_token.json"


def get_google_token_path(token_path: str = "") -> Path:
    if token_path.strip():
        return Path(token_path).expanduser()
    return get_data_dir() / DEFAULT_GOOGLE_TOKEN_FILE


def load_google_credentials(
    client_secrets_path: str,
    token_path: str = "",
) -> Optional[Credentials]:
    secrets = Path(client_secrets_path).expanduser()
    if not secrets.is_file():
        return None

    token_file = get_google_token_path(token_path)
    if not token_file.is_file():
        return None

    credentials = Credentials.from_authorized_user_file(
        str(token_file),
        GOOGLE_DRIVE_SCOPES,
    )
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        save_google_credentials(credentials, token_path)

    if credentials.valid:
        return credentials
    return None


def save_google_credentials(
    credentials: Credentials,
    token_path: str = "",
) -> Path:
    token_file = get_google_token_path(token_path)
    token_file.parent.mkdir(parents=True, exist_ok=True)
    token_file.write_text(credentials.to_json(), encoding="utf-8")
    return token_file


def authorize_google_drive(
    client_secrets_path: str,
    token_path: str = "",
) -> Credentials:
    secrets = Path(client_secrets_path).expanduser()
    if not secrets.is_file():
        raise CloudProviderError(
            "Укажите файл OAuth-клиента Google (client_secret*.json)."
        )

    flow = InstalledAppFlow.from_client_secrets_file(
        str(secrets),
        GOOGLE_DRIVE_SCOPES,
    )
    credentials = flow.run_local_server(port=0, prompt="consent")
    save_google_credentials(credentials, token_path)
    return credentials


def is_google_drive_authorized(
    client_secrets_path: str,
    token_path: str = "",
) -> bool:
    return load_google_credentials(client_secrets_path, token_path) is not None
