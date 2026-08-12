import { useMotionValueEvent, useScroll, useTransform, motion } from "framer-motion";
import { useState, type RefObject } from "react";

import { useReducedMotion } from "@/shared/hooks/use-reduced-motion";
import { cn } from "@/shared/lib/utils";

/** Tracks scroll progress through a section (entrance → settle) and derives
 * a discrete "which step is active" index. Powers the traveling-dot line
 * shared by the step-chain sections (context pipeline, issue→plan, sandbox
 * verify, human approval) so scrolling through each row feels alive instead
 * of a one-shot fade. Under reduced motion, every step reports active
 * immediately and the line renders fully filled/static. */
export function useScrollTrack(ref: RefObject<HTMLElement | null>, steps: number) {
  const reducedMotion = useReducedMotion();
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start 75%", "center 45%"] });
  const [activeIndex, setActiveIndex] = useState(reducedMotion ? steps - 1 : -1);

  useMotionValueEvent(scrollYProgress, "change", (v) => {
    if (reducedMotion) return;
    setActiveIndex(Math.min(steps - 1, Math.floor(v * steps)));
  });

  return { scrollYProgress, activeIndex, reducedMotion };
}

interface ScrollTrackLineProps {
  progress: ReturnType<typeof useScrollTrack>["scrollYProgress"];
  reducedMotion?: boolean;
  className?: string;
}

/** Absolute connecting line for a step-chain row: a dashed idle track, a
 * primary-colored fill that grows with scroll, and a small glowing dot
 * riding the leading edge. Landing-only. */
export function ScrollTrackLine({ progress, reducedMotion, className }: ScrollTrackLineProps) {
  const dotLeft = useTransform(progress, (v) => `${Math.min(Math.max(v, 0), 1) * 100}%`);

  return (
    <div
      className={cn(
        "border-border absolute top-1/2 right-0 left-0 hidden h-px -translate-y-1/2 border-t border-dashed sm:block",
        className,
      )}
      aria-hidden
    >
      <motion.div
        className="bg-primary absolute inset-y-0 left-0 h-px origin-left"
        style={reducedMotion ? { scaleX: 1 } : { scaleX: progress }}
      />
      {reducedMotion ? null : (
        <motion.div
          className="bg-primary absolute top-1/2 size-2 -translate-x-1/2 -translate-y-1/2 rounded-full shadow-[0_0_10px_rgba(var(--lum-primary-rgb),0.7)]"
          style={{ left: dotLeft }}
        />
      )}
    </div>
  );
}
