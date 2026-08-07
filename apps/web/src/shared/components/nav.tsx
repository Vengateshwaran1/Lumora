import { NavLink } from "react-router-dom";

import { cn } from "@/shared/lib/utils";

const NAV_ITEMS: { to: string; label: string; end: boolean }[] = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/repos", label: "Repos", end: false },
  { to: "/chat", label: "Chat", end: false },
  { to: "/issues", label: "Issues", end: false },
  { to: "/pr-review", label: "PR Review", end: false },
  { to: "/agent-runs", label: "Agent Runs", end: false },
  { to: "/settings", label: "Settings", end: false },
];

export function Nav() {
  return (
    <nav aria-label="Primary" className="flex flex-col gap-1">
      {NAV_ITEMS.map(({ to, label, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          className={({ isActive }) =>
            cn(
              "rounded-md px-3 py-2 text-sm font-medium transition-colors",
              isActive
                ? "bg-secondary text-secondary-foreground"
                : "text-muted-foreground hover:bg-secondary/50 hover:text-foreground",
            )
          }
        >
          {label}
        </NavLink>
      ))}
    </nav>
  );
}
