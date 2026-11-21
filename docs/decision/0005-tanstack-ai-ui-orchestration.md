---
status: accepted
date: 2026-11-20
supersedes: []
superseded_by: null
---

# Use TanStack AI for UI orchestration outside the paid search workflow

## Context

The job-search product needs a conversational interface that can render structured UI, request
approval, and operate persisted searches. Decision 0002 keeps paid SerpApi and Firecrawl calls in a
bounded Python LangGraph workflow because an open tool loop cannot guarantee cost or prompt-injection
boundaries.

## Decision

Run a separate TanStack AI loop in the Cloudflare web Worker. It streams AG-UI events to `useChat()`
and receives a fixed tool allowlist. Deterministic server tools inspect briefs and explain the
pipeline. Browser tools reuse the authenticated Axios client to create, read, and list searches;
creating a run and opening an external posting require explicit user approval.

The UI loop never calls SerpApi or Firecrawl. Search status and results remain authoritative in
PostgreSQL and TanStack Query. Conversation state is ephemeral. Product-owned AI Elements render
TanStack AI parts without adding a second chat state library.

## Alternatives

- Extending the Python graph with UI tools was rejected because it mixes interaction with paid work.
- Proxying the browser session through the model Worker was rejected because it expands the secret
  boundary.
- A text-only stream was rejected because approvals and structured search results need dedicated UI.
- Persisting chat was deferred because search runs are the durable user value.

## Consequences

The Worker needs a `GEMINI_API_KEY`, while browser API calls continue to use the HttpOnly session.
Tool definitions must stay fixed on the server. Pacer improves client flow control but is not a
security quota. Provider budgets, retries, ranking, and untrusted page handling remain governed by
decision 0002.

## Status history

| Date       | Status   | Reason            |
| ---------- | -------- | ----------------- |
| 2026-11-20 | accepted | Initial decision. |
