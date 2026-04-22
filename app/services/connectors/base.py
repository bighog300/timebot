from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass
class OAuthStartResult:
    authorization_url: str
    state: str


@dataclass
class OAuthTokenResult:
    account_email: str | None
    account_id: str | None
    access_token: str
    refresh_token: str | None
    expires_at: datetime | None
    scopes: list[str]


@dataclass
class SyncResult:
    added: int
    updated: int
    failed: int
    bytes_synced: int
    files_seen: int


class ConnectorProvider(Protocol):
    provider_type: str
    display_name: str

    def build_authorization_url(self, *, state: str) -> OAuthStartResult:
        ...

    def exchange_code_for_tokens(self, *, code: str) -> OAuthTokenResult:
        ...

    def list_remote_files(self, *, access_token: str, page_size: int = 100) -> list[dict]:
        ...
