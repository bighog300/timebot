"""One-off backfill for legacy plaintext connector tokens.

Run after setting CONNECTOR_TOKEN_ENCRYPTION_KEY to convert old plaintext rows to
encrypted-at-rest values.
"""

from app.db.session import SessionLocal
from app.models.relationships import Connection
from app.services.connectors.token_crypto import connector_token_crypto


def main() -> None:
    db = SessionLocal()
    try:
        rows = db.query(Connection).all()
        updated = 0
        for conn in rows:
            for field in ("access_token", "refresh_token"):
                value = getattr(conn, field)
                if value and not connector_token_crypto.is_encrypted(value):
                    setattr(conn, field, connector_token_crypto.encrypt(value))
                    updated += 1
                    db.add(conn)
        db.commit()
        print(f"Re-encrypted {updated} connector token values")
    finally:
        db.close()


if __name__ == "__main__":
    main()
