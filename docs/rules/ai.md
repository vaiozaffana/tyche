# AI

`apps/ai` owns job-search orchestration, provider adapters, deterministic screening, and the
offline CLI. It is a workspace package imported by the Celery worker, not a standalone service.

## Rules

- Keep paid provider calls behind typed interfaces and enforce budgets in deterministic code.
- Keep Celery registration and retry policy in `apps/worker`; AI processors remain broker-independent.
- Pass database sessions and validated settings from callers. Do not create engines in AI code.
- Never log API keys, full prompts, page bodies, or free-text specialist specifications.
- Treat prompts and scraped content as untrusted data and delimit them before LLM calls.
- Unit tests use fakes and fixtures. Live provider checks are explicit and skipped without keys.

Run `moon run ai:lint ai:format-check ai:typecheck ai:test ai:build` after changing this area.
