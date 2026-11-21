import { toolDefinition } from "@tanstack/ai";
import {
  jobSearchCreatedSchema,
  jobSearchDetailSchema,
  jobSearchListSchema,
} from "@repo/contracts/job-search";
import { z } from "zod";

export const inspectSearchBriefDefinition = toolDefinition({
  description:
    "Validate and summarize a job-search brief before offering to start a paid search run.",
  inputSchema: z.object({ prompt: z.string().trim().min(10).max(1_000) }),
  name: "inspect_search_brief",
  outputSchema: z.object({
    missing: z.array(z.enum(["role", "location", "skills"])),
    normalizedPrompt: z.string(),
    ready: z.boolean(),
    summary: z.string(),
  }),
});

export const explainSearchPipelineDefinition = toolDefinition({
  description: "Explain how Tyche searches, reads, assesses, and ranks jobs.",
  inputSchema: z.object({}),
  name: "explain_search_pipeline",
  outputSchema: z.object({
    safeguards: z.array(z.string()),
    stages: z.array(z.object({ name: z.string(), purpose: z.string() })),
  }),
});

export const createJobSearchDefinition = toolDefinition({
  description:
    "Start an authenticated job-search run after the user has reviewed the exact prompt.",
  inputSchema: z.object({ prompt: z.string().trim().min(10).max(1_000) }),
  name: "create_job_search",
  needsApproval: true,
  outputSchema: jobSearchCreatedSchema,
});

export const getJobSearchDefinition = toolDefinition({
  description: "Load the latest status and ranked results for one authenticated job search.",
  inputSchema: z.object({ searchId: z.string().min(1) }),
  name: "get_job_search",
  outputSchema: jobSearchDetailSchema,
});

export const listJobSearchesDefinition = toolDefinition({
  description: "List the authenticated user's recent job searches.",
  inputSchema: z.object({}),
  name: "list_job_searches",
  outputSchema: jobSearchListSchema,
});

export const openJobPostingDefinition = toolDefinition({
  description: "Open an external job posting after the user approves leaving Tyche.",
  inputSchema: z.object({
    company: z.string(),
    title: z.string(),
    url: z.url({ protocol: /^https?$/ }),
  }),
  name: "open_job_posting",
  needsApproval: true,
  outputSchema: z.object({ opened: z.boolean() }),
});

export const clientToolDefinitions = [
  createJobSearchDefinition,
  getJobSearchDefinition,
  listJobSearchesDefinition,
  openJobPostingDefinition,
];

export function getOpenPostingMessage(opened: boolean) {
  return opened ? "Posting opened in a new tab." : "The browser blocked the new tab.";
}
