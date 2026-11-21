# Job Search

The MVP is an authenticated, asynchronous pipeline. `apps/api` creates and reads searches,
`packages/queue` carries only the search ID, `apps/worker` owns Celery retries, `apps/ai` owns the
LangGraph workflow and providers, and `packages/db` owns the three persisted tables.

## Stages and subagents

1. `query_analyst` parses Indonesian or English prompts into a typed query.
2. `specialist_planner` creates at most three guarded specialist specs; invalid output falls back
   to a deterministic general specialist.
3. `job_scout` calls only SerpApi's Google Jobs engine (`hl=id`, `gl=id`).
4. Deterministic code deduplicates and filters titles.
5. `page_reader` calls Firecrawl only for matching jobs with incomplete descriptions, cache first.
6. Runtime `job_assessor` subgraphs score jobs without tools; deterministic code ranks and caps them.
7. The web UI polls the persisted run and renders ranked results. Its TanStack AI loop may create or
   inspect runs through the authenticated API, but cannot call search or page-reading providers.

The predefined team is exactly `query_analyst`, `specialist_planner`, `job_scout`, and
`page_reader`. Dynamic specialists may vary only their allowlisted role family, rubric, extraction
focus, signals, reasoning level (`low|medium`), and output budget. They cannot request tools.

## Deterministic gates and budgets

A page read is skipped in this order: missing URL, title mismatch, sufficient description,
blocked domain, exhausted budget. A description needs enrichment when it is below
`JOB_SEARCH_MIN_DESCRIPTION_CHARS` or has neither a qualification/responsibility/salary marker nor
SerpApi highlights. LinkedIn is blocked by default. Per-run defaults are 2 SerpApi calls, 5
Firecrawl reads, 10 assessed jobs, 3 specialists, 10 returned results, and 4 concurrent LLM calls.
The PostgreSQL scrape cache defaults to 24 hours.

## Extending and swapping components

- Add a predefined subagent by defining isolated input/output schemas and a builder, then add it to
  `PREDEFINED_SUBAGENTS` and its exact-team test.
- Add a role family or extraction focus in `agents/dynamic/spec.py`, update guardrails/defaults, and
  add routing and malicious-spec tests.
- Swap providers by implementing `StructuredLLM`, `JobSearchProvider`, or `PageReader` and injecting
  it into `RunContext`. Keep cost gates outside provider and LLM code.
- Do not add tool-calling loops inside this paid workflow without a new decision record and
  thought-signature handling. The separately bounded UI loop is covered by decision 0005.

## Running and testing

```sh
moon run ai:lint ai:format-check ai:typecheck ai:test ai:build
uv run --package tyche-ai python -m tyche_ai.job_search.cli --fake "backend Python Jakarta"
uv run --package tyche-ai python -m tyche_ai.job_search.cli_probe
```

The probe performs 15 Stage-1 calls only when `SERPAPI_API_KEY` exists; otherwise it exits safely.
The React workspace, Zod contracts, and Axios client expose this workflow to authenticated users.
They do not own provider budgets or ranking.

Log search IDs, counts, hashed candidate keys, spec IDs, and reason codes only. Never log keys,
session tokens, prompts, descriptions, page bodies, or free-text specialist fields. User prompts and
scraped text stay inside explicitly delimited untrusted-data blocks before reaching an LLM.
