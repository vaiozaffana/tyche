import { UnauthorizedApiError } from "@repo/api-client";
import { Badge } from "@repo/ui/components/badge";
import { useQuery } from "@tanstack/react-query";
import { createFileRoute, redirect } from "@tanstack/react-router";
import { SparklesIcon } from "lucide-react";
import { AppShell } from "../features/app-shell/app-shell";
import { meQueryOptions } from "../features/auth/hooks/use-auth";
import { AgentWorkspace } from "../features/job-search/components/agent-workspace";
import { SearchOperations } from "../features/job-search/components/search-results";

export const Route = createFileRoute("/")({
  beforeLoad: async ({ context }) => {
    try {
      await context.queryClient.ensureQueryData(meQueryOptions);
    } catch (error) {
      if (error instanceof UnauthorizedApiError) throw redirect({ to: "/login" });
      throw error;
    }
  },
  component: JobSearchPage,
});

function JobSearchPage() {
  const user = useQuery(meQueryOptions);
  if (!user.data) return null;

  return (
    <AppShell>
      <div className="grid gap-6">
        <header className="grid gap-4 border-b-2 border-foreground pb-5 lg:grid-cols-[1fr_auto] lg:items-end">
          <div>
            <div className="mb-3 flex items-center gap-2">
              <SparklesIcon className="size-4 text-primary" />
              <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-primary">
                Agent-led job intelligence
              </span>
            </div>
            <h1 className="max-w-4xl font-display text-4xl font-semibold leading-[0.95] tracking-[-0.04em] sm:text-5xl lg:text-6xl">
              Search less. Inspect the <span className="text-primary">right work.</span>
            </h1>
            <p className="mt-4 max-w-2xl text-sm leading-6 text-muted-foreground sm:text-base">
              Turn a natural-language brief into a transparent, ranked shortlist. Tyche validates
              intent, asks permission, and keeps every run inspectable.
            </p>
          </div>
          <div className="flex flex-wrap gap-2 lg:max-w-64 lg:justify-end">
            <Badge className="rounded-sm font-mono text-[10px]" variant="outline">
              Human approval
            </Badge>
            <Badge className="rounded-sm font-mono text-[10px]" variant="outline">
              Persisted runs
            </Badge>
            <Badge className="rounded-sm font-mono text-[10px]" variant="outline">
              Ranked evidence
            </Badge>
          </div>
        </header>

        <div className="grid gap-8 xl:grid-cols-[minmax(420px,0.85fr)_minmax(0,1.15fr)]">
          <AgentWorkspace />
          <SearchOperations />
        </div>
      </div>
    </AppShell>
  );
}
