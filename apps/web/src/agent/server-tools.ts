import {
  clientToolDefinitions,
  explainSearchPipelineDefinition,
  inspectSearchBriefDefinition,
} from "./tools";

const ROLE_MARKERS = [
  "accountant",
  "akuntan",
  "analyst",
  "designer",
  "developer",
  "engineer",
  "manager",
  "marketing",
  "product",
  "sales",
];
const LOCATION_MARKERS = ["bandung", "jakarta", "remote", "surabaya", "yogyakarta"];
const SKILL_MARKERS = ["accurate", "excel", "figma", "javascript", "python", "react", "sql"];

export const inspectSearchBriefTool = inspectSearchBriefDefinition.server(({ prompt }) => {
  const normalizedPrompt = prompt.trim().replace(/\s+/g, " ");
  const lowerPrompt = normalizedPrompt.toLowerCase();
  const missing = [] as Array<"role" | "location" | "skills">;
  if (!ROLE_MARKERS.some((marker) => lowerPrompt.includes(marker))) missing.push("role");
  if (!LOCATION_MARKERS.some((marker) => lowerPrompt.includes(marker))) missing.push("location");
  if (!SKILL_MARKERS.some((marker) => lowerPrompt.includes(marker))) missing.push("skills");

  return {
    missing,
    normalizedPrompt,
    ready: missing.length === 0,
    summary:
      missing.length === 0
        ? "The brief includes a target role, location, and useful skill signals."
        : `The brief can be stronger by adding: ${missing.join(", ")}.`,
  };
});

export const explainSearchPipelineTool = explainSearchPipelineDefinition.server(() => ({
  safeguards: [
    "Paid provider calls are capped in deterministic backend code.",
    "External pages are read only after title and completeness checks.",
    "The agent cannot add tools or change provider budgets.",
  ],
  stages: [
    { name: "Understand", purpose: "Parse the role, location, skills, and time window." },
    { name: "Discover", purpose: "Find candidate jobs through Google Jobs." },
    { name: "Enrich", purpose: "Read only matching postings with incomplete detail." },
    { name: "Assess", purpose: "Score, explain, rank, and persist the best matches." },
  ],
}));

export const serverTools = [
  inspectSearchBriefTool,
  explainSearchPipelineTool,
  ...clientToolDefinitions,
];
