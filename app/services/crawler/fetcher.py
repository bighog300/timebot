import httpx

from app.services.crawler.types import FetchResult


class HttpFetcher:
    def __init__(self, timeout_seconds: float = 10.0):
        self.timeout_seconds = timeout_seconds

    def fetch(self, url: str) -> FetchResult:
        try:
            response = httpx.get(url, timeout=self.timeout_seconds, follow_redirects=True)
        except Exception as exc:
            return FetchResult(ok=False, error_type=exc.__class__.__name__, error_message=str(exc))

        content_type = response.headers.get("content-type")
        if response.status_code != 200:
            return FetchResult(ok=False, status_code=response.status_code, content_type=content_type)

        return FetchResult(ok=True, status_code=response.status_code, content_type=content_type, text=response.text)
