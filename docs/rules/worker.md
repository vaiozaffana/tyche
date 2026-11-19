# Worker

`apps/worker` owns Celery task registration and processors. `packages/queue` owns the Celery factory, task names, payload/result models, and producer helpers. Run the worker with `moon run worker:dev` while Redis is available.

## Rules

- Define task names and Pydantic payload/result models in `repo_queue.contracts`.
- Validate before enqueueing and again inside processors.
- Keep processors broker-independent in `apps/worker/src/worker/processors` so unit tests need no Redis.
- Configure JSON-only serialization and Redis in the shared Celery factory.
- Assume tasks may run more than once. Make side effects idempotent or add a deliberate deduplication strategy.
- Set retries/backoff deliberately for real tasks; invalid payloads must not retry forever.
- Log task identifiers and errors, never whole sensitive payloads.

## Adding a task

1. Add its contract and stable task name in `packages/queue`.
2. Add a producer helper that validates before `send_task`.
3. Implement and test the processor, then register a thin decorated task in `worker/tasks.py`.
4. Verify real delivery against Redis when changing broker behavior.

Run `moon run worker:lint worker:format-check worker:typecheck worker:test`.
