import { motion, type Variants } from "framer-motion";
import type { PointerEvent } from "react";

import { useReducedMotion } from "@/shared/hooks/use-reduced-motion";

const LINES = [
  { n: 84, code: "def process_retry(payment_id: str) -> None:", cite: null },
  { n: 85, code: "    with idempotency_lock(payment_id):", cite: "idempotency.py:41" },
  { n: 86, code: "        if already_processed(payment_id):", cite: "commit a3f91c2" },
  { n: 87, code: "            return", cite: null },
  { n: 88, code: "        charge = retry_queue.consume(payment_id)", cite: "issue #482" },
  { n: 89, code: "        commit_order(charge)", cite: "PR #156" },
];

const row: Variants = {
  hidden: { opacity: 0, x: -8 },
  show: { opacity: 1, x: 0, transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] } },
};

/** Real-shaped Lumora surface — a file with retrieval citations attached to
 * specific lines — standing in for the old fragmented-sources hub/spoke
 * diagram. This is closer to what the product actually shows. */
export function CodeCitationPanel() {
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
      variants={reducedMotion ? undefined : { show: { transition: { staggerChildren: 0.06 } } }}
      onPointerMove={handlePointerMove}
      className="spotlight border-border bg-card/60 w-full overflow-hidden rounded-md border"
    >
      <div className="border-border bg-secondary/30 flex items-center gap-2 border-b px-4 py-2.5">
        <span className="bg-destructive/60 size-2.5 rounded-full" aria-hidden />
        <span className="bg-approval/60 size-2.5 rounded-full" aria-hidden />
        <span className="bg-success/60 size-2.5 rounded-full" aria-hidden />
        <span className="text-muted-foreground font-mono ml-2 text-xs">orders/service.py</span>
      </div>
      <div className="overflow-x-auto py-2">
        {LINES.map((line) => (
          <motion.div
            key={line.n}
            variants={reducedMotion ? undefined : row}
            className={`group flex items-center gap-4 px-4 py-1 font-mono text-xs ${line.cite ? "bg-primary/[0.04]" : ""}`}
          >
            <span className="text-muted-foreground/50 w-5 shrink-0 text-right select-none">
              {line.n}
            </span>
            <span className="text-foreground/90 min-w-0 flex-1 whitespace-pre">{line.code}</span>
            {line.cite ? (
              <span className="border-primary/30 bg-primary/10 text-primary shrink-0 rounded-sm border px-1.5 py-0.5 text-[10px] whitespace-nowrap">
                {line.cite}
              </span>
            ) : null}
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
