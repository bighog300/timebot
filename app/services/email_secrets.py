from __future__ import annotations
import base64, hashlib
from cryptography.fernet import Fernet
from app.config import settings
from app.services.connectors.token_crypto import connector_token_crypto

class EmailSecretCrypto:
    def decrypt(self, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            return connector_token_crypto.decrypt(value)
        except Exception:
            if value.startswith("enc:fallback:"):
                key = base64.urlsafe_b64encode(hashlib.sha256(settings.AUTH_SECRET_KEY.encode('utf-8')).digest())
                return Fernet(key).decrypt(value.split("enc:fallback:",1)[1].encode()).decode()
            raise

    def encrypt(self, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            return connector_token_crypto.encrypt(value)
        except RuntimeError:
            key = base64.urlsafe_b64encode(hashlib.sha256(settings.AUTH_SECRET_KEY.encode('utf-8')).digest())
            return f"enc:fallback:{Fernet(key).encrypt(value.encode()).decode()}"

email_secret_crypto = EmailSecretCrypto()
