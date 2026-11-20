"""Candidate duplicate removal."""

import re
from urllib.parse import urlparse

from tyche_ai.job_search.models import Candidate

LEGAL_SUFFIXES = {"pt", "tbk", "cv", "inc", "ltd", "llc"}


def _normalize(value: str, *, company: bool = False) -> str:
    tokens = re.findall(r"\w+", value.lower())
    if company:
        tokens = [token for token in tokens if token not in LEGAL_SUFFIXES]
    return " ".join(tokens)


def candidate_key(candidate: Candidate) -> tuple[str, str, str]:
    return (
        _normalize(candidate.title),
        _normalize(candidate.company, company=True),
        _normalize(candidate.location),
    )


def deduplicate(
    candidates: list[Candidate], preferred_hosts: tuple[str, ...] = ()
) -> list[Candidate]:
    chosen: dict[tuple[str, str, str], Candidate] = {}
    order: list[tuple[str, str, str]] = []
    for candidate in candidates:
        key = candidate_key(candidate)
        if key not in chosen:
            order.append(key)
            chosen[key] = candidate
            continue
        current = chosen[key]
        candidate_host = urlparse(candidate.source_url or "").hostname or ""
        current_host = urlparse(current.source_url or "").hostname or ""
        candidate_score = (
            any(host in candidate_host for host in preferred_hosts),
            len(candidate.description),
        )
        current_score = (
            any(host in current_host for host in preferred_hosts),
            len(current.description),
        )
        if candidate_score > current_score:
            candidate.highlights = list(dict.fromkeys([*current.highlights, *candidate.highlights]))
            chosen[key] = candidate
        else:
            current.highlights = list(dict.fromkeys([*current.highlights, *candidate.highlights]))
    return [chosen[key] for key in order]
