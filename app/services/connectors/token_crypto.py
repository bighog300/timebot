from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings

_ENCRYPTED_PREFIX = "enc:v1:"


class ConnectorTokenCrypto:
    """Encrypt/decrypt connector OAuth tokens with Fernet."""

    def __init__(self) -> None:
        self._fernet: Fernet | None = None

    def _require_fernet(self) -> Fernet:
        if self._fernet is not None:
            return self._fernet

        key = settings.CONNECTOR_TOKEN_ENCRYPTION_KEY.strip()
        if not key:
            raise RuntimeError(
                "CONNECTOR_TOKEN_ENCRYPTION_KEY is required when using connector OAuth token storage"
            )

        try:
            self._fernet = Fernet(key.encode("utf-8"))
        except Exception as exc:  # pragma: no cover - defensive config guard
            raise RuntimeError(
                "CONNECTOR_TOKEN_ENCRYPTION_KEY must be a valid Fernet key "
                "(URL-safe base64-encoded 32-byte value)"
            ) from exc
        return self._fernet

    @staticmethod
    def is_encrypted(value: str | None) -> bool:
        return bool(value) and value.startswith(_ENCRYPTED_PREFIX)

    def encrypt(self, value: str | None) -> str | None:
        if value is None:
            return None
        token = self._require_fernet().encrypt(value.encode("utf-8")).decode("utf-8")
        return f"{_ENCRYPTED_PREFIX}{token}"

    def decrypt(self, value: str | None) -> str | None:
        if value is None:
            return None
        if not self.is_encrypted(value):
            return value

        payload = value[len(_ENCRYPTED_PREFIX):]
        try:
            decrypted = self._require_fernet().decrypt(payload.encode("utf-8"))
        except InvalidToken as exc:
            raise RuntimeError("Failed to decrypt connector token: invalid key or token payload") from exc
        return decrypted.decode("utf-8")


connector_token_crypto = ConnectorTokenCrypto()
