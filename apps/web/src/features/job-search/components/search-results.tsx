import type {
  JobSearchDetail,
  JobSearchResult,
  JobSearchStatus,
  JobSearchSummary,
} from "@repo/contracts/job-search";
import { Badge } from "@repo/ui/components/badge";
import { Button } from "@repo/ui/components/button";
import { Progress } from "@repo/ui/components/progress";
import { Skeleton } from "@repo/ui/components/skeleton";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowUpRightIcon,
  BriefcaseBusinessIcon,
  Building2Icon,
  CircleAlertIcon,
  Clock3Icon,
  MapPinIcon,
  RadarIcon,
} from "lucide-react";
import { useEffect, useState } from "react";
import {
  jobSearchDetailQueryOptions,
  jobSearchKeys,
  jobSearchListQueryOptions,
} from "../hooks/use-job-search";

export function SearchOperations() {
  const searches = useQuery(jobSearchListQueryOptions);
  const [selectedId, setSelectedId] = useState<string>();
  const activeId = selectedId ?? searches.data?.[0]?.id;

  return (
    <section
      aria-labelledby="operations-heading"
      className="grid min-h-0 gap-4 lg:grid-rows-[auto_1fr]"
    >
      <div className="flex items-end justify-between gap-4 border-b border-foreground pb-3">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-primary">
            Persisted state
          </p>
          <h2
            className="font-display text-2xl font-semibold tracking-tight"
            id="operations-heading"
          >
            Search operations
          </h2>
        </div>
        <Badge className="rounded-sm font-mono text-[10px]" variant="outline">
          {searches.data?.length ?? 0} runs
        </Badge>
      </div>

      <div className="grid min-h-0 gap-4 xl:grid-cols-[280px_minmax(0,1fr)]">
        <SearchHistory
          activeId={activeId}
          isLoading={searches.isLoading}
          onSelect={setSelectedId}
          searches={searches.data ?? []}
        />
        {activeId ? (
          <SearchDetail searchId={activeId} />
        ) : (
          <div className="grid min-h-72 place-content-center border border-dashed bg-background/70 p-8 text-center">
            <BriefcaseBusinessIcon className="mx-auto mb-4 size-8 text-primary" />
            <p className="font-display text-xl font-semibold">No search runs yet</p>
            <p className="mt-1 max-w-sm text-sm leading-6 text-muted-foreground">
              Tell the agent what role you want. It will review the brief before asking permission
              to start.
            </p>
          </div>
        )}
      </div>
    </section>
  );
}

function SearchHistory({
  activeId,
  isLoading,
  onSelect,
  searches,
}: {
  activeId?: string;
  isLoading: boolean;
  onSelect: (id: string) => void;
  searches: Array<{ createdAt: string; id: string; prompt: string; status: JobSearchStatus }>;
}) {
  if (isLoading) {
    return (
      <div className="grid content-start gap-2">
        <Skeleton className="h-20" />
        <Skeleton className="h-20" />
        <Skeleton className="h-20" />
      </div>
    );
  }

  return (
    <div aria-label="Recent searches" className="grid content-start gap-2" role="list">
      {searches.map((search, index) => (
        <button
          aria-pressed={activeId === search.id}
          className="group grid gap-2 border p-3 text-left transition-colors hover:border-foreground data-[active=true]:border-foreground data-[active=true]:bg-foreground data-[active=true]:text-background"
          data-active={activeId === search.id}
          key={search.id}
          onClick={() => onSelect(search.id)}
          role="listitem"
          type="button"
        >
          <div className="flex items-center justify-between gap-3">
            <span className="font-mono text-[10px] opacity-60">
              RUN {String(index + 1).padStart(2, "0")}
            </span>
            <StatusBadge status={search.status} />
          </div>
          <span className="line-clamp-2 text-sm font-medium leading-5">{search.prompt}</span>
          <time className="font-mono text-[10px] opacity-60">{formatDate(search.createdAt)}</time>
        </button>
      ))}
    </div>
  );
}

function SearchDetail({ searchId }: { searchId: string }) {
  const search = useQuery(jobSearchDetailQueryOptions(searchId));
  const queryClient = useQueryClient();

  useEffect(() => {
    const data = search.data;
    if (!data) return;
    queryClient.setQueryData<Array<JobSearchSummary>>(jobSearchKeys.all, (current) =>
      current?.map((item) =>
        item.id === data.id
          ? { ...item, completedAt: data.completedAt, status: data.status }
          : item,
      ),
    );
  }, [queryClient, search.data]);

  if (search.isLoading || !search.data) {
    return (
      <div className="grid content-start gap-3">
        <Skeleton className="h-32" />
        <Skeleton className="h-52" />
      </div>
    );
  }

  return <SearchDetailContent search={search.data} />;
}

