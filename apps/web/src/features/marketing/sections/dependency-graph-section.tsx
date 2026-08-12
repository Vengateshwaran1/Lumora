import { useMotionValueEvent, useScroll, motion } from "framer-motion";
import { useRef, useState } from "react";

import { useReducedMotion } from "@/shared/hooks/use-reduced-motion";
import { cn } from "@/shared/lib/utils";

import { SectionBand } from "./section-band";
import { SectionHeading } from "./section-heading";

const NODES = [
  { id: "service", label: "service.py", x: 50, y: 20 },
  { id: "retry", label: "retry_handler.py", x: 18, y: 45 },
  { id: "idempotency", label: "idempotency.py", x: 82, y: 45 },
  { id: "orders", label: "orders/service.py", x: 50, y: 55 },
  { id: "db", label: "db.py", x: 20, y: 82 },
  { id: "webhooks", label: "webhooks/github.py", x: 80, y: 82 },
];

const EDGES: [string, string][] = [
  ["service", "retry"],
  ["service", "idempotency"],
  ["service", "orders"],
  ["orders", "db"],
  ["retry", "webhooks"],
];

function nodeById(id: string) {
  return NODES.find((node) => node.id === id)!;
}

export function DependencyGraphSection() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const reducedMotion = useReducedMotion();
  const [hovered, setHovered] = useState<string | null>(null);
  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ["start 70%", "center 40%"],
  });
  const [revealCount, setRevealCount] = useState(reducedMotion ? EDGES.length : 0);

  useMotionValueEvent(scrollYProgress, "change", (v) => {
    if (reducedMotion) return;
    setRevealCount(Math.round(Math.min(Math.max(v, 0), 1) * EDGES.length));
  });

  const revealedNodeIds = new Set(EDGES.slice(0, revealCount).flat());
  const settled = revealCount >= EDGES.length;

  return (
    <SectionBand grid>
      <div ref={sectionRef} className="grid gap-12 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)] lg:items-center lg:gap-16">
        <SectionHeading
          index="03"
          eyebrow="Symbol graph"
          title="Understand the system, not just the file."
          subtitle="Lumora maps how files, symbols, and modules actually depend on each other — hover a node to trace its edges."
        />

        <div className="border-border bg-card/60 relative aspect-[16/11] w-full rounded-md border">
        <svg viewBox="0 0 100 100" className="h-full w-full" preserveAspectRatio="xMidYMid meet">
          {EDGES.map(([from, to], index) => {
            const a = nodeById(from);
            const b = nodeById(to);
            const active = hovered === from || hovered === to;
            const revealed = index < revealCount;
            return (
              <line
                key={`${from}-${to}`}
                x1={a.x}
                y1={a.y}
                x2={b.x}
                y2={b.y}
                pathLength={1}
                strokeDasharray={1}
                strokeDashoffset={revealed ? 0 : 1}
                strokeWidth={active ? 0.8 : 0.4}
                className={cn(
                  "transition-[stroke-dashoffset,stroke] duration-500 ease-out",
                  active ? "stroke-primary" : "stroke-border",
                )}
              />
            );
          })}
        </svg>

        {NODES.map((node) => {
          const revealed = reducedMotion || revealedNodeIds.has(node.id);
          const isRoot = node.id === "service";
          return (
            <motion.button
              key={node.id}
              type="button"
              onMouseEnter={() => setHovered(node.id)}
              onMouseLeave={() => setHovered(null)}
              initial={false}
              animate={{ opacity: revealed ? 1 : 0, scale: revealed ? 1 : 0.8 }}
              transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
              whileHover={reducedMotion ? undefined : { scale: 1.08 }}
              className={cn(
                "text-foreground absolute -translate-x-1/2 -translate-y-1/2 rounded-md border px-2 py-1 font-mono text-[10px] whitespace-nowrap shadow-sm transition-shadow duration-500",
                isRoot && settled
                  ? "border-primary/50 bg-card shadow-[0_0_16px_rgba(var(--lum-primary-rgb),0.3)]"
                  : "border-engineering/30 bg-card",
              )}
              style={{ left: `${node.x}%`, top: `${node.y}%` }}
            >
              {node.label}
            </motion.button>
          );
        })}
        </div>
      </div>
    </SectionBand>
  );
}
