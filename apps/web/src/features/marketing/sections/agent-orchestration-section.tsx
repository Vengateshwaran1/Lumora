import { useGSAP } from "@gsap/react";
import { Bot, Bug, Code2, Search, ShieldCheck, TestTube2, Workflow } from "lucide-react";
import { useRef } from "react";

import { useReducedMotion } from "@/shared/hooks/use-reduced-motion";
import { ensureGsapRegistered, gsap } from "@/shared/lib/gsap";

import { AgentDecisionStream } from "./agent-decision-stream";
import { SectionBand } from "./section-band";
import { SectionHeading } from "./section-heading";

const SUPERVISOR = {
  icon: Workflow,
  label: "Supervisor",
  description: "Coordinates every specialist and owns the final handoff.",
};

const SPOKES = [
  {
    icon: Bot,
    label: "Planner",
    description: "Breaks the issue into ordered, reviewable subtasks.",
  },
  {
    icon: Search,
    label: "Retriever",
    description: "Pulls the exact files, symbols, and history each subtask needs.",
  },
  { icon: Code2, label: "Coder", description: "Drafts the patch scoped to the retrieved context." },
  { icon: TestTube2, label: "Tester", description: "Runs the sandboxed suite against the patch." },
  { icon: Bug, label: "Debugger", description: "Diagnoses failures and revises the patch." },
  {
    icon: ShieldCheck,
    label: "Reviewer",
    description: "Checks the diff before it reaches a human.",
  },
];

const RADIUS = 40;

function spokePosition(index: number) {
  const angle = (index / SPOKES.length) * Math.PI * 2 - Math.PI / 2;
  return {
    x: 50 + RADIUS * Math.cos(angle),
    y: 50 + RADIUS * Math.sin(angle),
  };
}