export function SearchDetailContent({ search }: { search: JobSearchDetail }) {
  const complete = search.status === "completed";
  const active = search.status === "queued" || search.status === "running";

  return (
    <div className="grid content-start gap-4">
      <div className="border bg-card p-4 shadow-[4px_4px_0_color-mix(in_srgb,var(--foreground)_14%,transparent)]">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-2xl">
            <div className="mb-2 flex items-center gap-2">
              <StatusBadge status={search.status} />
              <span className="font-mono text-[10px] text-muted-foreground">
                {search.id.slice(0, 10)}
              </span>
            </div>
            <h3 className="font-display text-xl font-semibold leading-tight">{search.prompt}</h3>
          </div>
          <div className="grid grid-cols-3 gap-4 text-right">
            <Metric label="found" value={search.results.length} />
            <Metric label="serp" value={search.stats.serpCalls} />
            <Metric label="reads" value={search.stats.firecrawlCalls} />
          </div>
        </div>
        {active ? (
          <div className="mt-4 grid gap-2">
            <Progress className="h-1" value={search.status === "queued" ? 18 : 62} />
            <p className="flex items-center gap-2 font-mono text-[10px] text-muted-foreground">
              <RadarIcon className="size-3 animate-pulse text-primary" />
              {search.status === "queued"
                ? "Waiting for a worker"
                : "Discovering and assessing matches"}
            </p>
          </div>
        ) : null}
        {search.status === "failed" ? (
          <p className="mt-4 flex gap-2 border-l-2 border-destructive bg-destructive/10 p-3 text-sm text-destructive">
            <CircleAlertIcon className="mt-0.5 size-4 shrink-0" />
            {search.errorMessage ?? "The search could not be completed."}
          </p>
        ) : null}
      </div>

      {complete && search.results.length === 0 ? (
        <div className="border border-dashed p-8 text-center text-sm text-muted-foreground">
          The run completed without a strong match. Refine the role, location, or skills and try
          again.
        </div>
      ) : null}

      <div className="grid gap-3 2xl:grid-cols-2">
        {search.results.map((result) => (
          <JobResultCard
            key={`${result.rank}-${result.sourceUrl ?? result.title}`}
            result={result}
          />
        ))}
      </div>
    </div>
  );
}

function JobResultCard({ result }: { result: JobSearchResult }) {
  return (
    <article className="group grid gap-4 border bg-card p-4 transition-transform hover:-translate-y-0.5">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="font-mono text-[10px] text-primary">
            MATCH {String(result.rank).padStart(2, "0")}
          </p>
          <h4 className="mt-1 font-display text-xl font-semibold leading-tight">{result.title}</h4>
        </div>
        {result.fitScore !== null ? (
          <div className="grid size-12 shrink-0 place-content-center border border-foreground bg-secondary font-mono text-sm font-semibold">
            {result.fitScore}
          </div>
        ) : null}
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-2 text-xs text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <Building2Icon className="size-3.5" />
          {result.company}
        </span>
        <span className="flex items-center gap-1.5">
          <MapPinIcon className="size-3.5" />
          {result.location}
        </span>
        {result.postedAt ? (
          <span className="flex items-center gap-1.5">
            <Clock3Icon className="size-3.5" />
            {result.postedAt}
          </span>
        ) : null}
      </div>
      {result.fitReason ? (
        <p className="text-sm leading-6 text-muted-foreground">{result.fitReason}</p>
      ) : null}
      <div className="flex flex-wrap gap-1.5">
        {result.techStack.slice(0, 6).map((technology) => (
          <Badge className="rounded-sm font-mono text-[10px]" key={technology} variant="secondary">
            {technology}
          </Badge>
        ))}
      </div>
      <div className="flex items-center justify-between gap-4 border-t pt-3">
        <span className="font-mono text-[10px] text-muted-foreground">{formatSalary(result)}</span>
        {result.sourceUrl ? (
          <Button asChild size="sm" variant="outline">
            <a href={result.sourceUrl} rel="noreferrer" target="_blank">
              View posting <ArrowUpRightIcon className="size-3.5" />
            </a>
          </Button>
        ) : null}
      </div>
    </article>
  );
}

export function StatusBadge({ status }: { status: JobSearchStatus }) {
  const label = status === "completed" ? "Complete" : status[0]?.toUpperCase() + status.slice(1);
  return (
    <Badge
      className="rounded-sm font-mono text-[9px] uppercase tracking-wide data-[status=failed]:border-destructive data-[status=failed]:text-destructive data-[status=running]:border-primary data-[status=running]:text-primary"
      data-status={status}
      variant="outline"
    >
      {label}
    </Badge>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <p className="font-display text-xl font-semibold">{value}</p>
      <p className="font-mono text-[9px] uppercase text-muted-foreground">{label}</p>
    </div>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(new Date(value));
}

export function formatSalary(result: JobSearchResult) {
  const salary = result.salary;
  if (!salary) return result.sourceSite ?? "Source not reported";
  if (salary.raw) return salary.raw;
  if (salary.min === null && salary.max === null) return result.sourceSite ?? "Salary not reported";
  const currency = salary.currency ?? "";
  const range = [salary.min, salary.max].filter((value) => value !== null).join(" – ");
  return `${currency} ${range}${salary.period ? ` / ${salary.period}` : ""}`.trim();
}
