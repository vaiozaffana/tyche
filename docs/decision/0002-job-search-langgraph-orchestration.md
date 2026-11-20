---
status: accepted
date: 2026-11-20
supersedes: []
superseded_by: null
---

# Use a bounded LangGraph workflow with predefined and dynamic subagents

## Context

Job discovery combines paid providers, untrusted web content, and runtime-specific hiring rubrics.
An LLM supervisor or tool-calling loop would make call order, cost, and retries hard to audit.

## Decision

Use a fixed LangGraph parent workflow with four predefined subagents and code-generated dynamic
assessors. LLMs parse, plan rubrics, and assess. Deterministic nodes own pagination, deduplication,
title filtering, Firecrawl gates, budgets, routing, and ranking. Dynamic assessors receive no tools.

Stage 1 is SerpApi Google Jobs; Stage 2 is cache-first Firecrawl for matching incomplete postings.
LangGraph runtime context carries injected dependencies and `Send` provides bounded assessment
fan-out. PostgreSQL rows, not a LangGraph checkpointer, are the source of truth.

## Alternatives

- An LLM supervisor was rejected because it cannot guarantee paid-call order or limits.
- ReAct/tool-calling agents were rejected because scraped prompt injection could trigger tools.
- A static rubric only was rejected because it cannot adapt extraction focus across role families.

## Consequences

The topology and cost are testable and degraded provider output can still produce results. Adding a
tool or new gate requires deterministic code and tests. The browser contract remains deferred.

The live SerpApi coverage probe on 2026-11-20 detected a configured key, but SerpApi rejected its
first query. The probe stopped immediately, so there is no live source-coverage claim yet.

## Status history

| Date       | Status   | Reason            |
| ---------- | -------- | ----------------- |
| 2026-11-20 | accepted | Initial decision. |
