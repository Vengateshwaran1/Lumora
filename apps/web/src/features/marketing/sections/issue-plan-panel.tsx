import { CheckCircle2, Circle } from "lucide-react";
import { useRef } from "react";

import { useScrollReveal } from "@/components/motion/use-scroll-reveal";
import { cn } from "@/shared/lib/utils";

const LABELS = [
  { text: "bug", tone: "text-destructive border-destructive/30 bg-destructive/10" },
  { text: "payments", tone: "text-engineering border-engineering/30 bg-engineering/10" },
];

const PLAN = [
  { done: true, text: "Add idempotency check before the commit lands", cite: "idempotency.py" },
  { done: true, text: "Guard the retry consumer against partition re-entry", cite: "retry_handler.py" },
  { done: false, text: "Add a regression test for concurrent retries", cite: "test_orders.py" },
  { done: false, text: "Note retry-queue behavior in the on-call runbook", cite: "runbook.md" },
];

/** Real-shaped Lumora surface — the actual issue header plus the generated
 * checklist plan traced back to files — standing in for a generic
 * "issue → context → plan → approval" icon row. */
export function IssuePlanPanel() {
  const ref = useRef<HTMLDivElement>(null);
  useScrollReveal(ref, "[data-reveal]");

  return (
    <div ref={ref} className="border-border bg-card/60 mx-auto w-full max-w-xl rounded-md border">
      <div data-reveal className="border-border flex items-start gap-3 border-b px-5 py-4">
        <span className="text-muted-foreground font-mono text-xs">#482</span>
        <div className="flex flex-1 flex-col gap-2">
          <p className="text-foreground text-sm font-medium">
            Payment retry creates duplicate orders
          </p>
          <div className="flex gap-1.5">
            {LABELS.map((label) => (
              <span
                key={label.text}
                className={cn(
                  "rounded-full border px-2 py-0.5 font-mono text-[10px]",
                  label.tone,
                )}
              >
                {label.text}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div data-reveal className="border-border text-muted-foreground border-b px-5 py-2.5 font-mono text-[11px] tracking-wide uppercase">
        Generated plan
      </div>

      <ul className="flex flex-col gap-3 px-5 py-4">
        {PLAN.map((item) => (
          <li key={item.text} data-reveal className="flex items-start gap-3">
            {item.done ? (
              <CheckCircle2 className="text-success mt-0.5 size-4 shrink-0" />
            ) : (
              <Circle className="text-muted-foreground/40 mt-0.5 size-4 shrink-0" />
            )}
            <div className="flex min-w-0 flex-1 flex-wrap items-baseline gap-x-2">
              <span className={cn("text-sm", item.done ? "text-foreground/70 line-through" : "text-foreground")}>
                {item.text}
              </span>
              <span className="text-primary shrink-0 font-mono text-[11px]">{item.cite}</span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
