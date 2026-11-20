"""Small bilingual title matcher used before paid page reads."""

import re

from tyche_ai.job_search.models import Candidate, ParsedQuery

SYNONYMS = {
    "pengembang": "developer",
    "developer": "developer",
    "akuntan": "accountant",
    "accountant": "accountant",
    "insinyur": "engineer",
    "engineer": "engineer",
    "perancang": "designer",
    "designer": "designer",
    "pemasaran": "marketing",
    "marketing": "marketing",
}


def _tokens(value: str) -> set[str]:
    return {SYNONYMS.get(token, token) for token in re.findall(r"\w+", value.lower())}


def title_matches(
    candidate: Candidate, query: ParsedQuery, *, threshold: float = 0.5
) -> tuple[bool, float]:
    title = _tokens(candidate.title)
    scores = []
    for role in query.target_roles:
        role_tokens = _tokens(role)
        if role_tokens:
            scores.append(len(title & role_tokens) / len(role_tokens))
    score = max(scores, default=0.0)
    return score >= threshold, score
