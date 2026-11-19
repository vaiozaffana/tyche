# Contracts

Public browser contracts use Zod in `packages/contracts`; FastAPI validates the same boundary with Pydantic models. `packages/api-client` owns credentialed fetch calls and response parsing.

## Rules

- Keep request normalization, optional/null semantics, and camelCase JSON names aligned in Pydantic and Zod.
- Use ISO timestamp strings in public JSON. Keep ORM records and Celery payload objects internal.
- Validate at every external boundary: HTTP input, browser responses, and queued task payloads.
- Keep `packages/contracts` browser-safe; it cannot import applications or server infrastructure.
- Treat an omitted profile image as “preserve” and explicit empty/null as “clear.”
- Add a focused boundary test when parsing or error mapping changes.

Cross-language generation is intentionally not included: the template has a small stable surface, and code generation would add more machinery than the current contracts require. If the API grows substantially, generate the TypeScript client from FastAPI OpenAPI rather than adding handwritten duplicates.
