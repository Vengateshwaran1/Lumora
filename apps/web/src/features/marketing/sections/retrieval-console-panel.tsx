import { motion, type Variants } from "framer-motion";
import type { PointerEvent } from "react";

import { useReducedMotion } from "@/shared/hooks/use-reduced-motion";
import { cn } from "@/shared/lib/utils";

const RESULTS = [
  { file: "orders/service.py", method: "Semantic search", score: 94 },
  { file: "retry_handler.py", method: "Symbol graph", score: 89 },
  { file: "idempotency.py", method: "Hybrid retrieval", score: 87 },
  { file: "PR #156", method: "Git history", score: 81 },
  { file: "issue #482", method: "Reranked", score: 76 },
];

const row: Variants = {
  hidden: { opacity: 0, x: -8 },
  show: { opacity: 1, x: 0, transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] } },
};

/** Real-shaped Lumora surface — the actual retrieval result list a query
 * produces, ranked with the method that surfaced each hit — standing in for
 * a generic "pipeline stages" icon row. */
export function RetrievalConsolePanel() {
  const reducedMotion = useReducedMotion();

  function handlePointerMove(event: PointerEvent<HTMLDivElement>) {
    const node = event.currentTarget;
    const rect = node.getBoundingClientRect();
    node.style.setProperty("--sx", `${((event.clientX - rect.left) / rect.width) * 100}%`);
    node.style.setProperty("--sy", `${((event.clientY - rect.top) / rect.height) * 100}%`);
  }

  return (
    <motion.div
      initial={reducedMotion ? undefined : "hidden"}
      whileInView={reducedMotion ? undefined : "show"}
      viewport={{ once: true, margin: "-80px" }}
      variants={reducedMotion ? undefined : { show: { transition: { staggerChildren: 0.07 } } }}
      onPointerMove={handlePointerMove}
      className="spotlight border-border bg-card/60 w-full overflow-hidden rounded-md border"
    >
      <div className="border-border bg-secondary/30 flex items-center gap-2 border-b px-4 py-2.5">
        <span className="text-muted-foreground font-mono text-xs">query</span>
        <span className="text-foreground font-mono text-xs">
          "why does payment retry create duplicate orders?"
        </span>
      </div>

      <div className="flex flex-col gap-1 p-3">
        {RESULTS.map((result) => (
          <motion.div
            key={result.file}
            variants={reducedMotion ? undefined : row}
            className="hover:bg-secondary/40 flex items-center gap-3 rounded-md px-2.5 py-2 transition-colors"
          >
            <span className="text-foreground/90 min-w-0 flex-1 truncate font-mono text-xs">
              {result.file}
            </span>
            <span className="text-muted-foreground hidden shrink-0 font-mono text-[10px] tracking-wide uppercase sm:inline">
              {result.method}
            </span>
            <div className="bg-secondary relative h-1 w-14 shrink-0 overflow-hidden rounded-full">
              <div
                className={cn(
                  "bg-primary absolute inset-y-0 left-0 rounded-full",
                  reducedMotion ? "" : "transition-[width] duration-700 ease-out",
                )}
                style={{ width: `${result.score}%` }}
              />
            </div>
            <span className="text-muted-foreground w-7 shrink-0 text-right font-mono text-[10px]">
              {result.score}
            </span>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
