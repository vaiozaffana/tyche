import { afterEach, describe, expect, it, vi } from "vitest";
import {
  UnauthorizedApiError,
  createApiClient,
  createJobSearch,
  fetchSessionUser,
  loginWithEmail,
} from "./index";

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

  it("loads the session through a credentialed Axios request", async () => {
    const fetch = vi.fn().mockResolvedValue(Response.json({ session: {}, user }));
    vi.stubGlobal("fetch", fetch);

    await expect(fetchSessionUser(createApiClient("http://localhost:8000/"))).resolves.toEqual(
      user,
    );
    const request = fetch.mock.calls[0]?.[0];
    expect(request).toBeInstanceOf(Request);
    expect(request).toMatchObject({ credentials: "include", url: "http://localhost:8000/session" });
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

  it("normalizes and parses job-search creation", async () => {
    const fetch = vi
      .fn()
      .mockResolvedValue(
        Response.json(
          { createdAt: "2026-11-20T10:00:00Z", id: "search-1", status: "queued" },
          { status: 202 },
        ),
      );
    vi.stubGlobal("fetch", fetch);

    await expect(
      createJobSearch(createApiClient("http://localhost:8000"), {
        prompt: "  Backend Python remote  ",
      }),
    ).resolves.toMatchObject({ id: "search-1", status: "queued" });

    const request = fetch.mock.calls[0]?.[0] as Request;
    await expect(request.clone().json()).resolves.toEqual({ prompt: "Backend Python remote" });
  });
});
