from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx

from app.config import settings
from app.services.connectors.base import OAuthStartResult, OAuthTokenResult


class GoogleDriveProvider:
    provider_type = "gdrive"
    display_name = "Google Drive"

    _auth_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
    _token_endpoint = "https://oauth2.googleapis.com/token"
    _files_endpoint = "https://www.googleapis.com/drive/v3/files"
    _userinfo_endpoint = "https://www.googleapis.com/oauth2/v2/userinfo"

    def build_authorization_url(self, *, state: str) -> OAuthStartResult:
        if not settings.GOOGLE_OAUTH_CLIENT_ID or not settings.GOOGLE_OAUTH_REDIRECT_URI:
            raise ValueError("Google OAuth is not configured")

        query = urlencode(
            {
                "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
                "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
                "response_type": "code",
                "scope": " ".join(settings.google_oauth_scopes),
                "access_type": "offline",
                "include_granted_scopes": "true",
                "prompt": "consent",
                "state": state,
            }
        )
        return OAuthStartResult(authorization_url=f"{self._auth_endpoint}?{query}", state=state)

    def exchange_code_for_tokens(self, *, code: str) -> OAuthTokenResult:
        if not settings.GOOGLE_OAUTH_CLIENT_ID or not settings.GOOGLE_OAUTH_CLIENT_SECRET:
            raise ValueError("Google OAuth credentials are not configured")

        payload = {
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
        }

        with httpx.Client(timeout=20.0) as client:
            token_response = client.post(self._token_endpoint, data=payload)
            token_response.raise_for_status()
            token_data = token_response.json()

            userinfo_response = client.get(
                self._userinfo_endpoint,
                headers={"Authorization": f"Bearer {token_data['access_token']}"},
            )
            userinfo_response.raise_for_status()
            profile = userinfo_response.json()

        expires_at = None
        expires_in = token_data.get("expires_in")
        if expires_in:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))

        return OAuthTokenResult(
            account_email=profile.get("email"),
            account_id=profile.get("id"),
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            expires_at=expires_at,
            scopes=(token_data.get("scope") or "").split(),
        )

    def list_remote_files(self, *, access_token: str, page_size: int = 100) -> list[dict]:
        fields = (
            "nextPageToken,files(id,name,mimeType,size,modifiedTime,createdTime,"
            "webViewLink,parents,trashed)"
        )
        files: list[dict] = []
        page_token = None

        with httpx.Client(timeout=20.0) as client:
            while True:
                params = {
                    "pageSize": page_size,
                    "fields": fields,
                    "q": "trashed = false",
                    "orderBy": "modifiedTime desc",
                }
                if page_token:
                    params["pageToken"] = page_token

                response = client.get(
                    self._files_endpoint,
                    params=params,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                response.raise_for_status()
                payload = response.json()
                files.extend(payload.get("files", []))
                page_token = payload.get("nextPageToken")
                if not page_token:
                    break

        return files
