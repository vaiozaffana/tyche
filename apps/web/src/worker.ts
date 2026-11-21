import {
  chat,
  chatParamsFromRequest,
  maxIterations,
  toServerSentEventsResponse,
  type AnyTextAdapter,
} from "@tanstack/ai";
import { createGeminiChat } from "@tanstack/ai-gemini";
import { serverTools } from "./agent/server-tools";

interface WorkerEnv {
  ASSETS: { fetch(request: Request): Promise<Response> };
  GEMINI_API_KEY?: string;
}

const SYSTEM_PROMPT = `You are Tyche, an agent that helps authenticated users operate a job-search product.
Use inspect_search_brief before proposing a search. Use create_job_search only after the user reviews
the exact prompt; the tool itself requires approval. Never invent search status, results, salary, or URLs.
Use get_job_search and list_job_searches for persisted state. Paid provider calls and ranking belong to
the backend job-search pipeline, not to you. Respond in the user's language. Keep prose concise because
tool-specific UI renders the structured details.`;

type AdapterFactory = (
  model: Parameters<typeof createGeminiChat>[0],
  apiKey: string,
) => AnyTextAdapter;

export function createAgentWorker(createAdapter: AdapterFactory = createGeminiChat) {
  return {
    async fetch(request: Request, env: WorkerEnv): Promise<Response> {
      const url = new URL(request.url);
      if (url.pathname !== "/api/chat") return env.ASSETS.fetch(request);
      if (request.method !== "POST") {
        return Response.json({ error: "method_not_allowed" }, { status: 405 });
      }
      if (!env.GEMINI_API_KEY) {
        return Response.json({ error: "agent_unavailable" }, { status: 503 });
      }

      try {
        const abortController = new AbortController();
        const params = await chatParamsFromRequest(request);
        const stream = chat({
          abortController,
          adapter: createAdapter("gemini-3.8-flash", env.GEMINI_API_KEY),
          agentLoopStrategy: maxIterations(6),
          messages: params.messages,
          reasoning: "low",
          runId: params.runId,
          systemPrompts: [SYSTEM_PROMPT],
          threadId: params.threadId,
          tools: serverTools,
        });
        return toServerSentEventsResponse(stream, {
          abortController,
          headers: { "Cache-Control": "no-cache, no-store" },
        });
      } catch (error) {
        if (error instanceof Response) return error;
        return Response.json({ error: "agent_unavailable" }, { status: 502 });
      }
    },
  };
}

export default createAgentWorker();
