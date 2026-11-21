# ExecPlan: Generative Job Search UI

This ExecPlan is a living document. Update `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` while the work proceeds. The
repository references `.agent/PLANS.md`, but that file is absent in this checkout;
this plan follows the established self-contained format in
`docs/plans/job-search-mvp.md` instead.

Repository: `vaiozaffana/tyche`.

## 1. Purpose and user-visible outcome

A signed-in user can describe the work they want in natural language, approve an
agent-proposed search, watch the existing asynchronous job-search pipeline run,
and inspect ranked results without leaving one responsive workspace. The agent is
more than a token stream: TanStack AI sends AG-UI-compatible SSE events, executes
both server and browser tools, exposes approvals, and renders tool-specific UI.

The visual language is fixed by the product owner:

- warm off-white `#F6F5F2` is the dominant page surface;
- carbon `#111111` owns text and structural lines;
- electric vermilion `#FF2E00` is the only accent and primary action color;
- concrete `#E5E3DC` is the secondary surface;
- Bricolage Grotesque is display/brand, Inter is core UI, and JetBrains Mono is
  metadata, timestamps, handles, and metrics.

Design read: a focused job-search product for active candidates, using a clean
editorial-operational language. Dials are variance 6, motion 4, density 6. The
interface is an authenticated product workspace, not a marketing landing page;
real product state is its visual asset, so decorative photography and fake
screenshots are intentionally excluded.

## 2. Existing system and boundaries

The completed backend from `docs/plans/job-search-mvp.md` already owns paid search
execution:

- FastAPI creates and reads searches at `POST /job-searches`,
  `GET /job-searches`, and `GET /job-searches/{id}`.
- Celery runs a bounded Python LangGraph pipeline. Deterministic code owns paid
  provider gates, budgets, ranking, and retry behavior.
- PostgreSQL is the source of truth. The browser polls status and results.

This work must not move SerpApi or Firecrawl access into the chat agent. The UI
agent may propose and invoke the authenticated API, but the Python workflow keeps
all paid-provider controls. This preserves decision 0002 while adding a separate
TypeScript UI-agent loop.

Current frontend facts:

- `apps/web` is a React 19/Vite SPA deployed as a Cloudflare Worker with static
  assets.
- TanStack Router and Query already exist. `@repo/ui` is the shadcn-style shared
  primitive layer.
- `@repo/api-client` currently uses `fetch`; public job-search Zod contracts do
  not exist yet.
- The current dashboard is an account overview and has no job-search route.

## 3. Scope map

The smallest complete change reaches every layer below.

| Area             | Required change                                                                                                                                                                        |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Public contracts | Add job-search request/response schemas and focused tests.                                                                                                                             |
| HTTP boundary    | Move the shared browser client to one credentialed Axios instance; preserve current auth/profile errors and add job-search calls.                                                      |
| Server state     | Add TanStack Query options/mutations, polling only while a run is queued/running, and list invalidation after completion.                                                              |
| Agent transport  | Add a Cloudflare Worker `/api/chat` route using TanStack AI `chat()`, Gemini, AG-UI request parsing, SSE output, bounded iterations, and safe errors.                                  |
| Tools            | Add allowlisted server tools plus authenticated client tools for creating/loading/listing searches and opening an external posting. Creation and external navigation require approval. |
| Flow control     | Use TanStack Pacer to queue rapid prompts, reject excess sends, throttle high-frequency status announcements, and batch Query invalidations.                                           |
| Generative UI    | Render text, thinking, tool states, approvals, search runs, and result collections with customized AI Elements/shadcn components.                                                      |
| Product shell    | Replace the generic dashboard with the agent workspace, add search history/detail navigation, and keep profile/auth routes working.                                                    |
| Configuration    | Document public API URL, worker API URL/model, and Gemini secret handling without exposing a key.                                                                                      |
| Tests            | Contract, Axios error mapping, query polling, tool schemas, worker request validation, and pure UI formatter tests.                                                                    |
| Docs             | Update frontend/contracts/deployment/job-search rules, README, and add an accepted decision for the UI-agent boundary.                                                                 |

Potential breakage to guard:

- Axios must still send credentials and preserve `UnauthorizedApiError` behavior.
- The agent must never receive or log cookies, session tokens, provider keys,
  complete job descriptions, or arbitrary backend error bodies.
- Client-declared tools cannot expand the server allowlist.
- Repeated agent messages cannot bypass the API's per-user active-search guard or
  create duplicate jobs without explicit approval.
- SSE responses must not be cached, and cancelled runs must stop client work.
- Theme changes must not regress login, registration, profile, or shared UI
  contrast.

## 4. Architecture

### 4.1 Browser data path

`@repo/api-client` owns an Axios instance configured with `withCredentials: true`.
Feature services parse every response with `@repo/contracts`. TanStack Query owns
remote job-search state. Local React state is limited to the draft prompt,
selected run, disclosure state, and ephemeral agent UI.

The browser talks directly to FastAPI for authenticated search data. This avoids
forwarding an HttpOnly session through the AI model or storing it in the Worker.
The client tools call the same Axios client as the ordinary UI and return only the
minimal structured result required by the agent.

