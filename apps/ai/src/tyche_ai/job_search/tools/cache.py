"""Scrape cache boundary used before the database-backed implementation exists."""

from threading import Lock
from typing import Protocol

from tyche_ai.job_search.models import PageContent


class ScrapeCache(Protocol):
    def get(self, url: str) -> PageContent | None: ...

    def put(self, url: str, content: PageContent) -> None: ...


class InMemoryScrapeCache:
    def __init__(self) -> None:
        self._items: dict[str, PageContent] = {}
        self._lock = Lock()

    def get(self, url: str) -> PageContent | None:
        with self._lock:
            return self._items.get(url)

    def put(self, url: str, content: PageContent) -> None:
        with self._lock:
            self._items[url] = content
