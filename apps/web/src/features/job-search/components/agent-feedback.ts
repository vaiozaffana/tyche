export const AGENT_RESPONSE_TIMEOUT_MS = 75_000;

export type AgentRunState =
  | { kind: "idle" }
  | { kind: "queued" }
  | { kind: "active" }
  | { kind: "complete" }
  | { kind: "cancelled" }
  | { kind: "timed-out" }
  | { kind: "error"; message: string };

export type AgentFeedback = {
  kind: AgentRunState["kind"] | "approval" | "submitted" | "streaming" | "resuming";
  label: string;
  title: string;
  description: string;
  active: boolean;
  canRetry: boolean;
};

export function getAgentFeedback({
  chatStatus,
  elapsedMs,
  hasInterrupt,
  resuming,
  runState,
}: {
  chatStatus: "ready" | "submitted" | "streaming" | "error";
  elapsedMs: number;
  hasInterrupt: boolean;
  resuming: boolean;
  runState: AgentRunState;
}): AgentFeedback {
  if (resuming) {
    return feedback(
      "resuming",
      "Resuming",
      "Decision received",
      "Tyche is continuing from your approval decision.",
      true,
    );
  }
  if (hasInterrupt) {
    return feedback(
      "approval",
      "Approval needed",
      "Waiting for your decision",
      "Review the action below. Nothing requiring approval will run until you choose.",
      false,
    );
  }
  if (chatStatus === "submitted") {
    if (elapsedMs >= 30_000) {
      return feedback(
        "submitted",
        "Delayed",
        "Taking longer than usual",
        "The model has not sent its first response yet. Tyche will stop automatically after 75 seconds.",
        true,
      );
    }
    if (elapsedMs >= 10_000) {
      return feedback(
        "submitted",
        "Thinking",
        "Still preparing a response",
        "The model has not started responding yet. You can keep waiting or stop this request.",
        true,
      );
    }
    return feedback(
      "submitted",
      "Sending",
      "Request received",
      "Tyche is preparing the first response.",
      true,
    );
  }
  if (chatStatus === "streaming") {
    return feedback(
      "streaming",
      "Responding",
      "Response in progress",
      "Response data is arriving. Tool steps and approvals will appear here as they happen.",
      true,
    );
  }

  switch (runState.kind) {
    case "queued":
      return feedback(
        "queued",
        "Queued",
        "Message queued",
        "Your message will be sent as soon as the current request is ready.",
        true,
      );
    case "active":
      return feedback(
        "active",
        "Connecting",
        "Opening a secure connection",
        "Tyche is sending your request to the model.",
        true,
      );
    case "complete":
      return feedback(
        "complete",
        "Complete",
        "Request completed",
        "Tyche finished this request. Any result or next action is shown above.",
        false,
      );
    case "cancelled":
      return feedback(
        "cancelled",
        "Stopped",
        "Request stopped",
        "You stopped this response. Any search you already approved may continue in Search operations.",
        false,
        true,
      );
    case "timed-out":
      return feedback(
        "timed-out",
        "Timed out",
        "The agent did not finish in time",
        "Tyche stopped waiting after 75 seconds. You can retry the last request safely.",
        false,
        true,
      );
    case "error":
      return feedback("error", "Error", "Request failed", runState.message, false, true);
    case "idle":
      return feedback("idle", "Ready", "Ready", "", false);
  }
}

export function getFriendlyAgentError(error: unknown) {
  const message =
    error instanceof Error ? error.message.toLowerCase() : String(error).toLowerCase();
  if (message.includes("agent_unavailable")) {
    return "The agent service is not configured right now. Try again after an administrator enables it.";
  }
  if (
    message.includes("429") ||
    message.includes("503") ||
    message.includes("rate limit") ||
    message.includes("quota") ||
    message.includes("high demand") ||
    message.includes("service unavailable")
  ) {
    return "The model provider is temporarily busy or unavailable. Wait a moment, then retry.";
  }
  if (message.includes("network") || message.includes("fetch") || message.includes("connection")) {
    return "The connection to Tyche was interrupted. Check your connection, then retry.";
  }
  if (
    message.includes("401") ||
    message.includes("403") ||
    message.includes("unauthorized") ||
    message.includes("forbidden")
  ) {
    return "Tyche could not authenticate with the model provider. An administrator needs to check the agent configuration.";
  }
  return "Tyche could not complete this request. Any search you already approved may still continue in Search operations.";
}

function feedback(
  kind: AgentFeedback["kind"],
  label: string,
  title: string,
  description: string,
  active: boolean,
  canRetry = false,
): AgentFeedback {
  return { active, canRetry, description, kind, label, title };
}
