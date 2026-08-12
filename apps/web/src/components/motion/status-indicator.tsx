import { cn } from "@/shared/lib/utils";

export type SignalTone =
  "engineering" | "approval" | "ai-activity" | "success" | "error" | "neutral";

const TONE_CLASSES: Record<SignalTone, string> = {
  engineering: "bg-engineering",
  approval: "bg-approval",
  "ai-activity": "bg-ai-activity",
  success: "bg-success",
  error: "bg-destructive",
  neutral: "bg-muted-foreground",
};

const TONE_GLOW: Record<SignalTone, string> = {
  engineering: "shadow-[0_0_8px_var(--engineering-glow)]",
  approval: "shadow-[0_0_8px_var(--approval-glow)]",
  "ai-activity": "shadow-[0_0_8px_var(--ai-activity-glow)]",
  success: "shadow-[0_0_8px_var(--success-glow)]",
  error: "shadow-[0_0_8px_rgba(255,107,107,0.35)]",
  neutral: "",
};

interface StatusIndicatorProps {
  tone: SignalTone;
  label: string;
  pulse?: boolean;
  className?: string;
}

/** Small colored dot + label used across the app to signal semantic state
 * (indexing = engineering, awaiting approval = approval, agent working =
 * ai-activity, etc.) — colors are signals, not decoration, per design spec. */
export function StatusIndicator({ tone, label, pulse = false, className }: StatusIndicatorProps) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 text-xs font-medium", className)}>
      <span className="relative flex h-1.5 w-1.5">
        {pulse ? (
          <span
            className={cn(
              "absolute inline-flex h-full w-full animate-ping rounded-full opacity-60",
              TONE_CLASSES[tone],
            )}
          />
        ) : null}
        <span
          className={cn(
            "relative inline-flex h-1.5 w-1.5 rounded-full",
            TONE_CLASSES[tone],
            pulse && TONE_GLOW[tone],
          )}
        />
      </span>
      {label}
    </span>
  );
}