### 4.2 Agent path

The Cloudflare Worker handles only `/api/chat`; all other requests go to static
assets. It parses the AG-UI request with `chatParamsFromRequest`, runs
`chat()` using the Gemini adapter, and returns `toServerSentEventsResponse()`.
The system prompt is narrow: help operate this product, call only registered
tools, never invent search state, and never claim a job exists without a tool
result.

Server tools are deterministic and non-privileged:

- `inspect_search_brief` validates a proposed prompt and returns a short,
  structured readiness report for generative rendering.
- `explain_search_pipeline` returns the fixed stages and privacy/cost boundary.

Authenticated actions are client tools:

- `create_job_search` calls FastAPI and requires approval because it queues paid
  provider work.
- `get_job_search` and `list_job_searches` read the user's persisted state.
- `open_job_posting` requires approval before opening an external URL.

The server receives only the known shared definitions for client tools. It does
not merge arbitrary client-declared tools. The agent loop is capped at six model
turns. This loop orchestrates UI tools only; it does not alter the bounded Python
job-search graph.

### 4.3 Generative rendering

`useChat()` owns message/run state and uses the SSE connection. Message parts are
rendered by type. Each known tool name has a dedicated typed component rather
than a raw JSON dump. Tool lifecycle states cover preparing, awaiting approval,
running, completed, denied, and failed. Search results use TanStack Query as the
authoritative live state after creation.

AI Elements supply the conversation, message, prompt input, reasoning, and tool
surface primitives. They are customized to this product's tokens and adapted to
TanStack AI message shapes; Vercel AI SDK state does not become a second chat
state system.

### 4.4 Pacer responsibilities

- `AsyncQueuer`, concurrency 1: retain rapid submissions and send them in order.
- `AsyncRateLimiter`: allow at most six chat starts per 60 seconds in the client
  as a UX quota. FastAPI's active-search cap remains the security/cost boundary.
- `Throttler`/React throttling hook: limit high-frequency prompt metadata updates
  without delaying the controlled input.
- `Batcher`: combine query invalidations caused by tool results and terminal
  polling transitions.

Pacer state is in-memory and is explicitly not an abuse-prevention mechanism.

## 5. Milestones

### Milestone 0: Baseline and evidence

- Read repository rules and accepted decisions.
- Verify current TanStack AI, Pacer, Query, Axios, AI Elements, and Cloudflare
  Worker APIs from current primary documentation.
- Run focused frontend baseline checks.

Acceptance: baseline results and any pre-existing failures are recorded below.

### Milestone 1: Typed HTTP and server state

- Add `packages/contracts/src/job-search.ts` plus parsing tests for all statuses,
  nullable salary/score fields, timestamps, and malformed URLs.
- Replace the fetch helper inside `@repo/api-client` with Axios without changing
  its public auth/profile API. Add search methods and tests.
- Add job-search feature services and TanStack Query hooks. Poll every two seconds
  only while active, stop on terminal state, and batch list invalidations.

Acceptance: contract and client tests pass, and current auth/profile callers need
no changes beyond imports if possible.

### Milestone 2: TanStack AI edge route and tools

- Add the Worker entry and route configuration.
- Add shared tool definitions and server/client implementations.
- Stream Gemini chat through SSE, cap iterations, merge no arbitrary tools, map
  validation/provider errors to safe HTTP/SSE errors, and disable caching.
- Add deterministic worker/tool tests without calling Gemini.

Acceptance: a recorded request fixture produces a valid SSE response with a fake
adapter or isolated handler; invalid AG-UI input returns 400; no secret enters a
response or log.

### Milestone 3: Product UI and generative components

- Apply the fixed semantic token palette and self-hosted fonts.
- Recompose the app shell around job search and retain profile/logout/theme
  controls.
- Build the agent workspace, history, live run panel, ranked result cards, and
  responsive mobile layout.
- Add AI Elements-based conversation, prompt, reasoning, tool, and approval
  surfaces. Implement loading, empty, error, denied, cancelled, queued, running,
  completed, and failed states.
- Integrate Pacer queue/rate-limit/throttle/batch behavior and stop/cancel.

Acceptance: the primary flow works with keyboard only at 320, 768, 1024, and
1440 CSS pixels; focus remains visible; reduced motion is honored; no visible
copy uses an em dash; all primary controls have descriptive labels.

### Milestone 4: Documentation and full verification

- Add the UI-agent decision record and update repository rules and README.
- Run formatting, checks, type checking, tests, and production build.
- Exercise the app in a real browser. Inspect console/network, both themes,
  responsive breakpoints, keyboard focus, and the live or safe fake agent flow.
- Run a live Gemini request only if a key is configured, without printing it.

Acceptance: all available local gates pass. Live-provider and deployment checks
are reported separately from static/local checks.

## 6. Progress

- [x] Read the three selected skill instructions and relevant repository rules.
- [x] Confirm the referenced `.agent/PLANS.md` is absent.
- [x] Inspect the current frontend, API client, UI package, job-search API, and
      Cloudflare deployment shape.
