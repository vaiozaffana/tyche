import { describe, expect, it } from "vitest";
import { getAgentFeedback, getFriendlyAgentError } from "./agent-feedback";

describe("agent feedback", () => {
  it("makes a slow first response explicit before the timeout", () => {
    expect(
      getAgentFeedback({
        chatStatus: "submitted",
        elapsedMs: 31_000,
        hasInterrupt: false,
        resuming: false,
        runState: { kind: "active" },
      }),
    ).toMatchObject({ active: true, label: "Delayed", title: "Taking longer than usual" });
  });

  it("puts approval ahead of a completed interrupt response", () => {
    expect(
      getAgentFeedback({
        chatStatus: "ready",
        elapsedMs: 0,
        hasInterrupt: true,
        resuming: false,
        runState: { kind: "complete" },
      }),
    ).toMatchObject({ kind: "approval", label: "Approval needed" });
  });

  it("offers retry after a timeout or failure", () => {
    for (const runState of [
      { kind: "timed-out" as const },
      { kind: "error" as const, message: "Safe failure" },
    ]) {
      expect(
        getAgentFeedback({
          chatStatus: "ready",
          elapsedMs: 75_000,
          hasInterrupt: false,
          resuming: false,
          runState,
        }).canRetry,
      ).toBe(true);
    }
  });

  it("confirms a completed request", () => {
    expect(
      getAgentFeedback({
        chatStatus: "ready",
        elapsedMs: 4_000,
        hasInterrupt: false,
        resuming: false,
        runState: { kind: "complete" },
      }),
    ).toMatchObject({ kind: "complete", label: "Complete", title: "Request completed" });
  });

  it("turns transport errors into actionable messages without exposing internals", () => {
    expect(getFriendlyAgentError(new Error("HTTP 429: provider quota exceeded"))).toBe(
      "The model provider is temporarily busy or unavailable. Wait a moment, then retry.",
    );
    expect(getFriendlyAgentError(new Error("HTTP 503 high demand"))).toContain("temporarily busy");
    expect(getFriendlyAgentError(new Error("503 agent_unavailable"))).toContain("not configured");
    expect(getFriendlyAgentError(new Error("secret provider trace"))).not.toContain("secret");
  });
});
