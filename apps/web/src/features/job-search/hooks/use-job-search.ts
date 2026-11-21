import { queryOptions } from "@tanstack/react-query";
import { getJobSearch, getJobSearches } from "../services";

export const jobSearchKeys = {
  all: ["job-searches"] as const,
  detail: (searchId: string) => ["job-searches", searchId] as const,
};

export const jobSearchListQueryOptions = queryOptions({
  queryFn: getJobSearches,
  queryKey: jobSearchKeys.all,
  staleTime: 30_000,
});

export function getJobSearchRefetchInterval(status?: string) {
  return status === "queued" || status === "running" ? 2_000 : false;
}

export function jobSearchDetailQueryOptions(searchId: string) {
  return queryOptions({
    enabled: Boolean(searchId),
    queryFn: () => getJobSearch(searchId),
    queryKey: jobSearchKeys.detail(searchId),
    refetchInterval: (query) => getJobSearchRefetchInterval(query.state.data?.status),
  });
}
