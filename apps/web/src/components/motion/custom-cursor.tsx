import { motion, useMotionValue, useSpring } from "framer-motion";
import { useEffect, useState } from "react";

import { useReducedMotion } from "@/shared/hooks/use-reduced-motion";
import { cn } from "@/shared/lib/utils";

const HOVER_SELECTOR = "a, button, [data-cursor-hover]";
const TARGET_PAD = 6;

const CORNERS = [
  "top-0 left-0 border-t border-l",
  "top-0 right-0 border-t border-r",
  "bottom-0 left-0 border-b border-l",
  "bottom-0 right-0 border-b border-r",
] as const;

interface TargetBox {
  left: number;
  top: number;
  width: number;
  height: number;
}

/** Precision crosshair that snaps into corner brackets around whatever
 * interactive element it lands on — a dev-tools "inspect element" motif
 * instead of the generic ring-and-dot cursor. Landing-only, fine-pointer
 * devices only — native cursor is left untouched on touch and under
 * reduced motion. */
export function CustomCursor() {
  const reducedMotion = useReducedMotion();
  const [finePointer, setFinePointer] = useState(() => {
    if (typeof window === "undefined") return false;
    return window.matchMedia("(pointer: fine)").matches;
  });
  const [target, setTarget] = useState<TargetBox | null>(null);
  const enabled = finePointer && !reducedMotion;

  const x = useMotionValue(-100);
  const y = useMotionValue(-100);
  const springX = useSpring(x, { stiffness: 700, damping: 45, mass: 0.4 });
  const springY = useSpring(y, { stiffness: 700, damping: 45, mass: 0.4 });

  useEffect(() => {
    if (typeof window === "undefined") return;
    const fine = window.matchMedia("(pointer: fine)");
    const handleChange = (event: MediaQueryListEvent) => setFinePointer(event.matches);
    fine.addEventListener("change", handleChange);
    return () => fine.removeEventListener("change", handleChange);
  }, []);

  useEffect(() => {
    if (!enabled) return;

    document.documentElement.classList.add("cursor-none-custom");

    function handleMove(event: PointerEvent) {
      x.set(event.clientX);
      y.set(event.clientY);
    }
    function handleOver(event: PointerEvent) {
      const el = (event.target as Element | null)?.closest<HTMLElement>(HOVER_SELECTOR);
      if (!el) {
        setTarget(null);
        return;
      }
      const rect = el.getBoundingClientRect();
      setTarget({
        left: rect.left - TARGET_PAD,
        top: rect.top - TARGET_PAD,
        width: rect.width + TARGET_PAD * 2,
        height: rect.height + TARGET_PAD * 2,
      });
    }

    window.addEventListener("pointermove", handleMove);
    window.addEventListener("pointerover", handleOver);
    return () => {
      document.documentElement.classList.remove("cursor-none-custom");
      window.removeEventListener("pointermove", handleMove);
      window.removeEventListener("pointerover", handleOver);
    };
  }, [enabled, x, y]);

  if (!enabled) return null;

  const hovering = Boolean(target);

  return (
    <>
      <motion.div
        aria-hidden
        className="pointer-events-none fixed top-0 left-0 z-[70]"
        style={{ x: springX, y: springY, translateX: "-50%", translateY: "-50%" }}
        animate={{ opacity: hovering ? 0 : 1, scale: hovering ? 0.5 : 1 }}
        transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
      >
        <span className="bg-primary absolute top-1/2 left-1/2 h-px w-3 -translate-x-1/2 -translate-y-1/2" />
        <span className="bg-primary absolute top-1/2 left-1/2 h-3 w-px -translate-x-1/2 -translate-y-1/2" />
        <span className="border-primary absolute top-1/2 left-1/2 size-1 -translate-x-1/2 -translate-y-1/2 rounded-full border" />
      </motion.div>

      <motion.div
        aria-hidden
        className="pointer-events-none fixed z-[70]"
        animate={{
          left: target?.left ?? 0,
          top: target?.top ?? 0,
          width: target?.width ?? 0,
          height: target?.height ?? 0,
          opacity: hovering ? 1 : 0,
        }}
        transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
      >
        {CORNERS.map((cornerClass) => (
          <span
            key={cornerClass}
            className={cn("border-primary absolute size-2.5", cornerClass)}
          />
        ))}
      </motion.div>
    </>
  );
}
