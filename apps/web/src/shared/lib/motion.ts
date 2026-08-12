/** JS mirror of the motion tokens in `index.css` (`--dur-*`/`--ease-*`) —
 * Framer Motion reads plain numbers/arrays, not CSS custom properties, so
 * these must be kept numerically identical to the CSS values by hand. */

export const DURATION = {
  fast: 0.15,
  base: 0.22,
  slow: 0.32,
} as const;

/** cubic-bezier(0.16, 1, 0.3, 1) — matches --ease-emph */
export const EASE_EMPHASIZED = [0.16, 1, 0.3, 1] as const;
/** cubic-bezier(0, 0, 0.2, 1) — matches --ease-out */
export const EASE_OUT = [0, 0, 0.2, 1] as const;
/** cubic-bezier(0.4, 0, 1, 1) — matches --ease-in */
export const EASE_IN = [0.4, 0, 1, 1] as const;
