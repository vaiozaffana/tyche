import { describe, expect, it } from "vitest";
import {
  jobSearchCreateInputSchema,
  jobSearchDetailSchema,
  jobSearchResultSchema,
} from "./job-search";

const result = {
  company: "Nusantara Systems",
  enrichment: "scraped",
  fitReason: "Relevant backend experience.",
  fitScore: 87,
  focusFindings: { techStack: ["Python", "PostgreSQL"] },
  location: "Jakarta",
  postedAt: "3 days ago",
  qualifications: ["Three years of backend experience"],
  rank: 1,
  salary: { currency: "IDR", max: 25_000_000, min: 18_000_000, period: "month", raw: null },
  sourceSite: "example.com",
  sourceUrl: "https://example.com/jobs/backend",
  techStack: ["Python", "PostgreSQL"],
  title: "Backend Engineer",
};

describe("job-search contract", () => {
  it("normalizes a search prompt at the browser boundary", () => {
    expect(jobSearchCreateInputSchema.parse({ prompt: "  Backend Python remote  " })).toEqual({
      prompt: "Backend Python remote",
    });
    expect(jobSearchCreateInputSchema.safeParse({ prompt: "short" }).success).toBe(false);
  });

  it("accepts nullable result fields and rejects unsafe source URLs", () => {
    expect(jobSearchResultSchema.safeParse(result).success).toBe(true);
    expect(
      jobSearchResultSchema.safeParse({ ...result, sourceUrl: "javascript:alert(1)" }).success,
    ).toBe(false);
    expect(
      jobSearchResultSchema.safeParse({
        ...result,
        fitReason: null,
        fitScore: null,
        salary: null,
        sourceUrl: null,
      }).success,
    ).toBe(true);
  });

  it("parses a completed detail response with serialized timestamps", () => {
    expect(
      jobSearchDetailSchema.safeParse({
        completedAt: "2026-11-20T10:00:00Z",
        createdAt: "2026-11-20T09:59:00Z",
        errorMessage: null,
        id: "search-1",
        parsedQuery: {
          datePosted: "week",
          experienceLevel: "mid",
          keywords: ["python"],
          language: "id",
          locations: ["Jakarta"],
          remotePreference: "remote",
          skills: ["PostgreSQL"],
          targetRoles: ["Backend Engineer"],
        },
        prompt: "Cari backend engineer Python remote",
        results: [result],
        specialists: [{ specId: "specialist-1" }],
        stats: {
          afterDedup: 4,
          afterFilter: 3,
          cacheHits: 1,
          candidates: 5,
          firecrawlCalls: 2,
          llmCalls: 3,
          serpCalls: 1,
          specialists: 1,
        },
        status: "completed",
      }).success,
    ).toBe(true);
  });
});
