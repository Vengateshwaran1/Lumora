import { ArrowRight } from "lucide-react";
import { useRef } from "react";
import { useNavigate } from "react-router-dom";

import { AnimatedWords } from "@/components/motion/animated-words";
import { MagneticButton } from "@/components/motion/magnetic-button";
import { useScrollReveal } from "@/components/motion/use-scroll-reveal";

export function FinalCtaSection() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  useScrollReveal(sectionRef, "[data-reveal]");

  return (
    <section
      ref={sectionRef}
      className="border-border/70 relative flex flex-col items-center gap-8 overflow-hidden border-t px-6 py-40 text-center sm:px-10"
    >
      <div className="blueprint-grid absolute inset-0 opacity-40" aria-hidden />

      <div className="relative z-10 flex flex-col items-center gap-8">
        <h2 className="text-foreground font-display flex flex-wrap items-center justify-center gap-x-4 gap-y-2 text-4xl font-medium tracking-tight sm:text-6xl">
          <AnimatedWords text="Understand. Plan. Build. Verify." />
        </h2>
        <p data-reveal className="text-muted-foreground max-w-md text-sm sm:text-base">
          Software engineering, with context — for every repository your team ships.
        </p>
        <div data-reveal className="ring-gradient rounded-full p-[1px]">
          <MagneticButton
            onClick={() => void navigate("/app")}
            className="text-primary-foreground flex items-center gap-1.5 rounded-full bg-[image:var(--primary-gradient)] px-7 py-3.5 text-sm font-medium shadow-[var(--shadow-glow-primary)] transition-shadow duration-200 hover:shadow-[var(--shadow-glow-primary-hover)]"
          >
            Launch Lumora
            <ArrowRight className="size-4" />
          </MagneticButton>
        </div>
      </div>
    </section>
  );
}
