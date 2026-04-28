from collections import deque

from app.services.crawler.types import QueueItem


class CrawlQueue:
    def __init__(self):
        self._queue: deque[QueueItem] = deque()
        self._seen: set[str] = set()

    def enqueue(self, item: QueueItem, normalized_url: str) -> bool:
        if normalized_url in self._seen:
            return False
        self._seen.add(normalized_url)
        self._queue.append(item)
        return True

    def dequeue(self) -> QueueItem | None:
        if not self._queue:
            return None
        return self._queue.popleft()

    def empty(self) -> bool:
        return len(self._queue) == 0
