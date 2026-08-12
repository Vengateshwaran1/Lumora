import { motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { MagneticButton } from "@/components/motion/magnetic-button";
import { cn } from "@/shared/lib/utils";

const SECTION_LINKS = [
  { id: "how-it-works", href: "#how-it-works", label: "How it works" },
  { id: "agents", href: "#agents", label: "Agents" },
];

interface Indicator {
  left: number;
  width: number;
}

export function MarketingNav() {
  const navigate = useNavigate();
  const navRef = useRef<HTMLElement>(null);
  const linkRefs = useRef<Record<string, HTMLAnchorElement | null>>({});
  const [scrolled, setScrolled] = useState(false);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [indicator, setIndicator] = useState<Indicator | null>(null);

  useEffect(() => {
    function handleScroll() {
      setScrolled(window.scrollY > window.innerHeight * 0.6);
    }
    handleScroll();
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    const observers = SECTION_LINKS.map((link) => {
      const el = document.getElementById(link.id);
      if (!el) return null;
      const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry?.isIntersecting) setActiveId(link.id);
        },
        { rootMargin: "-45% 0px -45% 0px" },
      );
      observer.observe(el);
      return observer;
    });
    return () => observers.forEach((observer) => observer?.disconnect());
  }, []);

  useEffect(() => {
    if (!activeId || !navRef.current) {
      setIndicator(null);
      return;
    }
    const linkEl = linkRefs.current[activeId];
    if (!linkEl) return;
    const navRect = navRef.current.getBoundingClientRect();
    const linkRect = linkEl.getBoundingClientRect();
    setIndicator({ left: linkRect.left - navRect.left, width: linkRect.width });
  }, [activeId, scrolled]);

  return (
    <motion.header
      layout
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className={cn(
        "fixed z-50 flex items-center justify-between",
        scrolled
          ? "glass border-border/60 inset-x-3 top-2.5 rounded-full border px-4 py-1.5 sm:inset-x-8"
          : "inset-x-0 top-0 border-transparent px-6 py-3 sm:px-10",
      )}
    >
      <Link to="/" className="flex items-center gap-2" data-cursor-hover>
        <div className="bg-primary flex h-5.5 w-5.5 items-center justify-center rounded-md">
          <span className="text-primary-foreground text-[11px] font-bold">L</span>
        </div>
        <span className="text-foreground text-[13px] font-semibold tracking-tight">LUMORA</span>
      </Link>

      <nav ref={navRef} className="relative hidden items-center gap-6 sm:flex">
        {indicator ? (
          <motion.span
            aria-hidden
            className="bg-primary absolute -bottom-1.5 h-px"
            animate={{ left: indicator.left, width: indicator.width }}
            transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
          />
        ) : null}
        {SECTION_LINKS.map((link) => (
          <a
            key={link.id}
            ref={(el) => {
              linkRefs.current[link.id] = el;
            }}
            href={link.href}
            data-cursor-hover
            className={cn(
              "text-[13px] transition-colors",
              activeId === link.id
                ? "text-foreground"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {link.label}
          </a>
        ))}
        <Link
          to="/login"
          data-cursor-hover
          className="text-muted-foreground hover:text-foreground text-[13px] transition-colors"
        >
          Sign in
        </Link>
      </nav>

      <MagneticButton
        onClick={() => void navigate("/app")}
        className="text-primary-foreground rounded-full bg-[image:var(--primary-gradient)] px-3.5 py-1.5 text-[13px] font-medium shadow-[var(--shadow-glow-primary)] transition-shadow duration-200 hover:shadow-[var(--shadow-glow-primary-hover)]"
      >
        Launch Lumora
      </MagneticButton>
    </motion.header>
  );
}
