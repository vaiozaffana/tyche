import { describe, expect, it } from "vitest";
import { explainSearchPipelineTool, inspectSearchBriefTool } from "./server-tools";
import {
  createJobSearchDefinition,
  getOpenPostingMessage,
  openJobPostingDefinition,
} from "./tools";

describe("job-search agent tools", () => {
  it("keeps readiness deterministic and requires a recognizable role", async () => {
    const incomplete = await inspectSearchBriefTool.execute?.(
      { prompt: "Cari pekerjaan remote di Jakarta" },
      {} as never,
    );
    const complete = await inspectSearchBriefTool.execute?.(
      { prompt: "Cari backend developer Python remote di Jakarta" },
      {} as never,
    );
    const partial = await inspectSearchBriefTool.execute?.(
      { prompt: "Cari backend developer remote" },
      {} as never,
    );
    expect(incomplete).toMatchObject({
      missing: expect.arrayContaining(["role", "skills"]),
      ready: false,
    });
    expect(partial).toMatchObject({ missing: ["skills"], ready: false });
    expect(complete).toMatchObject({ missing: [], ready: true });
  });

  it("exposes the fixed cost and privacy safeguards", async () => {
    const result = await explainSearchPipelineTool.execute?.({}, {} as never);
    expect(result).toMatchObject({
      safeguards: expect.arrayContaining([expect.stringContaining("capped")]),
    });
    expect(result?.stages).toHaveLength(4);
  });

  it("requires approval for paid searches and external navigation", () => {
    expect(createJobSearchDefinition.needsApproval).toBe(true);
    expect(openJobPostingDefinition.needsApproval).toBe(true);
  });

  it("reports whether external navigation actually opened", () => {
    expect(getOpenPostingMessage(true)).toBe("Posting opened in a new tab.");
    expect(getOpenPostingMessage(false)).toBe("The browser blocked the new tab.");
  });
});
