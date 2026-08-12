import { motion, useScroll, useSpring } from "framer-motion";

/** Thin copper progress bar pinned to the top of the viewport, tracking
 * whole-page scroll. Landing-page only. */
export function ScrollProgress() {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, { stiffness: 200, damping: 40, restDelta: 0.001 });

  return (
    <motion.div
      style={{ scaleX }}
      className="bg-primary fixed inset-x-0 top-0 z-50 h-[2px] origin-left"
      aria-hidden
    />
  );
}
