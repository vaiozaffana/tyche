"""Small deterministic helpers for parent graph nodes."""

import hashlib
import re

from tyche_ai.job_search.models import Candidate
from tyche_ai.job_search.screening.dedup import candidate_key


def candidate_id(candidate: Candidate) -> str:
    stable = "|".join(candidate_key(candidate))
    return hashlib.sha256(stable.encode()).hexdigest()[:16]


def recency_days(posted_at: str | None) -> int:
    if not posted_at:
        return 10_000
    lowered = posted_at.lower()
    if "hour" in lowered or "jam" in lowered or "today" in lowered or "hari ini" in lowered:
        return 0
    match = re.search(r"\d+", lowered)
    value = int(match.group()) if match else 10_000
    if "week" in lowered or "minggu" in lowered:
        return value * 7
    if "month" in lowered or "bulan" in lowered:
        return value * 30
    return value
