import { useGSAP } from "@gsap/react";
import { ArrowRight } from "lucide-react";
import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { AnimatedWords } from "@/components/motion/animated-words";
import { Aurora } from "@/components/motion/aurora";
import { CustomCursor } from "@/components/motion/custom-cursor";
import { MagneticButton } from "@/components/motion/magnetic-button";
import { ScrollProgress } from "@/components/motion/scroll-progress";
import { TiltCard } from "@/components/motion/tilt-card";
import { useReducedMotion } from "@/shared/hooks/use-reduced-motion";
import { ensureGsapRegistered, gsap } from "@/shared/lib/gsap";

import { ContextThread } from "./context-thread";
import { EngineeringInterfaceDemo } from "./hero/engineering-interface-demo";
import { MarketingFooter } from "./marketing-footer";
import { MarketingNav } from "./marketing-nav";
import { Preloader } from "./preloader";
import { AgentOrchestrationSection } from "./sections/agent-orchestration-section";
import { ContextPipelineSection } from "./sections/context-pipeline-section";
import { DependencyGraphSection } from "./sections/dependency-graph-section";
import { EngineeringMemorySection } from "./sections/engineering-memory-section";
import { FinalCtaSection } from "./sections/final-cta-section";
import { FragmentedKnowledgeSection } from "./sections/fragmented-knowledge-section";
import { HumanApprovalSection } from "./sections/human-approval-section";
import { IssueToPlanSection } from "./sections/issue-to-plan-section";
import { SandboxVerifySection } from "./sections/sandbox-verify-section";
import { TechMarquee } from "./tech-marquee";

export function LandingPage() {
  const navigate = useNavigate();
  const reducedMotion = useReducedMotion();
  const heroRef = useRef<HTMLElement>(null);
  const [heroReady, setHeroReady] = useState(false);
  const [headlinePlay, setHeadlinePlay] = useState(false);

  // Load choreography — plays once the preloader stops gating the page.
  useGSAP(
    () => {
      if (!heroReady || !heroRef.current || reducedMotion) return;
      ensureGsapRegistered();

      const badge = gsap.utils.toArray<HTMLElement>("[data-hero-badge]", heroRef.current);
      const subhead = gsap.utils.toArray<HTMLElement>("[data-hero-subhead]", heroRef.current);
      const ctas = gsap.utils.toArray<HTMLElement>("[data-hero-ctas]", heroRef.current);
      const demo = gsap.utils.toArray<HTMLElement>("[data-hero-demo]", heroRef.current);

      gsap.set([...badge, ...subhead, ...ctas, ...demo], { opacity: 0, y: 16 });

      gsap
        .timeline({ defaults: { ease: "power3.out", duration: 0.7 } })
        .to(badge, { opacity: 1, y: 0 })
        .call(() => setHeadlinePlay(true), [], "-=0.35")
        .to(subhead, { opacity: 1, y: 0 }, "+=0.5")
        .to(ctas, { opacity: 1, y: 0 }, "-=0.45")
        .to(demo, { opacity: 1, y: 0, duration: 0.9 }, "-=0.3");
    },
    { scope: heroRef, dependencies: [heroReady, reducedMotion] },
  );

  // Scroll parallax — hero copy and demo drift at different rates as the
  // hero scrolls out of view.
  useGSAP(
    () => {
      if (!heroRef.current || reducedMotion) return;
      ensureGsapRegistered();

      const scrollOpts = { trigger: heroRef.current, start: "top top", end: "bottom top", scrub: true };
      gsap.to("[data-hero-copy]", { yPercent: -14, ease: "none", scrollTrigger: scrollOpts });
      gsap.to("[data-hero-demo]", { yPercent: -5, ease: "none", scrollTrigger: scrollOpts });
    },
    { scope: heroRef, dependencies: [reducedMotion] },
  );

  return (
    <div className="bg-background grain relative min-h-svh overflow-x-clip">
      <CustomCursor />
      <Preloader onDone={() => setHeroReady(true)} />
      <ScrollProgress />
      <MarketingNav />
      <ContextThread />

      <section
        id="hero"
        ref={heroRef}
        className="relative flex min-h-svh flex-col items-center justify-center px-6 pt-24 pb-16 sm:px-10"
      >
        <Aurora variant="landing" />

        <div
          data-hero-copy
          className="relative z-10 mx-auto flex max-w-4xl flex-col items-center text-center"
        >
          <span
            data-hero-badge
            className="border-border text-muted-foreground mb-6 flex items-center gap-2 rounded-full border px-3 py-1 font-mono text-xs"
          >
            <span className="bg-primary size-1.5 rounded-full" aria-hidden />
            AI Engineering Intelligence Platform
          </span>
          <h1 className="text-foreground font-display text-5xl leading-[1.05] font-medium tracking-tight sm:text-7xl">
            <AnimatedWords text="Software engineering," className="block" play={headlinePlay} />
            <AnimatedWords
              text="with context."
              className="block"
              staggerDelay={0.07}
              play={headlinePlay}
            />
          </h1>
          <p data-hero-subhead className="text-muted-foreground mt-6 max-w-xl text-base sm:text-lg">
            Lumora understands your code, dependencies, engineering history, and decisions — giving
            AI agents the context to build software you can trust.
          </p>

          <div data-hero-ctas className="mt-9 flex flex-col items-center gap-3 sm:flex-row">
            <MagneticButton
              onClick={() => void navigate("/app")}
              className="text-primary-foreground flex items-center gap-1.5 rounded-full bg-[image:var(--primary-gradient)] px-6 py-3 text-sm font-medium shadow-[var(--shadow-glow-primary)] transition-shadow duration-200 hover:shadow-[var(--shadow-glow-primary-hover)]"
            >
              Launch Lumora
              <ArrowRight className="size-4" />
            </MagneticButton>
            <a
              href="#how-it-works"
              className="border-border text-foreground hover:bg-secondary/50 rounded-full border px-6 py-3 text-sm font-medium transition-colors"
            >
              Explore the system
            </a>
          </div>
        </div>

        <div data-hero-demo className="relative z-10 mt-16 w-full max-w-4xl">
          <TiltCard intensity={4} className="rounded-2xl">
            <EngineeringInterfaceDemo />
          </TiltCard>
        </div>
      </section>

      <div className="border-border/60 relative border-y py-6">
        <TechMarquee />
      </div>

      <div id="how-it-works" className="relative">
        <FragmentedKnowledgeSection />
        <ContextPipelineSection />
        <DependencyGraphSection />
      </div>

      <div id="issue-to-plan" className="relative">
        <IssueToPlanSection />
      </div>

      <div id="agents" className="relative">
        <AgentOrchestrationSection />
        <SandboxVerifySection />
      </div>

      <div id="approval" className="relative">
        <HumanApprovalSection />
      </div>
      <div id="memory" className="relative">
        <EngineeringMemorySection />
      </div>
      <div id="cta" className="relative">
        <FinalCtaSection />
      </div>

      <MarketingFooter />
    </div>
  );
}
