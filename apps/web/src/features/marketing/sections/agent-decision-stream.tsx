import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";

import { useReducedMotion } from "@/shared/hooks/use-reduced-motion";

const LOG_LINES = [
  "supervisor → planner: decompose issue #482 into 4 subtasks",
  "planner → retriever: fetch context for orders/service.py",
  "retriever: 12 chunks, 3 files, 2 related commits found",
  "coder: patch drafted — idempotency check before commit",
  "tester: 18/18 existing tests pass, 2 new tests added",
  "reviewer: flags edge case in retry-queue race condition",
  "debugger → coder: revise patch, awaiting re-test",
  "supervisor: escalating to human review before merge",
];

/** Cycling one-line agent activity log — landing-only flourish that reads
 * as "watch it work" without wiring a real run. Ticks every 2.8s. */
export function AgentDecisionStream() {
  const [index, setIndex] = useState(0);
  const reducedMotion = useReducedMotion();

  useEffect(() => {
    if (reducedMotion) return;
    const timer = setInterval(() => setIndex((v) => (v + 1) % LOG_LINES.length), 2800);
    return () => clearInterval(timer);
  }, [reducedMotion]);

  return (
    <div className="border-border bg-card/60 relative flex h-11 w-full max-w-2xl items-center overflow-hidden rounded-lg border px-4 font-mono text-xs">
      <span className="bg-success mr-3 size-1.5 shrink-0 animate-pulse rounded-full" aria-hidden />
      {reducedMotion ? (
        <span className="text-muted-foreground truncate">{LOG_LINES[0]}</span>
      ) : (
        <AnimatePresence mode="wait">
          <motion.span
            key={index}
            initial={{ opacity: 0, y: 8, filter: "blur(4px)" }}
            animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
            exit={{ opacity: 0, y: -8, filter: "blur(4px)" }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            className="text-muted-foreground truncate"
          >
            {LOG_LINES[index]}
          </motion.span>
        </AnimatePresence>
      )}
      <span className="text-primary ml-0.5 animate-pulse" aria-hidden>
        _
      </span>
    </div>
  );
}
