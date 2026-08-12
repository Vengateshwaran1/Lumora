/** Types for the M3+ feature previews (issues, PRs, agent runs, reviews,
 * activity beyond repo-level). No backend exists for any of this yet —
 * see `shared/mocks/data.ts` and `shared/mocks/api.ts`. Keep every consumer
 * of these types marked with `<PreviewBadge />` so it's never mistaken for
 * live data. */

export type IssueStatus = "open" | "planned" | "in_progress" | "closed";
export type IssuePriority = "low" | "medium" | "high";

export interface MockIssue {
  id: string;
  number: number;
  title: string;
  description: string;
  status: IssueStatus;
  priority: IssuePriority;
  repository: string;
  labels: string[];
  author: string;
  createdAt: string;
  updatedAt: string;
}

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

export type AgentRunStatus =
  | "queued"
  | "planning"
  | "retrieving"
  | "coding"
  | "testing"
  | "debugging"
  | "reviewing"
  | "awaiting_approval"
  | "completed"
  | "failed";

export interface AgentRunStep {
  name: string;
  status: "pending" | "active" | "done" | "failed";
  startedAt: string | null;
  completedAt: string | null;
}

export interface MockAgentRun {
  id: string;
  repository: string;
  issueId: string | null;
  status: AgentRunStatus;
  currentAgent: string | null;
  startedAt: string;
  completedAt: string | null;
  steps: AgentRunStep[];
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
