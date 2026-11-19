# Frontend

The React application lives in `apps/web`. Run it with `moon run web:dev`.

## Rules

- Route files own routing/access redirects; substantial UI belongs in `src/features/<feature>`.
- Use TanStack Query for server state and local React state for form drafts.
- Use the credentialed fetch client from `src/api.ts` for auth, session, and feature operations.
- Parse public responses with Zod and reuse shared schemas for form validation.
- Use `@repo/ui` for reusable primitives. Keep product components in the app.
- Treat `VITE_*` values as public and validate them in `src/config.ts`.
- Never edit `src/routeTree.gen.ts` manually.

Run `moon run web:typecheck web:test web:build` after changing routes or shared UI.
