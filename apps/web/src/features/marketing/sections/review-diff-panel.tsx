import { motion, type Variants } from "framer-motion";
import { CheckCircle2, MessageSquare, XCircle } from "lucide-react";
import type { PointerEvent } from "react";

import { useReducedMotion } from "@/shared/hooks/use-reduced-motion";
import { cn } from "@/shared/lib/utils";

const DIFF = [
  { type: "context" as const, code: "def commit_order(charge: Charge) -> Order:" },
  { type: "del" as const, code: "    order = Order.create(charge)" },
  { type: "add" as const, code: "    if idempotency.seen(charge.key):" },
  { type: "add" as const, code: "        return idempotency.existing(charge.key)" },
  { type: "add" as const, code: "    order = Order.create(charge)" },
  { type: "context" as const, code: "    return order" },
];

const row: Variants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { duration: 0.3 } },
};

/** Real-shaped Lumora surface — a diff plus a reviewer's comment and the
 * approval gate — standing in for the old icon-chain "AI proposes → human
 * reviews → approves" row. */
export function ReviewDiffPanel() {
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
      variants={reducedMotion ? undefined : { show: { transition: { staggerChildren: 0.05 } } }}
      onPointerMove={handlePointerMove}
      className="spotlight border-border bg-card/60 w-full overflow-hidden rounded-md border"
    >
      <div className="border-border bg-secondary/30 flex items-center justify-between border-b px-4 py-2.5">
        <span className="text-muted-foreground font-mono text-xs">
          orders/service.py <span className="text-muted-foreground/50">· PR #156</span>
        </span>
        <span className="text-success font-mono text-[11px]">+3 −1</span>
      </div>

      <div className="py-2">
        {DIFF.map((line, index) => (
          <motion.div
            key={index}
            variants={reducedMotion ? undefined : row}
            className={cn(
              "flex items-start gap-3 px-4 py-1 font-mono text-xs whitespace-pre",
              line.type === "add" && "bg-success/[0.07] text-success",
              line.type === "del" && "bg-destructive/[0.07] text-destructive line-through",
              line.type === "context" && "text-foreground/70",
            )}
          >
            <span className="w-3 shrink-0 select-none">
              {line.type === "add" ? "+" : line.type === "del" ? "−" : " "}
            </span>
            {line.code}
          </motion.div>
        ))}
      </div>

      <div className="border-border flex items-start gap-3 border-t px-4 py-3">
        <div className="bg-approval/15 text-approval flex size-6 shrink-0 items-center justify-center rounded-full">
          <MessageSquare className="size-3.5" />
        </div>
        <p className="text-foreground text-xs leading-relaxed">
          <span className="font-medium">Reviewer:</span> idempotency check looks right — approving
          before this ships to the retry queue.
        </p>
      </div>

      <div className="border-border flex items-center gap-2 border-t px-4 py-3">
        <span className="text-approval bg-approval/10 border-approval/30 flex items-center gap-1.5 rounded-sm border px-2.5 py-1 text-xs font-medium">
          <CheckCircle2 className="size-3.5" />
          Approved
        </span>
        <span className="text-muted-foreground flex items-center gap-1.5 rounded-sm border border-transparent px-2.5 py-1 text-xs">
          <XCircle className="size-3.5" />
          Request changes
        </span>
      </div>
    </motion.div>
  );
}
