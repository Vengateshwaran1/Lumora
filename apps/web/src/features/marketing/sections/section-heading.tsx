import { useRef, type ReactNode } from "react";

import { useScrollReveal } from "@/components/motion/use-scroll-reveal";
import { cn } from "@/shared/lib/utils";

interface SectionHeadingProps {
  /** Two-digit section index shown in the mono label row, e.g. "01". */
  index?: string;
  eyebrow?: string;
  title: ReactNode;
  subtitle?: ReactNode;
  align?: "left" | "center";
}

/** Mono index/label row + oversized display-serif title — the data-dense
 * replacement for the old centered uppercase-eyebrow pattern shared by
 * every section. */
export function SectionHeading({
  index,
  eyebrow,
  title,
  subtitle,
  align = "left",
}: SectionHeadingProps) {
  const ref = useRef<HTMLDivElement>(null);
  useScrollReveal(ref, "[data-reveal]");
  const centered = align === "center";

  return (
    <div
      ref={ref}
      className={cn("flex flex-col gap-5", centered ? "items-center text-center" : "items-start text-left")}
    >
      {index || eyebrow ? (
        <div
          data-reveal
          className="text-muted-foreground font-mono flex items-center gap-3 text-xs"
        >
          {index ? <span className="text-primary">{index}</span> : null}
          <span className="bg-border h-px w-8" aria-hidden />
          {eyebrow ? <span className="tracking-wide">{eyebrow}</span> : null}
        </div>
      ) : null}
      <h2
        data-reveal
        className="text-foreground font-display max-w-3xl text-4xl leading-[1.05] font-medium tracking-tight sm:text-5xl lg:text-[3.4rem]"
      >
        {title}
      </h2>
      {subtitle ? (
        <p data-reveal className="text-muted-foreground max-w-xl text-base sm:text-lg">
          {subtitle}
        </p>
      ) : null}
    </div>
  );
}
