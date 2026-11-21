import { describe, expect, it } from "vitest";
import { getJobSearchRefetchInterval } from "./use-job-search";

describe("getJobSearchRefetchInterval", () => {
  it("polls active searches and stops on terminal states", () => {
    expect(getJobSearchRefetchInterval("queued")).toBe(2_000);
    expect(getJobSearchRefetchInterval("running")).toBe(2_000);
    expect(getJobSearchRefetchInterval("completed")).toBe(false);
    expect(getJobSearchRefetchInterval("failed")).toBe(false);
  });
});
