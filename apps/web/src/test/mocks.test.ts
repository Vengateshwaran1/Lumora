import { describe, expect, it } from "vitest";

import {
  listMockActivity,
  listMockAgentRuns,
  listMockIssues,
  listMockPullRequests,
  listMockReviews,
} from "@/shared/mocks/api";

describe("shared/mocks/api", () => {
  it("returns non-empty preview data for every M3+ surface", async () => {
    await expect(listMockIssues()).resolves.not.toHaveLength(0);
    await expect(listMockPullRequests()).resolves.not.toHaveLength(0);
    await expect(listMockAgentRuns()).resolves.not.toHaveLength(0);
    await expect(listMockReviews()).resolves.not.toHaveLength(0);
    await expect(listMockActivity()).resolves.not.toHaveLength(0);
  });
});
