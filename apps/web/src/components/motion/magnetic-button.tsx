import { motion, useMotionTemplate, useMotionValue, useSpring } from "framer-motion";
import { type MouseEvent, type ReactNode, useRef, useState } from "react";

import { useReducedMotion } from "@/shared/hooks/use-reduced-motion";
import { cn } from "@/shared/lib/utils";

interface MagneticButtonProps {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
  strength?: number;
}

/** Button that leans toward the cursor within its bounds and carries a soft
 * glow that trails the pointer. Landing-page flourish — not used inside the
 * application shell. */
export function MagneticButton({
  children,
  className,
  onClick,
  strength = 0.35,
}: MagneticButtonProps) {
  const ref = useRef<HTMLButtonElement>(null);
  const reducedMotion = useReducedMotion();
  const [hovering, setHovering] = useState(false);

  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const springX = useSpring(x, { stiffness: 250, damping: 20, mass: 0.4 });
  const springY = useSpring(y, { stiffness: 250, damping: 20, mass: 0.4 });

  const gx = useMotionValue(50);
  const gy = useMotionValue(50);
  const glow = useMotionTemplate`radial-gradient(120px circle at ${gx}% ${gy}%, rgba(255, 255, 255, 0.35), transparent 70%)`;

  function handleMouseMove(event: MouseEvent<HTMLButtonElement>) {
    if (reducedMotion || !ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    x.set((event.clientX - rect.left - rect.width / 2) * strength);
    y.set((event.clientY - rect.top - rect.height / 2) * strength);
    gx.set(((event.clientX - rect.left) / rect.width) * 100);
    gy.set(((event.clientY - rect.top) / rect.height) * 100);
  }

  function handleMouseLeave() {
    x.set(0);
    y.set(0);
    setHovering(false);
  }

  return (
    <motion.button
      ref={ref}
      type="button"
      onClick={onClick}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setHovering(true)}
      onMouseLeave={handleMouseLeave}
      style={reducedMotion ? undefined : { x: springX, y: springY }}
      whileTap={reducedMotion ? undefined : { scale: 0.96 }}
      className={cn(
        "relative overflow-hidden ring-1 ring-white/15 ring-inset [&_svg]:transition-transform [&_svg]:duration-300 hover:[&_svg]:translate-x-0.5",
        className,
      )}
    >
      <span
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-1/2 rounded-t-[inherit] bg-gradient-to-b from-white/20 to-transparent"
      />
      {!reducedMotion ? (
        <motion.span
          aria-hidden
          className="pointer-events-none absolute inset-0 rounded-[inherit]"
          style={{ background: glow }}
          animate={{ opacity: hovering ? 1 : 0 }}
          transition={{ duration: 0.2 }}
        />
      ) : null}
      <span className="relative z-10 flex items-center gap-1.5">{children}</span>
    </motion.button>
  );
}
