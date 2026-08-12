/** Types for the M4+ feature previews (PRs, reviews, activity beyond
 * repo-level). No backend exists for any of this yet — see
 * `shared/mocks/data.ts` and `shared/mocks/api.ts`. Keep every consumer of
 * these types marked with `<PreviewBadge />` so it's never mistaken for live
 * data. Issues and agent runs went live in M3 — see `shared/api/issues.ts`,
 * `shared/api/runs.ts`, and `features/issues`/`features/runs`. */

export type PrStatus = "draft" | "open" | "approved" | "merged" | "closed";

export interface MockPullRequest {
  id: string;
  number: number;
  title: string;
  status: PrStatus;
  repository: string;
  branch: string;
  author: "agent" | "human";
  createdAt: string;
  updatedAt: string;
  filesChanged: number;
  additions: number;
  deletions: number;
  checks: { passed: number; failed: number; pending: number };
  issueId: string | null;
}

export type ReviewStatus = "pending" | "approved" | "changes_requested";

export interface MockReview {
  id: string;
  prId: string;
  prTitle: string;
  repository: string;
  status: ReviewStatus;
  reviewer: "human" | "agent";
  comments: number;
  createdAt: string;
}

export type ActivityEventType =
  "index" | "issue" | "pull_request" | "agent_run" | "webhook" | "review";

export interface MockActivityEvent {
  id: string;
  type: ActivityEventType;
  title: string;
  description: string;
  repository: string;
  actor: string;
  timestamp: string;
}
