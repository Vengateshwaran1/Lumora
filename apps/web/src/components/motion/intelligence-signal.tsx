import { motion } from "framer-motion";

import { useReducedMotion } from "@/shared/hooks/use-reduced-motion";

/** Small animated node-and-edge glyph used to mark "AI is reasoning here" —
 * a slow pulse, not a spinner. Used sparingly (chat, agent activity). */
export function IntelligenceSignal({ className }: { className?: string }) {
  const reducedMotion = useReducedMotion();

  return (
    <span
      className={`relative inline-flex h-4 w-4 items-center justify-center ${className ?? ""}`}
      aria-hidden
    >
      <motion.span
        className="bg-ai-activity absolute h-4 w-4 rounded-full opacity-30"
        animate={reducedMotion ? undefined : { scale: [1, 1.6, 1], opacity: [0.35, 0, 0.35] }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
      />
      <span className="bg-ai-activity relative h-1.5 w-1.5 rounded-full" />
    </span>
  );
}
