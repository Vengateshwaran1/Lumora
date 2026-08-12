import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";

import { useReducedMotion } from "@/shared/hooks/use-reduced-motion";

const STAGES = ["Context", "Repository", "Knowledge", "Agents", "Verification"];
const STORAGE_KEY = "lumora.seenPreloader";
const STAGE_DURATION_MS = 320;

interface PreloaderProps {
  /** Fires once, the moment the preloader stops gating the page — either
   * immediately (reduced motion / returning visitor, nothing was ever
   * shown) or when the dismiss timer fires. Lets the hero start its own
   * load choreography in sync instead of guessing a fixed delay. */
  onDone?: () => void;
}

/** Branded ~1.6s intro shown once per browser, built from the same grain +
 * copper-gradient + Fraunces-adjacent vocabulary as the rest of the landing
 * page instead of a bare system-font wordmark. Purely decorative — it never
 * gates data loading, and reduced-motion / returning visitors skip it
 * entirely so nothing real is hidden behind it. */
export function Preloader({ onDone }: PreloaderProps) {
  const reducedMotion = useReducedMotion();
  const [visible, setVisible] = useState(() => {
    if (typeof window === "undefined" || reducedMotion) return false;
    return !window.localStorage.getItem(STORAGE_KEY);
  });
  const [stageIndex, setStageIndex] = useState(0);

  useEffect(() => {
    if (!visible) onDone?.();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible]);

  useEffect(() => {
    if (!visible) return;

    window.localStorage.setItem(STORAGE_KEY, "1");

    const stageTimer = window.setInterval(() => {
      setStageIndex((index) => Math.min(index + 1, STAGES.length - 1));
    }, STAGE_DURATION_MS);

    const dismissTimer = window.setTimeout(
      () => setVisible(false),
      STAGE_DURATION_MS * STAGES.length,
    );

    return () => {
      window.clearInterval(stageTimer);
      window.clearTimeout(dismissTimer);
    };
  }, [visible]);

  const progress = ((stageIndex + 1) / STAGES.length) * 100;

  return (
    <AnimatePresence>
      {visible ? (
        <motion.div
          key="preloader"
          initial={{ opacity: 1 }}
          exit={{ opacity: 0, filter: "blur(8px)" }}
          transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
          className="bg-background grain fixed inset-0 z-[100] flex flex-col items-center justify-center gap-5"
        >
          <div
            aria-hidden
            className="absolute size-[40vw] rounded-full opacity-40 blur-[100px]"
            style={{ background: "var(--primary)" }}
          />

          <span className="font-display relative bg-[image:var(--primary-gradient)] bg-clip-text text-4xl font-medium tracking-[0.15em] text-transparent">
            LUMORA
          </span>
          <span className="text-muted-foreground relative text-[11px] tracking-widest uppercase">
            Intelligence initializing
          </span>

          <div className="relative mt-3 flex w-40 flex-col items-center gap-2">
            <div className="bg-border h-px w-full overflow-hidden">
              <div
                className="h-full bg-[image:var(--primary-gradient)] transition-[width] duration-300 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
            <AnimatePresence mode="wait">
              <motion.span
                key={stageIndex}
                initial={reducedMotion ? undefined : { opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={reducedMotion ? undefined : { opacity: 0, y: -4 }}
                transition={{ duration: 0.2 }}
                className="text-primary font-mono text-[11px] tracking-widest"
              >
                {STAGES[stageIndex]}
              </motion.span>
            </AnimatePresence>
          </div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
