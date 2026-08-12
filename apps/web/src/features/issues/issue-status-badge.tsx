import { StatusIndicator, type SignalTone } from "@/components/motion/status-indicator";

/** GitHub issue state — `IssueResponse.state` is a free-form string mirrored
 * from GitHub (typically "open"/"closed"), not a closed enum, so this falls
 * back to a neutral tone for anything unrecognized instead of erroring. */
export function IssueStateBadge({ state }: { state: string }) {
  const normalized = state.toLowerCase();
  const tone: SignalTone = normalized === "open" ? "engineering" : "success";
  const label = state.charAt(0).toUpperCase() + state.slice(1);
  return <StatusIndicator tone={tone} label={label} />;
}
