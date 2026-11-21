import type { JobSearchResult } from "@repo/contracts/job-search";
import { describe, expect, it } from "vitest";
import { formatSalary } from "./search-results";

describe("formatSalary", () => {
  it("prefers provider text and safely falls back to source metadata", () => {
    expect(formatSalary({ salary: { raw: "IDR 15–20 juta" } } as JobSearchResult)).toBe(
      "IDR 15–20 juta",
    );
    expect(formatSalary({ salary: null, sourceSite: "LinkedIn" } as JobSearchResult)).toBe(
      "LinkedIn",
    );
  });

  it("formats structured salary bounds without inventing missing values", () => {
    expect(
      formatSalary({
        salary: { currency: "USD", max: 8_000, min: 5_000, period: "month", raw: null },
      } as JobSearchResult),
    ).toBe("USD 5000 – 8000 / month");
  });
});
