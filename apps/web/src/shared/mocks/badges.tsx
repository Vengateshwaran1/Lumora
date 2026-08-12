import { StatusIndicator, type SignalTone } from "@/components/motion/status-indicator";

import type { AgentRunStatus, IssueStatus, PrStatus, ReviewStatus } from "./types";

const ISSUE_TONE: Record<IssueStatus, SignalTone> = {
  open: "neutral",
  planned: "ai-activity",
  in_progress: "engineering",
  closed: "success",
};

const PR_TONE: Record<PrStatus, SignalTone> = {
  draft: "neutral",
  open: "engineering",
  approved: "success",
  merged: "ai-activity",
  closed: "error",
};

const RUN_TONE: Record<AgentRunStatus, SignalTone> = {
  queued: "neutral",
  planning: "ai-activity",
  retrieving: "ai-activity",
  coding: "ai-activity",
  testing: "ai-activity",
  debugging: "ai-activity",
  reviewing: "ai-activity",
  awaiting_approval: "approval",
  completed: "success",
  failed: "error",
};

const REVIEW_TONE: Record<ReviewStatus, SignalTone> = {
  pending: "approval",
  approved: "success",
  changes_requested: "error",
};

function label(value: string): string {
  return value
    .split("_")
    .map((word) => word[0]!.toUpperCase() + word.slice(1))
    .join(" ");
}

export function IssueStatusBadge({ status }: { status: IssueStatus }) {
  return <StatusIndicator tone={ISSUE_TONE[status]} label={label(status)} />;
}

export function PrStatusBadge({ status }: { status: PrStatus }) {
  return <StatusIndicator tone={PR_TONE[status]} label={label(status)} />;
}

export function RunStatusBadge({ status }: { status: AgentRunStatus }) {
  const active = !["queued", "completed", "failed"].includes(status);
  return <StatusIndicator tone={RUN_TONE[status]} label={label(status)} pulse={active} />;
}

export function ReviewStatusBadge({ status }: { status: ReviewStatus }) {
  return <StatusIndicator tone={REVIEW_TONE[status]} label={label(status)} />;
}
