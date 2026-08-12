import { animate, useInView } from "framer-motion";
import { useEffect, useRef, useState } from "react";

import { useReducedMotion } from "@/shared/hooks/use-reduced-motion";

interface CounterProps {
  to: number;
  duration?: number;
  prefix?: string;
  suffix?: string;
  className?: string;
}

/** Ticks up from 0 → `to` once the element scrolls into view. Landing-page
 * only — real app numbers (repo/chunk counts) render as plain text, never
 * animated, since they're live data rather than a narrative reveal. */
export function Counter({ to, duration = 1.4, prefix = "", suffix = "", className }: CounterProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-10%" });
  const reducedMotion = useReducedMotion();
  const [value, setValue] = useState(reducedMotion ? to : 0);

  useEffect(() => {
    if (!inView || reducedMotion) return;
    const controls = animate(0, to, {
      duration,
      ease: [0.16, 1, 0.3, 1],
      onUpdate: (latest) => setValue(Math.round(latest)),
    });
    return () => controls.stop();
  }, [inView, to, duration, reducedMotion]);

  return (
    <span ref={ref} className={className}>
      {prefix}
      {value.toLocaleString()}
      {suffix}
    </span>
  );
}
