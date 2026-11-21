import type { ToolCallPart } from "@tanstack/ai";
import { fetchServerSentEvents, useChat } from "@tanstack/ai-react";
import {
  jobSearchCreatedSchema,
  jobSearchDetailSchema,
  jobSearchListSchema,
} from "@repo/contracts/job-search";
import {
  Conversation,
  ConversationContent,
  ConversationEmptyState,
  ConversationScrollButton,
} from "@repo/ui/components/ai-elements/conversation";
import {
  Message,
  MessageContent,
  MessageMeta,
  MessageResponse,
} from "@repo/ui/components/ai-elements/message";
import {
  PromptInput,
  PromptInputFooter,
  PromptInputHint,
  PromptInputSubmit,
  PromptInputTextarea,
  submitPrompt,
} from "@repo/ui/components/ai-elements/prompt-input";
import {
  Reasoning,
  ReasoningContent,
  ReasoningTrigger,
} from "@repo/ui/components/ai-elements/reasoning";
import {
  Tool,
  ToolContent,
  ToolHeader,
  ToolSection,
  type ToolStatus,
} from "@repo/ui/components/ai-elements/tool";
import { Badge } from "@repo/ui/components/badge";
import { Button } from "@repo/ui/components/button";
import { toast } from "@repo/ui/components/sonner";
import {
  useAsyncQueuer,
  useAsyncRateLimiter,
  useBatcher,
  useThrottler,
} from "@tanstack/react-pacer";
import {
  BotIcon,
  CheckIcon,
  CircleAlertIcon,
  Clock3Icon,
  ExternalLinkIcon,
  ShieldCheckIcon,
  XIcon,
} from "lucide-react";
import { useMemo, useState } from "react";
import { createClientTools } from "../../../agent/client-tools";
import { getOpenPostingMessage } from "../../../agent/tools";
import { jobSearchDetailQueryOptions, jobSearchKeys } from "../hooks/use-job-search";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { StatusBadge } from "./search-results";

const agentConnection = fetchServerSentEvents("/api/chat");
const suggestions = [
  "Cari React developer remote dengan TypeScript dan 3 tahun pengalaman",
  "Tampilkan pencarian saya yang terbaru",
  "Jelaskan bagaimana Tyche menilai kecocokan pekerjaan",
];

