import { StatusIndicator, type SignalTone } from "@/components/motion/status-indicator";

import type { RunStatus } from "@/shared/api/types";

const STATUS_LABEL: Record<RunStatus, string> = {
  queued: "Queued",
  running: "Running",
  awaiting_approval: "Awaiting approval",
  plan_approved: "Plan approved",
  rejected: "Rejected",
  failed: "Failed",
};

const STATUS_TONE: Record<RunStatus, SignalTone> = {
  queued: "neutral",
  running: "ai-activity",
  awaiting_approval: "approval",
  plan_approved: "success",
  rejected: "error",
  failed: "error",
};

const ACTIVE: RunStatus[] = ["queued", "running"];

export function RunStatusBadge({ status }: { status: RunStatus }) {
  return (
    <StatusIndicator
      tone={STATUS_TONE[status]}
      label={STATUS_LABEL[status]}
      pulse={ACTIVE.includes(status)}
    />
  );
}
