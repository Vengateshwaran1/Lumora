import { Link, Outlet } from "react-router-dom";

const BULLETS = [
  "Understands your code, not just your prompt.",
  "Every answer cites the file, commit, or issue behind it.",
  "Agents work in a sandbox — a human approves before it ships.",
];

export function AuthLayout() {
  return (
    <div className="bg-background grid min-h-svh lg:grid-cols-2">
      <div className="border-border relative hidden overflow-hidden border-r lg:flex lg:flex-col lg:justify-between lg:p-10">
        <div className="grain absolute inset-0" aria-hidden />
        <div className="pointer-events-none absolute inset-0 overflow-hidden opacity-30">
          <div className="bg-primary absolute top-[-10%] left-[-10%] size-[36rem] rounded-full blur-[140px]" />
          <div className="bg-engineering absolute right-[-10%] bottom-[-10%] size-[30rem] rounded-full blur-[140px]" />
        </div>

        <Link to="/" className="relative z-10 flex items-center gap-2">
          <div className="bg-primary flex h-8 w-8 items-center justify-center rounded-md">
            <span className="text-primary-foreground text-sm font-bold">L</span>
          </div>
          <span className="text-lg font-semibold tracking-tight">LUMORA</span>
        </Link>

        <div className="relative z-10 flex flex-col gap-6">
          <p className="font-display max-w-md text-3xl leading-[1.15] font-medium tracking-tight">
            Software engineering, with context.
          </p>
          <ul className="flex flex-col gap-3">
            {BULLETS.map((bullet) => (
              <li key={bullet} className="text-muted-foreground flex items-start gap-2.5 text-sm">
                <span className="bg-primary mt-2 size-1 shrink-0 rounded-full" aria-hidden />
                {bullet}
              </li>
            ))}
          </ul>
        </div>

        <span className="text-muted-foreground/60 relative z-10 font-mono text-[11px] tracking-wide">
          Obsidian / Copper — Engineering Intelligence
        </span>
      </div>

      <div className="relative flex items-center justify-center px-4 py-12">
        <div className="pointer-events-none absolute inset-0 overflow-hidden opacity-[0.08] lg:hidden">
          <div className="bg-primary absolute top-0 left-1/4 size-96 rounded-full blur-[140px]" />
          <div className="bg-engineering absolute right-1/4 bottom-0 size-96 rounded-full blur-[140px]" />
        </div>

        <div className="relative flex w-full max-w-sm flex-col gap-6">
          <Link to="/" className="flex items-center justify-center gap-2 lg:hidden">
            <div className="bg-primary flex h-8 w-8 items-center justify-center rounded-md">
              <span className="text-primary-foreground text-sm font-bold">L</span>
            </div>
            <span className="text-lg font-semibold tracking-tight">LUMORA</span>
          </Link>
          <div className="surface-card rounded-xl p-6 shadow-[var(--shadow-elevated)]">
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  );
}
