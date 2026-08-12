import { fireEvent, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { RunResponse } from "@/shared/api/types";
import { renderPage } from "@/test/render-with-providers";

import { RunDetailPage } from "./run-detail-page";

const { getRunMock, approveRunMock, rejectRunMock, regenerateRunMock } = vi.hoisted(() => ({
  getRunMock: vi.fn(),
  approveRunMock: vi.fn(),
  rejectRunMock: vi.fn(),
  regenerateRunMock: vi.fn(),
}));

vi.mock("@/shared/api/runs", () => ({
  getRun: getRunMock,
  approveRun: approveRunMock,
  rejectRun: rejectRunMock,
  regenerateRun: regenerateRunMock,
}));

vi.mock("@/shared/api/run-events", () => ({ useRunEvents: vi.fn() }));

const PLAN: NonNullable<RunResponse["implementation_plan"]> = {
  summary: "Add JWT auth to the API",
  understanding: "Auth currently doesn't exist.",
  affected_files: ["src/auth/middleware.py"],
  affected_components: ["auth"],
  implementation_steps: [
    {
      step_number: 1,
      description: "Add JWT middleware",
      affected_files: ["src/auth/middleware.py"],
      affected_symbols: ["AuthMiddleware"],
      reason: "No auth exists yet",
      depends_on_steps: [],
      verification_method: "Integration tests",
    },
  ],
  dependencies: [],
  database_changes: [],
  api_changes: ["POST /login"],
  frontend_changes: [],
  testing_strategy: "Add integration tests for protected routes.",
  security_considerations: ["Rotate JWT secret regularly"],
  performance_considerations: [],
  risks: ["Existing sessions will be invalidated"],
  assumptions: ["Users table already has a password_hash column"],
  acceptance_criteria: ["Unauthenticated requests to protected routes return 401"],
  citations: [
    { file_path: "src/auth/middleware.py", start_line: 1, end_line: 10, claim: "no-op middleware" },
  ],
  confidence: 0.72,
};

function awaitingApprovalRun(overrides: Partial<RunResponse> = {}): RunResponse {
  return {
    id: "run-1",
    repository_id: "repo-1",
    issue_id: "issue-1",
    run_type: "planning",
    status: "awaiting_approval",
    implementation_plan: PLAN,
    validation_errors: [],
    metrics: {},
    error_message: null,
    created_at: "2026-08-12T00:00:00Z",
    started_at: "2026-08-12T00:00:01Z",
    completed_at: null,
    ...overrides,
  };
}

describe("RunDetailPage", () => {
  beforeEach(() => {
    getRunMock.mockReset();
    approveRunMock.mockReset();
    rejectRunMock.mockReset();
    regenerateRunMock.mockReset();
  });

  it("renders plan sections and citations for an awaiting-approval run", async () => {
    getRunMock.mockResolvedValue(awaitingApprovalRun());
    renderPage(<RunDetailPage />, { path: "/runs/:id", route: "/runs/run-1" });

    expect(await screen.findByText("Add JWT auth to the API")).toBeInTheDocument();
    expect(screen.getByText(/Awaiting human approval/)).toBeInTheDocument();
    expect(screen.getByText("Understanding")).toBeInTheDocument();
    expect(screen.getByText(/Affected Files \(1\)/)).toBeInTheDocument();
    expect(screen.getByText(/Citations \(1\)/)).toBeInTheDocument();
  });

  it("shows the validation-errors banner instead of hiding problems", async () => {
    getRunMock.mockResolvedValue(
      awaitingApprovalRun({ validation_errors: ["citation references an unretrieved file"] }),
    );
    renderPage(<RunDetailPage />, { path: "/runs/:id", route: "/runs/run-1" });

    expect(await screen.findByText("Plan validation issues")).toBeInTheDocument();
    expect(screen.getByText(/citation references an unretrieved file/)).toBeInTheDocument();
  });

  it("calls approveRun when Approve is clicked", async () => {
    const run = awaitingApprovalRun();
    getRunMock.mockResolvedValue(run);
    approveRunMock.mockResolvedValue({ ...run, status: "plan_approved" });

    renderPage(<RunDetailPage />, { path: "/runs/:id", route: "/runs/run-1" });
    const approveButton = await screen.findByRole("button", { name: /approve/i });
    fireEvent.click(approveButton);

    await waitFor(() => expect(approveRunMock).toHaveBeenCalledWith("run-1", undefined));
  });

  it("calls rejectRun when Reject is clicked", async () => {
    const run = awaitingApprovalRun();
    getRunMock.mockResolvedValue(run);
    rejectRunMock.mockResolvedValue({ ...run, status: "rejected" });

    renderPage(<RunDetailPage />, { path: "/runs/:id", route: "/runs/run-1" });
    const rejectButton = await screen.findByRole("button", { name: /reject/i });
    fireEvent.click(rejectButton);

    await waitFor(() => expect(rejectRunMock).toHaveBeenCalledWith("run-1", undefined));
  });

  it("calls regenerateRun when Regenerate is clicked", async () => {
    getRunMock.mockResolvedValue(awaitingApprovalRun());
    regenerateRunMock.mockResolvedValue({ run_id: "run-2", status: "queued" });

    renderPage(<RunDetailPage />, { path: "/runs/:id", route: "/runs/run-1" });
    const regenerateButton = await screen.findByRole("button", { name: /regenerate/i });
    fireEvent.click(regenerateButton);

    await waitFor(() => expect(regenerateRunMock).toHaveBeenCalledWith("run-1"));
  });

  it("does not show approve/reject/regenerate for a non-awaiting run", async () => {
    getRunMock.mockResolvedValue(awaitingApprovalRun({ status: "plan_approved" }));
    renderPage(<RunDetailPage />, { path: "/runs/:id", route: "/runs/run-1" });

    await screen.findByText("Add JWT auth to the API");
    expect(screen.queryByRole("button", { name: /approve/i })).not.toBeInTheDocument();
  });
});