export function AgentWorkspace() {
  const [draft, setDraft] = useState("");
  const [visibleLength, setVisibleLength] = useState(0);
  const [threadId] = useState(() => crypto.randomUUID());
  const queryClient = useQueryClient();
  const searchInvalidations = useBatcher(
    () => void queryClient.invalidateQueries({ queryKey: jobSearchKeys.all }),
    { maxSize: 5, wait: 100 },
  );
  const clientTools = useMemo(
    () => createClientTools(() => searchInvalidations.addItem("searches")),
    [searchInvalidations],
  );
  const chat = useChat({
    connection: agentConnection,
    threadId,
    tools: clientTools,
  });
  const draftTelemetry = useThrottler(setVisibleLength, {
    leading: true,
    trailing: true,
    wait: 120,
  });
  const sendLimiter = useAsyncRateLimiter((prompt: string) => chat.sendMessage(prompt), {
    limit: 6,
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Agent request failed."),
    onReject: () => toast.error("Please wait before sending another agent request."),
    window: 60_000,
  });
  const sendQueue = useAsyncQueuer(
    async (prompt: string) => {
      await sendLimiter.maybeExecute(prompt);
    },
    {
      concurrency: 1,
      maxSize: 8,
      onError: (error) =>
        toast.error(error instanceof Error ? error.message : "Queued request failed."),
      started: true,
    },
    (state) => ({ size: state.size }),
  );

  function enqueue(prompt: string) {
    sendQueue.addItem(prompt);
    // StrictMode runs the hook cleanup once during development, which stops the queue.
    sendQueue.start();
    setDraft("");
    setVisibleLength(0);
  }

  return (
    <section
      aria-labelledby="agent-heading"
      className="grid min-h-[620px] grid-rows-[auto_1fr_auto] border border-foreground bg-card shadow-[6px_6px_0_#111111] dark:shadow-[6px_6px_0_#ff4b23]"
    >
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-foreground px-4 py-3">
        <div className="flex items-center gap-3">
          <span className="grid size-9 place-content-center bg-primary text-primary-foreground">
            <BotIcon className="size-4" />
          </span>
          <div>
            <h2 className="font-display text-lg font-semibold leading-none" id="agent-heading">
              Tyche agent
            </h2>
            <p className="mt-1 font-mono text-[9px] uppercase tracking-[0.16em] text-muted-foreground">
              Brief · approve · search · inspect
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="size-1.5 bg-emerald-500" aria-hidden="true" />
          <span className="font-mono text-[10px] text-muted-foreground">
            {chat.isLoading ? "Working" : chat.resuming ? "Resuming" : "Ready"}
          </span>
        </div>
      </header>

      <Conversation>
        <ConversationContent className="min-h-full p-4 sm:p-5">
          {chat.messages.length === 0 ? (
            <div className="grid min-h-full content-center gap-6 py-10">
              <ConversationEmptyState
                description="Describe the role, location, and skills. The agent will validate your brief and ask before starting a search run."
                title="Turn intent into a ranked shortlist."
              />
              <div className="mx-auto grid w-full max-w-xl gap-2">
                {suggestions.map((suggestion) => (
                  <button
                    className="border bg-background px-3 py-2 text-left text-sm transition-colors hover:border-primary hover:text-primary"
                    key={suggestion}
                    onClick={() => enqueue(suggestion)}
                    type="button"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          {chat.messages.map((message) => (
            <Message from={message.role} key={message.id}>
              <MessageContent>
                {message.parts.map((part, index) => {
                  if (part.type === "text") {
                    return <MessageResponse key={index}>{part.content}</MessageResponse>;
                  }
                  if (part.type === "thinking" && part.content) {
                    return (
                      <Reasoning isStreaming={chat.isLoading} key={index}>
                        <ReasoningTrigger />
                        <ReasoningContent>{part.content}</ReasoningContent>
                      </Reasoning>
                    );
                  }
                  if (part.type === "tool-call") {
                    return <ToolCallCard key={part.id} part={part} />;
                  }
                  return null;
                })}
              </MessageContent>
              <MessageMeta>{message.role === "user" ? "YOU" : "TYCHE"}</MessageMeta>
            </Message>
          ))}

          {chat.interrupts.map((interrupt) =>
            interrupt.kind === "tool-approval" ? (
              <ApprovalCard
                disabled={!interrupt.canResolve || chat.resuming}
                interrupt={interrupt}
                key={interrupt.id}
              />
            ) : null,
          )}

          {chat.error ? (
            <div className="flex gap-3 border border-destructive bg-destructive/10 p-3 text-sm text-destructive">
              <CircleAlertIcon className="mt-0.5 size-4 shrink-0" />
              <div>
                <p className="font-medium">The agent is unavailable.</p>
                <p className="mt-1 opacity-80">{chat.error.message}</p>
              </div>
            </div>
          ) : null}
        </ConversationContent>
        <ConversationScrollButton />
      </Conversation>

      <div className="border-t border-foreground bg-background p-3 sm:p-4">
        <PromptInput onSubmit={(event) => submitPrompt(event, draft, enqueue)}>
          <PromptInputTextarea
            aria-label="Message the Tyche agent"
            maxLength={1_000}
            onChange={(event) => {
              setDraft(event.target.value);
              draftTelemetry.maybeExecute(event.target.value.length);
            }}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                const prompt = draft.trim();
                if (prompt) enqueue(prompt);
              }
            }}
            placeholder="Example: Data analyst in Jakarta, strong SQL and Python, hybrid preferred..."
            value={draft}
          />
          <PromptInputFooter>
            <PromptInputHint>
              {sendQueue.state.size > 0 ? `${sendQueue.state.size} queued · ` : ""}
              {visibleLength}/1000 · Enter to send
            </PromptInputHint>
            <PromptInputSubmit
              disabled={!draft.trim() && !chat.isLoading}
              isStreaming={chat.isLoading}
              onStop={chat.stop}
            />
          </PromptInputFooter>
        </PromptInput>
      </div>
    </section>
  );
}

function ApprovalCard({
  disabled,
  interrupt,
}: {
  disabled: boolean;
  interrupt: {
    id: string;
    originalArgs: unknown;
    resolveInterrupt: (approved: boolean) => void;
    toolName: string;
  };
}) {
  const args = asRecord(interrupt.originalArgs);
  const creating = interrupt.toolName === "create_job_search";
  const label = creating ? "Start this search run?" : "Open this external posting?";
  const detail = creating ? readString(args, "prompt") : readString(args, "url");

  return (
    <Message from="activity">
      <div className="w-full border-2 border-primary bg-primary/5 p-4">
        <div className="flex gap-3">
          <ShieldCheckIcon className="mt-0.5 size-5 shrink-0 text-primary" />
          <div className="min-w-0 flex-1">
            <p className="font-display text-lg font-semibold">{label}</p>
            <p className="mt-2 break-words text-sm leading-6 text-muted-foreground">{detail}</p>
            <p className="mt-3 font-mono text-[10px] text-muted-foreground">
              {creating
                ? "This can use paid search and page-reading providers."
                : "This leaves Tyche in a new tab."}
            </p>
            <div className="mt-4 flex gap-2">
              <Button
                disabled={disabled}
                onClick={() => interrupt.resolveInterrupt(true)}
                size="sm"
                type="button"
              >
                <CheckIcon className="size-3.5" /> Approve
              </Button>
              <Button
                disabled={disabled}
                onClick={() => interrupt.resolveInterrupt(false)}
                size="sm"
                type="button"
                variant="outline"
              >
                <XIcon className="size-3.5" /> Deny
              </Button>
            </div>
          </div>
        </div>
      </div>
    </Message>
  );
}

function ToolCallCard({ part }: { part: ToolCallPart }) {
  const status = part.state as ToolStatus;
  return (
    <Tool
      defaultOpen={
        part.state === "complete" || part.state === "error" || part.state === "approval-requested"
      }
    >
      <ToolHeader name={formatToolName(part.name)} status={status} />
      <ToolContent>
        <ToolOutput name={part.name} output={part.output} />
      </ToolContent>
    </Tool>
  );
}

function ToolOutput({ name, output }: { name: string; output: unknown }) {
  if (output === undefined) {
    return (
      <p className="border-t pt-3 text-sm text-muted-foreground">Waiting for the tool to finish.</p>
    );
  }

  if (name === "create_job_search") {
    const parsed = jobSearchCreatedSchema.safeParse(output);
    return parsed.success ? <LiveRun searchId={parsed.data.id} /> : <ToolFailure />;
  }
  if (name === "get_job_search") {
    const parsed = jobSearchDetailSchema.safeParse(output);
    return parsed.success ? (
      <ToolSection label="Latest state">
        <div className="flex items-center justify-between gap-4">
          <span className="line-clamp-2">{parsed.data.prompt}</span>
          <StatusBadge status={parsed.data.status} />
        </div>
        <p className="mt-2 font-mono text-[10px] text-muted-foreground">
          {parsed.data.results.length} ranked matches
        </p>
      </ToolSection>
    ) : (
      <ToolFailure />
    );
  }
  if (name === "list_job_searches") {
    const parsed = jobSearchListSchema.safeParse(output);
    return parsed.success ? (
      <ToolSection label="Recent searches">
        <div className="grid gap-2">
          {parsed.data.searches.slice(0, 5).map((search) => (
            <div className="flex items-center justify-between gap-4" key={search.id}>
              <span className="line-clamp-1">{search.prompt}</span>
              <StatusBadge status={search.status} />
            </div>
          ))}
        </div>
      </ToolSection>
    ) : (
      <ToolFailure />
    );
  }
  if (name === "inspect_search_brief") {
    const value = asRecord(output);
    const missing = Array.isArray(value.missing)
      ? value.missing.filter((item): item is string => typeof item === "string")
      : [];
    return (
      <ToolSection label="Brief check">
        <p>{readString(value, "summary")}</p>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {missing.length === 0 ? (
            <Badge variant="secondary">Ready to review</Badge>
          ) : (
            missing.map((item) => (
              <Badge key={item} variant="outline">
                Add {item}
              </Badge>
            ))
          )}
        </div>
      </ToolSection>
    );
  }
  if (name === "explain_search_pipeline") {
    const value = asRecord(output);
    const stages = Array.isArray(value.stages) ? value.stages : [];
    return (
      <ToolSection label="Pipeline">
        <ol className="grid gap-2">
          {stages.map((stage, index) => {
            const item = asRecord(stage);
            return (
              <li className="grid grid-cols-[20px_1fr] gap-2" key={index}>
                <span className="font-mono text-primary">{index + 1}</span>
                <span>
                  <strong>{readString(item, "name")}</strong> · {readString(item, "purpose")}
                </span>
              </li>
            );
          })}
        </ol>
      </ToolSection>
    );
  }
  if (name === "open_job_posting") {
    const opened = asRecord(output).opened === true;
    return (
      <ToolSection label="Browser">
        <p className="flex items-center gap-2">
          <ExternalLinkIcon className="size-4 text-primary" /> {getOpenPostingMessage(opened)}
        </p>
      </ToolSection>
    );
  }
  return (
    <ToolSection label="Result">
      <p>Tool completed.</p>
    </ToolSection>
  );
}

function LiveRun({ searchId }: { searchId: string }) {
  const search = useQuery(jobSearchDetailQueryOptions(searchId));
  if (!search.data)
    return (
      <ToolSection label="Search run">
        <p className="flex items-center gap-2 text-muted-foreground">
          <Clock3Icon className="size-4" /> Loading persisted status...
        </p>
      </ToolSection>
    );
  return (
    <ToolSection label="Search run">
      <div className="flex items-center justify-between gap-4">
        <span className="line-clamp-2">{search.data.prompt}</span>
        <StatusBadge status={search.data.status} />
      </div>
      <p className="mt-2 font-mono text-[10px] text-muted-foreground">
        {search.data.results.length} results · {search.data.stats.firecrawlCalls} page reads
      </p>
    </ToolSection>
  );
}

function ToolFailure() {
  return (
    <ToolSection label="Result">
      <p className="text-destructive">The tool returned an unexpected response.</p>
    </ToolSection>
  );
}

function formatToolName(name: string) {
  return name
    .split("_")
    .map((part) => part[0]?.toUpperCase() + part.slice(1))
    .join(" ");
}

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

function readString(value: Record<string, unknown>, key: string) {
  return typeof value[key] === "string" ? value[key] : "";
}
