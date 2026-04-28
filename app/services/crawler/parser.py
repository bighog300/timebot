from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse


class _AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        for key, value in attrs:
            if key.lower() == "href" and value:
                self.links.append(value)


class LinkParser:
    def extract_links(self, html: str, *, base_url: str) -> list[str]:
        parser = _AnchorParser()
        parser.feed(html)

        base_domain = urlparse(base_url).netloc
        links: list[str] = []
        for href in parser.links:
            joined = urljoin(base_url, href)
            parsed = urlparse(joined)
            if parsed.scheme not in {"http", "https"}:
                continue
            if parsed.netloc != base_domain:
                continue
            links.append(joined)
        return links
