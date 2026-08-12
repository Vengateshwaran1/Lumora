import { motion, useMotionTemplate, useMotionValue, useSpring } from "framer-motion";
import { type PointerEvent, type ReactNode } from "react";

import { useReducedMotion } from "@/shared/hooks/use-reduced-motion";
import { cn } from "@/shared/lib/utils";

interface TiltCardProps {
  children: ReactNode;
  className?: string;
  /** Max rotation in degrees. */
  intensity?: number;
}

/** 3D cursor-tracked tilt + a glare highlight that follows the pointer.
 * Landing-page flourish — reserve for a handful of the most prominent
 * cards, not every surface. */
export function TiltCard({ children, className, intensity = 8 }: TiltCardProps) {
  const reducedMotion = useReducedMotion();

  const rx = useMotionValue(0);
  const ry = useMotionValue(0);
  const gx = useMotionValue(50);
  const gy = useMotionValue(50);

  const springRx = useSpring(rx, { stiffness: 300, damping: 30 });
  const springRy = useSpring(ry, { stiffness: 300, damping: 30 });
  const glareBackground = useMotionTemplate`radial-gradient(280px circle at ${gx}% ${gy}%, rgba(var(--lum-primary-rgb), 0.16), transparent 65%)`;

  function handlePointerMove(event: PointerEvent<HTMLDivElement>) {
    if (reducedMotion) return;
    const rect = event.currentTarget.getBoundingClientRect();
    const px = (event.clientX - rect.left) / rect.width;
    const py = (event.clientY - rect.top) / rect.height;
    ry.set((px - 0.5) * intensity * 2);
    rx.set(-(py - 0.5) * intensity * 2);
    gx.set(px * 100);
    gy.set(py * 100);
  }

  function handlePointerLeave() {
    rx.set(0);
    ry.set(0);
  }

  return (
    <motion.div
      onPointerMove={handlePointerMove}
      onPointerLeave={handlePointerLeave}
      style={
        reducedMotion
          ? undefined
          : { rotateX: springRx, rotateY: springRy, transformStyle: "preserve-3d", transformPerspective: 900 }
      }
      className={cn("surface-card-interactive relative", className)}
    >
      {!reducedMotion ? (
        <motion.div
          aria-hidden
          className="pointer-events-none absolute inset-0 z-10 rounded-[inherit]"
          style={{ background: glareBackground }}
        />
      ) : null}
      {children}
    </motion.div>
  );
}
