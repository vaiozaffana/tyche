"""TTL scrape cache backed by the shared database."""

import hashlib
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Literal, cast
from urllib.parse import urlsplit, urlunsplit

from repo_db import ScrapeCacheEntry, utc_now
from sqlalchemy.orm import Session

from tyche_ai.job_search.models import PageContent


def normalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, parts.query, ""))


def url_hash(url: str) -> str:
    return hashlib.sha256(normalize_url(url).encode()).hexdigest()


class DatabaseScrapeCache:
    def __init__(
        self,
        session: Session,
        *,
        ttl: timedelta,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self.session = session
        self.ttl = ttl
        self.clock = clock

    def get(self, url: str) -> PageContent | None:
        entry = self.session.get(ScrapeCacheEntry, url_hash(url))
        if not entry or entry.fetched_at < self.clock() - self.ttl:
            return None
        return PageContent(
            status=cast(Literal["ok", "failed", "blocked"], entry.status),
            markdown=entry.content,
        )

    def put(self, url: str, content: PageContent) -> None:
        self.session.merge(
            ScrapeCacheEntry(
                url_hash=url_hash(url),
                url=normalize_url(url),
                status=content.status,
                content=content.markdown,
                fetched_at=self.clock(),
            )
        )
        self.session.flush()
