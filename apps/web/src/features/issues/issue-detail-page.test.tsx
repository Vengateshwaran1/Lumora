import { screen, waitFor } from "@testing-library/react";
import { fireEvent } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { IssueResponse } from "@/shared/api/types";
import { renderPage } from "@/test/render-with-providers";

import { IssueDetailPage } from "./issue-detail-page";

const { getIssueMock, generatePlanMock, navigateMock } = vi.hoisted(() => ({
  getIssueMock: vi.fn(),
  generatePlanMock: vi.fn(),
  navigateMock: vi.fn(),
}));

vi.mock("@/shared/api/issues", () => ({
  getIssue: getIssueMock,
  generatePlan: generatePlanMock,
}));

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router-dom")>();
  return { ...actual, useNavigate: () => navigateMock };
});

const ISSUE: IssueResponse = {
  id: "issue-1",
  repository_id: "repo-1",
  number: 42,
  title: "Add JWT authentication",
  body: "We need JWT auth for the API.",
  author: "octocat",
  labels: ["enhancement"],
  state: "open",
  html_url: "https://github.com/o/r/issues/42",
  github_created_at: "2026-08-01T00:00:00Z",
  github_updated_at: "2026-08-01T00:00:00Z",
  github_closed_at: null,
  synced_at: "2026-08-01T00:00:00Z",
};

describe("IssueDetailPage", () => {
  beforeEach(() => {
    getIssueMock.mockReset();
    generatePlanMock.mockReset();
    navigateMock.mockReset();
  });

  it("shows a helpful message when opened without repository context", () => {
    renderPage(<IssueDetailPage />, { path: "/issues/:id", route: "/issues/issue-1" });
    expect(screen.getByText(/Missing repository context for this issue/)).toBeInTheDocument();
  });

  it("generates a plan and navigates to the new run", async () => {
    getIssueMock.mockResolvedValue(ISSUE);
    generatePlanMock.mockResolvedValue({ run_id: "run-1", status: "queued" });

    renderPage(<IssueDetailPage />, {
      path: "/issues/:id",
      route: "/issues/issue-1?repo=repo-1",
    });

    const button = await screen.findByRole("button", { name: /generate plan/i });
    fireEvent.click(button);

    await waitFor(() => expect(generatePlanMock).toHaveBeenCalledWith("repo-1", "issue-1"));
    await waitFor(() => expect(navigateMock).toHaveBeenCalledWith("/app/runs/run-1"));
  });
});
