import { createJobSearch, fetchJobSearch, fetchJobSearches } from "@repo/api-client";
import type { JobSearchCreateInput } from "@repo/contracts/job-search";
import { apiClient } from "../../api";

export function startJobSearch(input: JobSearchCreateInput) {
  return createJobSearch(apiClient, input);
}

export function getJobSearch(searchId: string) {
  return fetchJobSearch(apiClient, searchId);
}

export function getJobSearches() {
  return fetchJobSearches(apiClient);
}
