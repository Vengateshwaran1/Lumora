import type { ReactNode } from "react";

import { Spotlight } from "@/components/motion/spotlight";
import { cn } from "@/shared/lib/utils";

interface PremiumCardProps {
  children: ReactNode;
  className?: string;
  /** "shine" — diagonal hover sweep (default, cheapest, use for most
   * clickable surfaces). "spotlight" — cursor-tracking glow, reserve for a
   * few featured surfaces (hero tiles, empty-state CTAs). "ring" — 1px
   * gradient-ring border, reserve for the single most prominent surface on
   * a page (e.g. the connect-repo form). */
  accent?: "shine" | "spotlight" | "ring";
}

export function PremiumCard({ children, className, accent = "shine" }: PremiumCardProps) {
  if (accent === "spotlight") {
    return (
      <Spotlight
        className={cn("surface-card overflow-hidden rounded-[var(--radius-lg)]", className)}
      >
        {children}
      </Spotlight>
    );
  }

  if (accent === "ring") {
    return <div className={cn("surface-card ring-gradient", className)}>{children}</div>;
  }

  return <div className={cn("surface-card-interactive", className)}>{children}</div>;
}
