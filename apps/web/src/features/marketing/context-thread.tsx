import { motion, useMotionValueEvent, useScroll, useSpring, useTransform } from "framer-motion";
import { useEffect, useState } from "react";

import { useReducedMotion } from "@/shared/hooks/use-reduced-motion";
import { cn } from "@/shared/lib/utils";

const NODES = [
  { id: "hero", label: "Signal" },
  { id: "how-it-works", label: "Context" },
  { id: "issue-to-plan", label: "Plan" },
  { id: "agents", label: "Agents" },
  { id: "approval", label: "Approval" },
  { id: "memory", label: "Memory" },
  { id: "cta", label: "Build" },
];

const RAIL_HEIGHT = 224;

interface Tick {
  id: string;
  label: string;
  fraction: number;
}

/** Left-gutter scroll telemetry — a ruler-style rail with a marker that
 * tracks the live scroll fraction (not a remembered max), so it reduces
 * again on scroll-up, plus a mono %/section readout. Visualizes Lumora's
 * own metaphor (position within accumulated engineering context) as a
 * measurement instrument rather than a generic progress dot-chain. Desktop
 * only, off under reduced motion. */
export function ContextThread() {
  const reducedMotion = useReducedMotion();
  const { scrollYProgress } = useScroll();
  const smoothProgress = useSpring(scrollYProgress, { stiffness: 260, damping: 40 });
  const markerTop = useTransform(smoothProgress, (v) => `${Math.min(Math.max(v, 0), 1) * 100}%`);

  const [ticks, setTicks] = useState<Tick[]>([]);
  const [fraction, setFraction] = useState(0);

  useEffect(() => {
    if (reducedMotion) return;

    function measure() {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      if (max <= 0) return;
      setTicks(
        NODES.map((node) => {
          const el = document.getElementById(node.id);
          return { id: node.id, label: node.label, fraction: el ? el.offsetTop / max : 0 };
        }),
      );
    }

    measure();
    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
  }, [reducedMotion]);

  useMotionValueEvent(scrollYProgress, "change", (v) => {
    if (reducedMotion) return;
    setFraction(v);
  });

  if (reducedMotion) return null;

  const passedTicks = ticks.filter((tick) => fraction >= tick.fraction - 0.015);
  const activeLabel = (passedTicks[passedTicks.length - 1] ?? ticks[0])?.label ?? NODES[0]!.label;

  return (
    <div className="pointer-events-none fixed top-1/2 left-6 z-40 hidden -translate-y-1/2 xl:block">
      <div className="flex items-center gap-3">
        <div className="relative w-px" style={{ height: RAIL_HEIGHT }}>
          <div className="bg-border absolute inset-0" />
          {ticks.map((tick) => (
            <span
              key={tick.id}
              className={cn(
                "absolute -left-[2.5px] size-[5px] rounded-full transition-colors duration-500",
                fraction >= tick.fraction - 0.015 ? "bg-primary" : "bg-border",
              )}
              style={{ top: `${tick.fraction * 100}%` }}
            />
          ))}
          <motion.div
            className="bg-primary absolute -left-[3px] size-[7px] rounded-full shadow-[0_0_8px_rgba(var(--lum-primary-rgb),0.8)]"
            style={{ top: markerTop }}
          />
        </div>
        <div className="flex flex-col font-mono text-[10px] leading-tight">
          <span className="text-primary tabular-nums">
            {Math.round(fraction * 100)
              .toString()
              .padStart(2, "0")}
            %
          </span>
          <span className="text-muted-foreground tracking-wide uppercase">{activeLabel}</span>
        </div>
      </div>
    </div>
  );
}
