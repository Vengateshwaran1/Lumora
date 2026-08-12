import { useGSAP } from "@gsap/react";
import { type RefObject } from "react";

import { ensureGsapRegistered, gsap } from "@/shared/lib/gsap";
import { useReducedMotion } from "@/shared/hooks/use-reduced-motion";

/** GSAP ScrollTrigger reveal for landing-page section typography/content —
 * fades + rises elements matching `selector` within `scope` as the section
 * scrolls into view. Cinematic timing (landing-only); the application uses
 * `Reveal` (Framer Motion) instead, never this. */
export function useScrollReveal(scope: RefObject<HTMLElement | null>, selector: string) {
  const reducedMotion = useReducedMotion();

  useGSAP(
    () => {
      if (reducedMotion || !scope.current) return;
      ensureGsapRegistered();

      const targets = gsap.utils.toArray<HTMLElement>(selector, scope.current);
      if (targets.length === 0) return;

      gsap.set(targets, { opacity: 0, y: 28, filter: "blur(6px)" });
      gsap.to(targets, {
        opacity: 1,
        y: 0,
        filter: "blur(0px)",
        duration: 0.9,
        ease: "power3.out",
        stagger: 0.12,
        scrollTrigger: {
          trigger: scope.current,
          start: "top 75%",
          toggleActions: "play none none reverse",
        },
      });
    },
    { scope, dependencies: [reducedMotion] },
  );
}
