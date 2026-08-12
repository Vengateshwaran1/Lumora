import { useRef } from "react";

import { useScrollReveal } from "@/components/motion/use-scroll-reveal";
import { cn } from "@/shared/lib/utils";

const LOG = [
  { text: "$ lumora sandbox run --patch idempotency-fix", tone: "text-muted-foreground" },
  { text: "✓ test_process_retry_success", tone: "text-success" },
  { text: "✓ test_idempotency_lock_acquired", tone: "text-success" },
  { text: "✗ test_concurrent_retry_no_duplicate", tone: "text-destructive" },
  { text: "→ debugger: patching retry consumer re-entry guard", tone: "text-approval" },
  { text: "↻ retrying sandbox run", tone: "text-muted-foreground" },
  { text: "✓ test_concurrent_retry_no_duplicate", tone: "text-success" },
  { text: "18/18 tests passing — ready for review", tone: "text-success" },
];

/** Real-shaped Lumora surface — the actual sandbox run log, failure and
 * retry included — standing in for a generic "patch → sandbox → verify"
 * icon row. Reuses the same three-dot terminal chrome as the retrieval and
 * citation panels so it reads as one family, while the content itself
 * (a live-feeling test run) is nothing like them. */
export function SandboxConsolePanel() {
  const ref = useRef<HTMLDivElement>(null);
  useScrollReveal(ref, "[data-reveal-step]");

  return (
    <div ref={ref} className="border-border bg-card/60 mx-auto w-full max-w-2xl overflow-hidden rounded-md border">
      <div className="border-border bg-secondary/30 flex items-center gap-2 border-b px-4 py-2.5">
        <span className="bg-destructive/60 size-2.5 rounded-full" aria-hidden />
        <span className="bg-approval/60 size-2.5 rounded-full" aria-hidden />
        <span className="bg-success/60 size-2.5 rounded-full" aria-hidden />
        <span className="text-muted-foreground font-mono ml-2 text-xs">sandbox</span>
      </div>

      <div className="flex flex-col gap-1.5 px-4 py-4">
        {LOG.map((line, index) => (
          <div key={index} data-reveal-step className={cn("font-mono text-xs", line.tone)}>
            {line.text}
          </div>
        ))}
      </div>
    </div>
  );
}
