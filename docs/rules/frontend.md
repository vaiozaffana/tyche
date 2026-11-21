# Frontend

The React application lives in `apps/web`. Run it with `moon run web:dev`.

## Rules

- Route files own routing/access redirects; substantial UI belongs in `src/features/<feature>`.
- Use TanStack Query for server state and local React state for form drafts.
- Use the credentialed Axios client from `src/api.ts` for auth, session, and feature operations.
- Parse public responses with Zod and reuse shared schemas for form validation.
- Use `@repo/ui` for reusable primitives. Keep product components in the app.
- TanStack AI owns agent message state. AI Elements are product-owned renderers, not a second chat
  state system. Render known tools as typed UI and never expose raw tool JSON to users.
- Agent UI must make submitted, streaming, approval, completion, cancellation, timeout, and failure
  states visible in the conversation. Bound stalled requests and provide stop or retry recovery.
- TanStack Query owns persisted search state. Agent client tools must invalidate or update the same
  cache keys used by ordinary product UI.
- Pacer queues and smooths browser work only; server-side limits remain the cost and abuse boundary.
- Treat `VITE_*` values as public and validate them in `src/config.ts`.
- Never edit `src/routeTree.gen.ts` manually.

Run `moon run web:typecheck web:test web:build` after changing routes or shared UI.
