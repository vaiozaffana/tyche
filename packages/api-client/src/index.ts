import axios, { AxiosError, type AxiosInstance } from "axios";
import {
  jobSearchCreateInputSchema,
  jobSearchCreatedSchema,
  jobSearchDetailSchema,
  jobSearchListSchema,
  type JobSearchCreateInput,
} from "@repo/contracts/job-search";
import {
  profileResponseSchema,
  type ProfileUser,
  type UpdateProfileInput as ProfileUpdateInput,
} from "@repo/contracts/profile";

export type ApiClient = AxiosInstance;
export type LoginInput = { email: string; password: string };
export type RegisterInput = LoginInput & { name: string };
export type SessionUser = ProfileUser;
export type UpdateProfileInput = ProfileUpdateInput;

export function createApiClient(baseUrl: string): ApiClient {
  return axios.create({
    adapter: "fetch",
    baseURL: baseUrl.replace(/\/$/, ""),
    headers: { "Content-Type": "application/json" },
    withCredentials: true,
  });
}

export class UnauthorizedApiError extends Error {
  constructor() {
    super("Unauthorized");
    this.name = "UnauthorizedApiError";
  }
}

export async function fetchSessionUser(client: ApiClient) {
  try {
    return profileResponseSchema.parse((await client.get("/session")).data).user;
  } catch (error) {
    throw mapApiError(error, "Failed to load current user.", true);
  }
}

export async function loginWithEmail(client: ApiClient, input: LoginInput) {
  try {
    return profileResponseSchema.parse((await client.post("/api/auth/sign-in/email", input)).data)
      .user;
  } catch (error) {
    throw mapApiError(error, "Authentication failed.");
  }
}

export async function registerWithEmail(client: ApiClient, input: RegisterInput) {
  try {
    return profileResponseSchema.parse((await client.post("/api/auth/sign-up/email", input)).data)
      .user;
  } catch (error) {
    throw mapApiError(error, "Registration failed.");
  }
}

export async function logoutCurrentUser(client: ApiClient) {
  try {
    await client.post("/api/auth/sign-out");
  } catch (error) {
    throw mapApiError(error, "Failed to log out.");
  }
}

export async function updateCurrentUserProfile(client: ApiClient, input: UpdateProfileInput) {
  try {
    return profileResponseSchema.parse((await client.patch("/profile", input)).data).user;
  } catch (error) {
    throw mapApiError(error, "Failed to update profile.", true);
  }
}

export async function createJobSearch(client: ApiClient, input: JobSearchCreateInput) {
  try {
    const body = jobSearchCreateInputSchema.parse(input);
    return jobSearchCreatedSchema.parse((await client.post("/job-searches", body)).data);
  } catch (error) {
    throw mapApiError(error, "Failed to start job search.", true);
  }
}

export async function fetchJobSearch(client: ApiClient, searchId: string) {
  try {
    return jobSearchDetailSchema.parse((await client.get(`/job-searches/${searchId}`)).data);
  } catch (error) {
    throw mapApiError(error, "Failed to load job search.", true);
  }
}

export async function fetchJobSearches(client: ApiClient) {
  try {
    return jobSearchListSchema.parse((await client.get("/job-searches")).data).searches;
  } catch (error) {
    throw mapApiError(error, "Failed to load job searches.", true);
  }
}

function mapApiError(error: unknown, fallback: string, mapUnauthorized = false): Error {
  if (mapUnauthorized && error instanceof AxiosError && error.response?.status === 401) {
    return new UnauthorizedApiError();
  }
  if (error instanceof AxiosError) {
    const data: unknown = error.response?.data;
    if (data && typeof data === "object") {
      if ("detail" in data && typeof data.detail === "string") return new Error(data.detail);
      if ("error" in data && typeof data.error === "string") return new Error(data.error);
    }
  }
  return error instanceof Error && !(error instanceof AxiosError) ? error : new Error(fallback);
}
