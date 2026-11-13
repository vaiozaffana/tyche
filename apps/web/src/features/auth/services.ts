import {
  fetchSessionUser,
  loginWithEmail,
  logoutCurrentUser,
  registerWithEmail,
} from "@repo/api-client";
import { apiClient } from "../../api";
import type { LoginInput, RegisterInput } from "./types";

export async function getCurrentUser() {
  return fetchSessionUser(apiClient);
}

export async function login(input: LoginInput) {
  return loginWithEmail(apiClient, input);
}

export async function register(input: RegisterInput) {
  return registerWithEmail(apiClient, {
    email: input.email,
    name: input.name.trim(),
    password: input.password,
  });
}

export async function logout() {
  await logoutCurrentUser(apiClient);
}
