import { afterEach, describe, expect, it, vi } from "vitest";
import { UnauthorizedApiError, createApiClient, fetchSessionUser, loginWithEmail } from "./index";

const user = {
  createdAt: "2026-11-11T00:00:00Z",
  email: "user@example.com",
  emailVerified: false,
  id: "user-id",
  image: null,
  name: "User",
  role: "user",
  updatedAt: "2026-11-11T00:00:00Z",
};

describe("API client", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("loads the session with credentialed fetch", async () => {
    const fetch = vi.fn().mockResolvedValue(Response.json({ session: {}, user }));
    vi.stubGlobal("fetch", fetch);

    await expect(fetchSessionUser(createApiClient("http://localhost:8000/"))).resolves.toEqual(
      user,
    );
    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8000/session",
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it("maps missing sessions to UnauthorizedApiError", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(Response.json({}, { status: 401 })));
    await expect(fetchSessionUser(createApiClient("http://localhost:8000"))).rejects.toBeInstanceOf(
      UnauthorizedApiError,
    );
  });

  it("returns FastAPI authentication errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          Response.json({ detail: "Invalid email or password." }, { status: 401 }),
        ),
    );
    await expect(
      loginWithEmail(createApiClient("http://localhost:8000"), {
        email: "user@example.com",
        password: "wrong",
      }),
    ).rejects.toThrow("Invalid email or password.");
  });
});
