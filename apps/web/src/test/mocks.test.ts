import { describe, expect, it } from "vitest";

import { listMockActivity, listMockPullRequests, listMockReviews } from "@/shared/mocks/api";

describe("shared/mocks/api", () => {
  it("returns non-empty preview data for every M4+ surface", async () => {
    await expect(listMockPullRequests()).resolves.not.toHaveLength(0);
    await expect(listMockReviews()).resolves.not.toHaveLength(0);
    await expect(listMockActivity()).resolves.not.toHaveLength(0);
  });
});
