import { motion, type Variants } from "framer-motion";

import { useReducedMotion } from "@/shared/hooks/use-reduced-motion";

const container: Variants = {
  hidden: {},
  show: (staggerDelay: number) => ({
    transition: { staggerChildren: staggerDelay, delayChildren: 0.1 },
  }),
};

const word: Variants = {
  hidden: { opacity: 0, y: "0.6em", rotateX: -60, filter: "blur(10px)" },
  show: {
    opacity: 1,
    y: "0em",
    rotateX: 0,
    filter: "blur(0px)",
    transition: { duration: 0.7, ease: [0.16, 1, 0.3, 1] },
  },
};

interface AnimatedWordsProps {
  text: string;
  className?: string;
  staggerDelay?: number;
  play?: boolean;
}

/** Splits `text` on spaces and reveals each word with a 3D flip-up + blur
 * focus, masked by an overflow-hidden wrapper so the motion reads as a
 * rise rather than a slide. Landing-only — cinematic weight, not for the
 * application shell. */
export function AnimatedWords({
  text,
  className,
  staggerDelay = 0.09,
  play,
}: AnimatedWordsProps) {
  const reducedMotion = useReducedMotion();
  const words = text.split(" ");

  if (reducedMotion) return <span className={className}>{text}</span>;

  const controlledProps =
    play === undefined
      ? { whileInView: "show" as const, viewport: { once: true, margin: "-80px" } }
      : { animate: play ? ("show" as const) : ("hidden" as const) };

  return (
    <motion.span
      variants={container}
      custom={staggerDelay}
      initial="hidden"
      {...controlledProps}
      className={className}
      style={{ perspective: 600 }}
    >
      {words.map((w, i) => (
        <span key={`${w}-${i}`} className="inline-block overflow-hidden pb-[0.12em] align-bottom">
          <motion.span variants={word} className="inline-block origin-bottom">
            {w}
            {i < words.length - 1 ? " " : ""}
          </motion.span>
        </span>
      ))}
    </motion.span>
  );
}
