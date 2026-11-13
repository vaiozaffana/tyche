import { createApiClient } from "@repo/api-client";
import { parseWebEnv } from "./config";

const env = parseWebEnv(import.meta.env);
export const apiClient = createApiClient(env.VITE_API_URL);
