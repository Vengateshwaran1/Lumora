import { type ReactNode } from "react";

import { cn } from "@/shared/lib/utils";

interface SectionBandProps {
  children: ReactNode;
  className?: string;
  /** Faint hairline grid behind the band — the data-dense alternative to
   * gradient-blob ambience. */
  grid?: boolean;
  innerClassName?: string;
}

/** Full-bleed section shell: a hairline rule spans the full viewport width
 * (no rounded card, no centered container framing the whole section), with
 * content constrained to a left-aligned inner column. Replaces the
 * everything-centered-in-a-card template across the landing page. */
export function SectionBand({ children, className, grid, innerClassName }: SectionBandProps) {
  return (
    <section className={cn("border-border/70 relative border-t", className)}>
      {grid ? <div className="blueprint-grid absolute inset-0 opacity-40" aria-hidden /> : null}
      <div
        className={cn(
          "relative mx-auto max-w-6xl px-6 py-24 sm:px-10 sm:py-32",
          innerClassName,
        )}
      >
        {children}
      </div>
    </section>
  );
}
