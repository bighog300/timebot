from app.services.connectors.base import ConnectorProvider
from app.services.connectors.google_drive import GoogleDriveProvider


_PROVIDERS: dict[str, ConnectorProvider] = {
    "gdrive": GoogleDriveProvider(),
}


def get_provider(provider_type: str) -> ConnectorProvider:
    if provider_type not in _PROVIDERS:
        raise KeyError(provider_type)
    return _PROVIDERS[provider_type]


def list_provider_types() -> list[str]:
    return sorted(_PROVIDERS.keys())
