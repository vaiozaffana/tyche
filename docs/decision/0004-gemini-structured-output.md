---
status: accepted
date: 2026-11-20
supersedes: []
superseded_by: null
---

# Access Gemini through a structured-output boundary

## Context

Gemini 3.8 Flash requires supported thinking levels and must not receive deprecated sampling or
candidate-count parameters. Provider behavior must be fakeable in every unit test.

## Decision

Use the direct `google-genai` SDK behind `StructuredLLM`. Requests set a JSON response schema,
system instruction, output cap, and `low|medium` thinking level only. They never set temperature,
top-p, top-k, candidate count, or tools. Transient status codes are classified separately from
permanent failures. Tests use `FakeStructuredLLM`.

The installed `langchain-google-genai` 4.5.1 was rejected after its builder always emitted
`candidate_count=1`; direct `google-genai` 3.6.1 generated the required minimal config.

## Alternatives

- The LangChain wrapper was rejected because it could not omit `candidate_count`.
- Raw unvalidated JSON was rejected because every agent boundary needs typed validation.
- Function/tool calling was rejected because it introduces thought-signature and injection risks.

## Consequences

Provider-specific code stays in one adapter, tests make no paid calls, and future model changes must
re-run the request-shape and live structured-output probes. The live Gemini probe remains pending
because no key was available during implementation.

## Status history

| Date       | Status   | Reason            |
| ---------- | -------- | ----------------- |
| 2026-11-20 | accepted | Initial decision. |
