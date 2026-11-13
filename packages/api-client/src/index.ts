import {
  profileResponseSchema,
  type ProfileUser,
  type UpdateProfileInput as ProfileUpdateInput,
} from "@repo/contracts/profile";

export type ApiClient = { baseUrl: string };
export type LoginInput = { email: string; password: string };
export type RegisterInput = LoginInput & { name: string };
export type SessionUser = ProfileUser;
export type UpdateProfileInput = ProfileUpdateInput;

export function createApiClient(baseUrl: string): ApiClient {
  return { baseUrl: baseUrl.replace(/\/$/, "") };
}

export class UnauthorizedApiError extends Error {
  constructor() {
    super("Unauthorized");
    this.name = "UnauthorizedApiError";
  }
}

export async function fetchSessionUser(client: ApiClient) {
  const response = await request(client, "/session");
  if (response.status === 401) throw new UnauthorizedApiError();
  await assertOk(response, "Failed to load current user.");
  return profileResponseSchema.parse(await response.json()).user;
}

export async function loginWithEmail(client: ApiClient, input: LoginInput) {
  const response = await request(client, "/api/auth/sign-in/email", {
    body: JSON.stringify(input),
    method: "POST",
  });
  await assertOk(response, "Authentication failed.");
  return profileResponseSchema.parse(await response.json()).user;
}

export async function registerWithEmail(client: ApiClient, input: RegisterInput) {
  const response = await request(client, "/api/auth/sign-up/email", {
    body: JSON.stringify(input),
    method: "POST",
  });
  await assertOk(response, "Registration failed.");
  return profileResponseSchema.parse(await response.json()).user;
}

export async function logoutCurrentUser(client: ApiClient) {
  const response = await request(client, "/api/auth/sign-out", { method: "POST" });
  await assertOk(response, "Failed to log out.");
}

export async function updateCurrentUserProfile(client: ApiClient, input: UpdateProfileInput) {
  const response = await request(client, "/profile", {
    body: JSON.stringify(input),
    method: "PATCH",
  });
  if (response.status === 401) throw new UnauthorizedApiError();
  await assertOk(response, "Failed to update profile.");
  return profileResponseSchema.parse(await response.json()).user;
}

function request(client: ApiClient, path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  if (init.body) headers.set("Content-Type", "application/json");
  return fetch(`${client.baseUrl}${path}`, {
    ...init,
    credentials: "include",
    headers,
  });
}

async function assertOk(response: Response, fallback: string) {
  if (response.ok) return;
  let data: unknown;
  try {
    data = await response.json();
  } catch {
    throw new Error(fallback);
  }
  if (data && typeof data === "object" && "detail" in data && typeof data.detail === "string") {
    throw new Error(data.detail);
  }
  throw new Error(fallback);
}
