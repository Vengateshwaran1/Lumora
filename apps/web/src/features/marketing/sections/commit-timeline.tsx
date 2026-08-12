import { useRef } from "react";

import { useScrollReveal } from "@/components/motion/use-scroll-reveal";
import { cn } from "@/shared/lib/utils";

const EVENTS = [
  { kind: "commit", ref: "a3f91c2", label: "fix: idempotency lock race" },
  { kind: "issue", ref: "#482", label: "Payment retry duplicates orders" },
  { kind: "decision", ref: "RFC-09", label: "Retry-queue redesign" },
  { kind: "pr", ref: "#156", label: "Idempotency check before commit" },
  { kind: "commit", ref: "9e0d41f", label: "test: retry-queue race" },
];

/** Real-shaped Lumora surface — a vertical ledger of the commits, issues,
 * decisions, and PRs that shaped a piece of code — standing in for the
 * generic horizontal row-of-nodes template shared by the other step
 * sections. */
export function CommitTimeline() {
  const ref = useRef<HTMLDivElement>(null);
  useScrollReveal(ref, "[data-reveal-step]");

  return (
    <div ref={ref} className="border-border relative mx-auto flex w-full max-w-xl flex-col gap-7 border-l pl-7">
      {EVENTS.map((event) => (
        <div key={event.ref} data-reveal-step className="relative">
          <span
            className="bg-primary absolute top-1 -left-[31px] size-2.5 rounded-full shadow-[0_0_10px_rgba(var(--lum-primary-rgb),0.6)]"
            aria-hidden
          />
          <div className="flex items-baseline gap-2">
            <span
              className={cn(
                "font-mono text-[10px] tracking-wide uppercase",
                event.kind === "commit" && "text-engineering",
                event.kind === "issue" && "text-destructive",
                event.kind === "decision" && "text-ai-activity",
                event.kind === "pr" && "text-success",
              )}
            >
              {event.kind}
            </span>
            <span className="text-primary font-mono text-xs">{event.ref}</span>
          </div>
          <p className="text-foreground/80 mt-1 text-sm leading-snug">{event.label}</p>
        </div>
      ))}
    </div>
  );
}
