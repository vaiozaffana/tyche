import { z } from "zod";

export const jobSearchStatusSchema = z.enum(["queued", "running", "completed", "failed"]);

export const jobSearchCreateInputSchema = z.object({
  prompt: z.string().trim().min(10).max(1_000),
});

export const jobSearchCreatedSchema = z.object({
  createdAt: z.iso.datetime(),
  id: z.string().min(1),
  status: jobSearchStatusSchema,
});

export const jobSearchSalarySchema = z.object({
  currency: z.string().nullable(),
  max: z.number().nullable(),
  min: z.number().nullable(),
  period: z.string().nullable(),
  raw: z.string().nullable(),
});

export const jobSearchResultSchema = z.object({
  company: z.string(),
  enrichment: z.enum(["not_needed", "scraped", "cached", "skipped", "failed"]),
  fitReason: z.string().nullable(),
  fitScore: z.number().int().min(0).max(100).nullable(),
  focusFindings: z.record(z.string(), z.array(z.string())),
  location: z.string(),
  postedAt: z.string().nullable(),
  qualifications: z.array(z.string()),
  rank: z.number().int().positive(),
  salary: jobSearchSalarySchema.nullable(),
  sourceSite: z.string().nullable(),
  sourceUrl: z.url({ protocol: /^https?$/ }).nullable(),
  techStack: z.array(z.string()),
  title: z.string(),
});

export const parsedJobSearchQuerySchema = z.object({
  datePosted: z.enum(["today", "3days", "week", "month"]).nullable(),
  experienceLevel: z.string().nullable(),
  keywords: z.array(z.string()),
  language: z.enum(["id", "en"]),
  locations: z.array(z.string()),
  remotePreference: z.enum(["remote", "hybrid", "onsite", "any"]),
  skills: z.array(z.string()),
  targetRoles: z.array(z.string()),
});

export const jobSearchStatsSchema = z.object({
  afterDedup: z.number().int().nonnegative(),
  afterFilter: z.number().int().nonnegative(),
  cacheHits: z.number().int().nonnegative(),
  candidates: z.number().int().nonnegative(),
  firecrawlCalls: z.number().int().nonnegative(),
  llmCalls: z.number().int().nonnegative(),
  serpCalls: z.number().int().nonnegative(),
  specialists: z.number().int().nonnegative(),
});

export const jobSearchSummarySchema = z.object({
  completedAt: z.iso.datetime().nullable(),
  createdAt: z.iso.datetime(),
  id: z.string().min(1),
  prompt: z.string(),
  status: jobSearchStatusSchema,
});

export const jobSearchListSchema = z.object({ searches: z.array(jobSearchSummarySchema) });

export const jobSearchDetailSchema = jobSearchSummarySchema.extend({
  errorMessage: z.string().nullable(),
  parsedQuery: parsedJobSearchQuerySchema.nullable(),
  results: z.array(jobSearchResultSchema),
  specialists: z.array(z.record(z.string(), z.unknown())),
  stats: jobSearchStatsSchema,
});

export type JobSearchCreateInput = z.output<typeof jobSearchCreateInputSchema>;
export type JobSearchCreated = z.output<typeof jobSearchCreatedSchema>;
export type JobSearchDetail = z.output<typeof jobSearchDetailSchema>;
export type JobSearchList = z.output<typeof jobSearchListSchema>;
export type JobSearchResult = z.output<typeof jobSearchResultSchema>;
export type JobSearchStatus = z.output<typeof jobSearchStatusSchema>;
export type JobSearchSummary = z.output<typeof jobSearchSummarySchema>;