- [x] Verify current TanStack AI, Pacer, AI Elements, and Cloudflare Worker
      patterns from Context7 and primary documentation.
- [x] Run the focused baseline: contracts 5, API client 3, and web 1 tests passed;
      frontend typecheck and production build passed before implementation.
- [x] Complete Milestone 1: shared schemas, credentialed Axios, query polling,
      and cache synchronization are implemented and focused tests pass.
- [x] Complete Milestone 2: the bounded Worker route, fixed server/client tools,
      approvals, safe missing-secret behavior, and deterministic tests are implemented.
- [x] Complete Milestone 3: the real browser verified both themes, exact tokens
      and fonts, visible keyboard focus, reduced motion, and no horizontal
      overflow at 320, 768, 1024, and 1440 CSS pixels. A live server tool
      rendered structured UI; a deterministic SSE fixture verified the
      approval interrupt without starting paid work.
- [x] Complete Milestone 4: documentation and repository-wide check, typecheck,
      test, and build gates pass.

## 7. Surprises and discoveries

- The original job-search decision bans tool-calling loops inside the Python
  paid-provider workflow. A separate UI-agent loop can coexist without weakening
  it only if client/server tools never directly invoke SerpApi or Firecrawl.
- TanStack AI's current client can declare tools, but accepting arbitrary
  `params.tools` with `mergeAgentTools` expands the model-visible tool surface.
  This implementation will pass a fixed allowlist of shared definitions instead.
- AI Elements examples use Vercel AI SDK message types. The visual components are
  reusable, but TanStack AI remains the only message state owner.
- TanStack Pacer rate limiters are in-memory and primarily client-side. They
  improve flow control but cannot replace FastAPI's persisted active-search cap.
- Cloudflare Worker static assets can selectively run the Worker first for
  `/api/*` and fall through through the `ASSETS` binding for the SPA.
- The official AI Elements registry currently pulls a second AI SDK and a large
  markdown/highlighting stack. The product keeps the generated component pattern
  but trims it to the five primitives needed by TanStack AI.
- Running multiple Vitest projects concurrently exhausted local fork workers and
  timed out. The same suites pass when run separately; this was test-process
  contention, not a product failure.
- React Strict Mode runs hook cleanup once during development, which stopped the
  Pacer queue before its first item. Starting the idempotent queue after enqueue
  keeps production behavior unchanged and makes development submissions reliable.
- Gemini authenticated successfully and a live `explain_search_pipeline` call
  streamed a 200 SSE response into its four-stage generative renderer. A later
  search-approval prompt remained provider-pending for more than four minutes and
  was stopped; the fake adapter fixture proves the same tool call ends in a bound
  approval interrupt without invoking the paid backend.

## 8. Decision log

- 2026-11-20: Keep the Python LangGraph workflow unchanged. The TypeScript
  TanStack AI loop is an interaction/orchestration layer only.
- 2026-11-20: Use browser client tools for authenticated FastAPI actions. This
  reuses the existing HttpOnly-cookie boundary and avoids exposing or proxying a
  session through the model server.
- 2026-11-20: Use one chat system: TanStack AI. AI Elements contribute owned UI
  components only; do not add Vercel AI SDK chat state.
- 2026-11-20: No chat persistence in this phase. Search runs/results are already
  persisted and are the valuable state; conversation state remains ephemeral.
- 2026-11-20: Use the existing Lucide dependency because it is already the
  repository-wide icon family. Adding another icon package would not improve the
  product enough to justify a mixed system.
- 2026-11-21: Load the root `GEMINI_API_KEY` only for `vite serve`. Production
  builds merely declare the required Worker secret, so local convenience cannot
  serialize the credential into client assets.

## 9. Verification commands

Focused:

    moon run contracts:test api-client:test web:test web:typecheck web:build web:bundle-check

Repository-wide:

    pnpm check
    pnpm typecheck
    pnpm test
    pnpm build

Browser acceptance:

- authenticate, create a search through approval, observe queued/running state,
  inspect terminal results, open a posting through approval, stop an active chat,
  and recover from a failed chat/search;
- inspect console errors and the `/api/chat` SSE request;
- test 320, 768, 1024, and 1440 widths, keyboard navigation, reduced motion, and
  light/dark themes.

## 10. Outcomes and retrospective

The code path has one durable source of search truth and one ephemeral agent
state owner. Axios and TanStack Query own authenticated persisted state. TanStack
AI streams fixed server/client tools, while Pacer serializes and limits prompt
flow. Product-owned AI Elements render text, reasoning, tool output, live runs,
result collections, and approval decisions without adding a second chat state.

Repository-wide formatting/lint/boundary checks, strict type checks, 83 Python
tests, 24 TypeScript tests, and all production builds pass. Browser acceptance
verified the live SSE server-tool renderer, API requests, responsive widths,
keyboard focus, reduced motion, exact typography/palette, dark mode, and a clean
console. Deployment and a paid provider search were intentionally not performed;
the deterministic SSE fixture covers the approval interrupt without incurring
external work.
