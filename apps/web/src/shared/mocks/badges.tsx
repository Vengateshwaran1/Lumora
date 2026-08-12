import { StatusIndicator, type SignalTone } from "@/components/motion/status-indicator";

import type { PrStatus, ReviewStatus } from "./types";

const PR_TONE: Record<PrStatus, SignalTone> = {
  draft: "neutral",
  open: "engineering",
  approved: "success",
  merged: "ai-activity",
  closed: "error",
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

export function PrStatusBadge({ status }: { status: PrStatus }) {
  return <StatusIndicator tone={PR_TONE[status]} label={label(status)} />;
}

export function ReviewStatusBadge({ status }: { status: ReviewStatus }) {
  return <StatusIndicator tone={REVIEW_TONE[status]} label={label(status)} />;
}
