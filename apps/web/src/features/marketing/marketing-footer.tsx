import { useRef } from "react";
import { Link } from "react-router-dom";

import { useScrollReveal } from "@/components/motion/use-scroll-reveal";

export function MarketingFooter() {
  const ref = useRef<HTMLElement>(null);
  useScrollReveal(ref, "[data-reveal]");

  return (
    <footer ref={ref} className="border-border border-t px-6 py-10 sm:px-10">
      <div
        data-reveal
        className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 sm:flex-row"
      >
        <div className="flex items-center gap-2">
          <div className="bg-primary flex h-6 w-6 items-center justify-center rounded-md">
            <span className="text-primary-foreground text-xs font-bold">L</span>
          </div>
          <span className="text-sm font-semibold tracking-tight">LUMORA</span>
        </div>
        <p className="text-muted-foreground text-xs">Understand. Plan. Build. Verify.</p>
        <nav className="flex items-center gap-5">
          <Link to="/login" className="text-muted-foreground hover:text-foreground text-xs">
            Sign in
          </Link>
          <Link to="/app" className="text-muted-foreground hover:text-foreground text-xs">
            Launch Lumora
          </Link>
        </nav>
      </div>
    </footer>
  );
}
