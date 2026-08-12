import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  chatWithRepository,
  getIndexStatus,
  registerRepository,
  searchRepository,
  triggerIndex,
  triggerReindex,
} from "@/shared/api/repositories";

function mockFetchOnce(body: unknown, status = 200) {
  const response = {
    ok: status < 400,
    status,
    json: () => Promise.resolve(body),
    text: () => Promise.resolve(JSON.stringify(body)),
  } as Response;
  const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(response);
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function lastCall(fetchMock: ReturnType<typeof vi.fn<typeof fetch>>) {
  const [url, init] = fetchMock.mock.calls[0]!;
  // apiFetch always calls fetch(`${API_BASE_URL}${path}`, ...) — url is always a plain string.
  return { url: url as string, init: init! };
}

describe("shared/api/repositories", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  it("registerRepository posts the url", async () => {
    const fetchMock = mockFetchOnce({ id: "1" });
    await registerRepository("https://github.com/acme/payments.git");

    const { url, init } = lastCall(fetchMock);
    expect(url).toMatch(/\/repositories$/);
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual({
      url: "https://github.com/acme/payments.git",
    });
  });

  it("triggerIndex posts to /index", async () => {
    const fetchMock = mockFetchOnce({ id: "1" });
    await triggerIndex("repo-1");
    const { url, init } = lastCall(fetchMock);
    expect(url).toMatch(/\/repositories\/repo-1\/index$/);
    expect(init.method).toBe("POST");
  });

  it("triggerReindex posts to /reindex", async () => {
    const fetchMock = mockFetchOnce({ id: "1" });
    await triggerReindex("repo-1");
    const { url, init } = lastCall(fetchMock);
    expect(url).toMatch(/\/repositories\/repo-1\/reindex$/);
    expect(init.method).toBe("POST");
  });

  it("getIndexStatus gets /index-status", async () => {
    const fetchMock = mockFetchOnce({ id: "1" });
    await getIndexStatus("repo-1");
    const { url } = lastCall(fetchMock);
    expect(url).toMatch(/\/repositories\/repo-1\/index-status$/);
  });

  it("searchRepository posts query and top_k", async () => {
    const fetchMock = mockFetchOnce({ results: [] });
    await searchRepository("repo-1", "auth flow", 5);
    const { url, init } = lastCall(fetchMock);
    expect(url).toMatch(/\/repositories\/repo-1\/search$/);
    expect(JSON.parse(init.body as string)).toEqual({ query: "auth flow", top_k: 5 });
  });

  it("chatWithRepository posts the question", async () => {
    const fetchMock = mockFetchOnce({ answer: "", citations: [] });
    await chatWithRepository("repo-1", "why does retry duplicate orders?");
    const { url, init } = lastCall(fetchMock);
    expect(url).toMatch(/\/repositories\/repo-1\/chat$/);
    expect(JSON.parse(init.body as string)).toEqual({
      question: "why does retry duplicate orders?",
    });
  });

  it("throws ApiError with the response status on failure", async () => {
    mockFetchOnce({ detail: "not found" }, 404);
    await expect(getIndexStatus("missing")).rejects.toMatchObject({ status: 404 });
  });
});
