import { useGSAP } from "@gsap/react";
import { motion } from "framer-motion";
import { useRef } from "react";

import { useReducedMotion } from "@/shared/hooks/use-reduced-motion";
import { ensureGsapRegistered, gsap } from "@/shared/lib/gsap";

interface AuroraProps {
  /** "landing" = full atmospheric field (heavy, slow-moving blurred forms).
   * "ambient" = a faint trace for use inside the application shell — never
   * the default there; most app surfaces should pass none at all. */
  variant?: "landing" | "ambient";
  className?: string;
}

const BLOBS = [
  { color: "var(--primary)", top: "-10%", left: "5%", size: "42vw", duration: 26, delay: 0 },
  { color: "var(--engineering)", top: "20%", left: "60%", size: "38vw", duration: 32, delay: 3 },
  { color: "var(--approval)", top: "55%", left: "10%", size: "30vw", duration: 30, delay: 6 },
  { color: "var(--ai-activity)", top: "65%", left: "55%", size: "34vw", duration: 28, delay: 2 },
];

/** Obsidian + copper atmospheric field — large blurred forms drifting
 * slowly, with grain overlay. Heavy on the landing page, essentially absent
 * inside the app (only "ambient" opacity, used rarely). */
export function Aurora({ variant = "landing", className }: AuroraProps) {
  const reducedMotion = useReducedMotion();
  const isAmbient = variant === "ambient";
  const rootRef = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      if (isAmbient || reducedMotion || !rootRef.current?.parentElement) return;
      ensureGsapRegistered();

      gsap.to(rootRef.current, {
        yPercent: -10,
        ease: "none",
        scrollTrigger: {
          trigger: rootRef.current.parentElement,
          start: "top top",
          end: "bottom top",
          scrub: true,
        },
      });
    },
    { scope: rootRef, dependencies: [isAmbient, reducedMotion] },
  );

  return (
    <div
      ref={rootRef}
      aria-hidden
      className={`pointer-events-none absolute inset-0 overflow-hidden ${isAmbient ? "opacity-[0.06]" : "opacity-90 dark:opacity-100"} ${className ?? ""}`}
    >
      {BLOBS.map((blob, index) => (
        <motion.div
          key={index}
          className="absolute rounded-full blur-[120px]"
          style={{
            top: blob.top,
            left: blob.left,
            width: blob.size,
            height: blob.size,
            background: blob.color,
            opacity: isAmbient ? 0.5 : 0.28,
          }}
          animate={
            reducedMotion
              ? undefined
              : {
                  x: [0, 40, -20, 0],
                  y: [0, -30, 20, 0],
                }
          }
          transition={{
            duration: blob.duration,
            delay: blob.delay,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      ))}
      <div className="bg-[url('data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22120%22 height=%22120%22><filter id=%22n%22><feTurbulence type=%22fractalNoise%22 baseFrequency=%220.9%22 numOctaves=%222%22 stitchTiles=%22stitch%22/></filter><rect width=%22120%22 height=%22120%22 filter=%22url(%23n)%22 opacity=%220.05%22/></svg>')] absolute inset-0 opacity-40 mix-blend-overlay" />
    </div>
  );
}
