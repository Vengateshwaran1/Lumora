import { motion, useInView } from "framer-motion";
import { useRef, type ReactNode } from "react";

import { useReducedMotion } from "@/shared/hooks/use-reduced-motion";

interface RevealProps {
  children: ReactNode;
  className?: string;
  delay?: number;
  y?: number;
  once?: boolean;
}

/** Fade + rise reveal on scroll-into-view. App-weight (200ms) by default —
 * for landing-page cinematic timing, pass a larger `delay`/duration via
 * className overrides or use GSAP ScrollTrigger directly instead. */
export function Reveal({ children, className, delay = 0, y = 12, once = true }: RevealProps) {
  const ref = useRef(null);
  const inView = useInView(ref, { once, margin: "-10% 0px" });
  const reducedMotion = useReducedMotion();

  return (
    <motion.div
      ref={ref}
      className={className}
      initial={reducedMotion ? false : { opacity: 0, y }}
      animate={inView ? { opacity: 1, y: 0 } : reducedMotion ? { opacity: 1 } : { opacity: 0, y }}
      transition={{ duration: 0.3, delay, ease: [0.16, 1, 0.3, 1] }}
    >
      {children}
    </motion.div>
  );
}