export function AgentOrchestrationSection() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const reducedMotion = useReducedMotion();

  useGSAP(
    () => {
      if (reducedMotion || !sectionRef.current) return;
      ensureGsapRegistered();

      const cards = gsap.utils.toArray<HTMLElement>("[data-agent-card]", sectionRef.current);
      const icons = gsap.utils.toArray<HTMLElement>("[data-agent-icon]", sectionRef.current);
      const lines = gsap.utils.toArray<SVGLineElement>("[data-agent-line]", sectionRef.current);
      const particles = gsap.utils.toArray<SVGCircleElement>(
        "[data-agent-particle]",
        sectionRef.current,
      );

      gsap.set(cards, { opacity: 0.3, scale: 0.82 });
      gsap.set(icons, { backgroundColor: "var(--card)", color: "var(--muted-foreground)" });
      gsap.set(lines, { strokeDashoffset: 1 });

      const timeline = gsap.timeline({
        scrollTrigger: {
          trigger: sectionRef.current,
          start: "top top",
          end: "+=140%",
          scrub: 0.7,
          pin: true,
          pinSpacing: true,
          anticipatePin: 1,
        },
      });

      SPOKES.forEach((_, index) => {
        const at = index * 0.55;
        if (lines[index]) timeline.to(lines[index], { strokeDashoffset: 0, ease: "none" }, at);
        timeline.to(cards[index]!, { opacity: 1, scale: 1, ease: "none" }, at);
        timeline.to(
          icons[index]!,
          {
            backgroundColor: "var(--ai-activity)",
            color: "var(--ai-activity-foreground)",
            ease: "none",
          },
          at,
        );
      });

      particles.forEach((particle, index) => {
        const pos = spokePosition(index);
        gsap.set(particle, { attr: { cx: pos.x, cy: pos.y }, opacity: 0 });
        gsap
          .timeline({ repeat: -1, delay: 0.4 + index * 0.3 })
          .to(particle, { opacity: 1, duration: 0.15 })
          .to(particle, { attr: { cx: 50, cy: 50 }, duration: 1.6, ease: "power1.in" }, "<")
          .to(particle, { opacity: 0, duration: 0.15 }, "-=0.15")
          .set(particle, { attr: { cx: pos.x, cy: pos.y } })
          .to({}, { duration: 0.7 });
      });
    },
    { scope: sectionRef, dependencies: [reducedMotion] },
  );

  return (
    <SectionBand grid>
      <div ref={sectionRef} className="flex flex-col gap-16">
        <div className="grid gap-12 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)] lg:items-center lg:gap-16">
          <SectionHeading
            index="05"
            eyebrow="Agent orchestration"
            title="Then let agents do the work."
            subtitle="A supervisor coordinates specialist agents — each with a narrow job, full context, and a clear handoff back to the center."
          />

          <div className="relative mx-auto aspect-square w-full max-w-sm">
            <div
              aria-hidden
              className="bg-ai-activity absolute top-1/2 left-1/2 size-64 -translate-x-1/2 -translate-y-1/2 rounded-full opacity-[0.07] blur-[80px]"
            />

            <svg viewBox="0 0 100 100" className="absolute inset-0 h-full w-full" aria-hidden>
              {SPOKES.map((spoke, index) => {
                const pos = spokePosition(index);
                return (
                  <line
                    key={spoke.label}
                    data-agent-line
                    x1={50}
                    y1={50}
                    x2={pos.x}
                    y2={pos.y}
                    pathLength={1}
                    strokeDasharray={1}
                    strokeDashoffset={reducedMotion ? 0 : 1}
                    className="stroke-ai-activity/40"
                    strokeWidth={0.5}
                  />
                );
              })}
              {!reducedMotion
                ? SPOKES.map((spoke) => (
                    <circle
                      key={`particle-${spoke.label}`}
                      data-agent-particle
                      r={0.9}
                      className="fill-ai-activity"
                    />
                  ))
                : null}
            </svg>

            {!reducedMotion ? (
              <div
                aria-hidden
                className="border-ai-activity/25 absolute top-1/2 left-1/2 size-24 -translate-x-1/2 -translate-y-1/2 rounded-full border border-dashed"
                style={{ animation: "lum-orbit 14s linear infinite" }}
              />
            ) : null}

            <div
              className="group border-ai-activity/40 bg-card/80 absolute top-1/2 left-1/2 z-10 flex size-16 -translate-x-1/2 -translate-y-1/2 flex-col items-center justify-center gap-1 rounded-full border backdrop-blur-sm"
              style={{ boxShadow: `0 0 24px var(--ai-activity-glow)` }}
            >
              <SUPERVISOR.icon className="text-ai-activity size-4" />
              <span className="font-mono text-[9px]">{SUPERVISOR.label}</span>
              <span className="border-border bg-popover text-popover-foreground pointer-events-none absolute bottom-full left-1/2 mb-3 w-40 -translate-x-1/2 rounded-md border px-2.5 py-2 text-[11px] leading-snug opacity-0 shadow-[var(--shadow-elevated)] transition-opacity duration-200 group-hover:opacity-100">
                {SUPERVISOR.description}
              </span>
            </div>

            {SPOKES.map((spoke, index) => {
              const pos = spokePosition(index);
              return (
                <div
                  key={spoke.label}
                  data-agent-card
                  data-cursor-hover
                  className="group absolute flex flex-col items-center gap-1.5 text-center"
                  style={{
                    left: `${pos.x}%`,
                    top: `${pos.y}%`,
                    transform: "translate(-50%, -50%)",
                  }}
                >
                  <div
                    data-agent-icon
                    className="border-border/60 flex size-11 items-center justify-center rounded-full border backdrop-blur-sm transition-colors"
                  >
                    <spoke.icon className="size-4" />
                  </div>
                  <span className="font-mono text-[10px] whitespace-nowrap">{spoke.label}</span>
                  <span className="border-border bg-popover text-popover-foreground pointer-events-none absolute bottom-full left-1/2 z-20 mb-3 w-36 -translate-x-1/2 rounded-md border px-2.5 py-2 text-[11px] leading-snug opacity-0 shadow-[var(--shadow-elevated)] transition-opacity duration-200 group-hover:opacity-100">
                    {spoke.description}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        <AgentDecisionStream />
      </div>
    </SectionBand>
  );
}
