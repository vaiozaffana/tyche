import {
  createJobSearchDefinition,
  getJobSearchDefinition,
  listJobSearchesDefinition,
  openJobPostingDefinition,
} from "./tools";
import { getJobSearch, getJobSearches, startJobSearch } from "../features/job-search/services";

export function createClientTools(onSearchStateChanged: () => void) {
  const createJobSearchTool = createJobSearchDefinition.client(async ({ prompt }) => {
    const search = await startJobSearch({ prompt });
    onSearchStateChanged();
    return search;
  });
  const getJobSearchTool = getJobSearchDefinition.client(({ searchId }) => getJobSearch(searchId));
  const listJobSearchesTool = listJobSearchesDefinition.client(async () => ({
    searches: await getJobSearches(),
  }));
  const openJobPostingTool = openJobPostingDefinition.client(({ url }) => {
    const opened = window.open(url, "_blank", "noopener,noreferrer") !== null;
    return { opened };
  });

  return [createJobSearchTool, getJobSearchTool, listJobSearchesTool, openJobPostingTool] as const;
}
