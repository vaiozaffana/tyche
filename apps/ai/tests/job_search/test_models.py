from concurrent.futures import ThreadPoolExecutor

from tyche_ai.job_search.models import Budget


def test_budget_counters_are_atomic_and_bounded() -> None:
    budget = Budget(max_serp_calls=1, max_firecrawl_calls=3, max_llm_jobs=1)

    with ThreadPoolExecutor(max_workers=8) as executor:
        outcomes = list(executor.map(lambda _: budget.take_firecrawl(), range(20)))

    assert sum(outcomes) == 3
    assert budget.firecrawl_calls == 3
    assert budget.take_serp()
    assert not budget.take_serp()
