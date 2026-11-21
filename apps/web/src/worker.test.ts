import { fakeText } from "@tanstack/ai/testing";
import { describe, expect, it, vi } from "vitest";
import worker, { createAgentWorker } from "./worker";

const assets = { fetch: vi.fn(() => Promise.resolve(new Response("asset"))) };

describe("agent worker route", () => {
  it("delegates non-agent requests to static assets", async () => {
    await expect(
      worker.fetch(new Request("https://tyche.test/profile"), { ASSETS: assets }),
    ).resolves.toHaveProperty("status", 200);
    expect(assets.fetch).toHaveBeenCalledOnce();
  });

  it("rejects unsupported methods and missing server credentials safely", async () => {
    const methodResponse = await worker.fetch(new Request("https://tyche.test/api/chat"), {
      ASSETS: assets,
    });
    expect(methodResponse.status).toBe(405);
    await expect(methodResponse.json()).resolves.toEqual({ error: "method_not_allowed" });

    const unavailableResponse = await worker.fetch(
      new Request("https://tyche.test/api/chat", { method: "POST" }),
      { ASSETS: assets },
    );
    expect(unavailableResponse.status).toBe(503);
    await expect(unavailableResponse.json()).resolves.toEqual({ error: "agent_unavailable" });
  });

  it("rejects malformed AG-UI input and streams a deterministic SSE response", async () => {
    const fake = fakeText();
    fake.setResponses([{ text: "Hello from Tyche." }]);
    const testWorker = createAgentWorker(() => fake);
    const invalidResponse = await testWorker.fetch(
      new Request("https://tyche.test/api/chat", { method: "POST", body: "{" }),
      { ASSETS: assets, GEMINI_API_KEY: "test-key" },
    );
    expect(invalidResponse.status).toBe(400);

    const response = await testWorker.fetch(
      new Request("https://tyche.test/api/chat", {
        body: JSON.stringify({
          context: [],
          forwardedProps: {},
          messages: [{ content: "Say hello", id: "message-1", role: "user" }],
          runId: "run-1",
          state: {},
          threadId: "thread-1",
          tools: [],
        }),
        headers: { "Content-Type": "application/json" },
        method: "POST",
      }),
      { ASSETS: assets, GEMINI_API_KEY: "test-key" },
    );

    expect(response.status).toBe(200);
    expect(response.headers.get("Content-Type")).toContain("text/event-stream");
    expect(response.headers.get("Cache-Control")).toBe("no-cache, no-store");
    const body = await response.text();
    expect(body).toContain("RUN_STARTED");
    const events = body
      .split("\n")
      .filter((line) => line.startsWith("data: "))
      .map((line) => JSON.parse(line.slice(6)) as { delta?: string; type: string });
    expect(
      events
        .filter((event) => event.type === "TEXT_MESSAGE_CONTENT")
        .map((event) => event.delta)
        .join(""),
    ).toBe("Hello from Tyche.");
    expect(events.at(-1)?.type).toBe("RUN_FINISHED");
  });

  it("streams an approval-gated client tool call without executing it", async () => {
    const fake = fakeText();
    fake.setResponses([
      {
        toolCalls: [
          {
            input: { prompt: "React developer remote with TypeScript" },
            name: "create_job_search",
          },
        ],
      },
    ]);
    const response = await createAgentWorker(() => fake).fetch(
      new Request("https://tyche.test/api/chat", {
        body: JSON.stringify({
          context: [],
          forwardedProps: {},
          messages: [{ content: "Find React jobs", id: "message-1", role: "user" }],
          runId: "run-approval",
          state: {},
          threadId: "thread-1",
          tools: [],
        }),
        headers: { "Content-Type": "application/json" },
        method: "POST",
      }),
      { ASSETS: assets, GEMINI_API_KEY: "test-key" },
    );

    const body = await response.text();
    expect(response.status).toBe(200);
    expect(body).toContain("TOOL_CALL_START");
    expect(body).toContain("create_job_search");
    const lastEvent = body
      .split("\n")
      .filter((line) => line.startsWith("data: "))
      .map((line) => JSON.parse(line.slice(6)) as unknown)
      .at(-1);
    expect(lastEvent).toMatchObject({
      outcome: {
        interrupts: [{ metadata: { kind: "approval", toolName: "create_job_search" } }],
        type: "interrupt",
      },
      type: "RUN_FINISHED",
    });
  });
});
