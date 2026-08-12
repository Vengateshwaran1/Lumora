import { motion } from "framer-motion";
import { Settings } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { NavLink } from "react-router-dom";

import { ThemeToggle } from "@/shared/components/theme-toggle";
import { cn } from "@/shared/lib/utils";

import { NAV_ITEMS } from "./nav-items";

function NavItem({
  to,
  label,
  icon: Icon,
  end,
}: {
  to: string;
  label: string;
  icon: LucideIcon;
  end?: boolean;
}) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        cn(
          "group relative flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors duration-200 ease-[var(--ease-premium)]",
          isActive ? "text-foreground" : "text-muted-foreground hover:text-foreground",
        )
      }
    >
      {({ isActive }) => (
        <>
          {isActive ? (
            <motion.span
              layoutId="sidebar-active-pill"
              className="border-primary/15 bg-secondary absolute inset-0 rounded-md border shadow-[0_0_0_1px_var(--primary-glow-soft),0_4px_16px_-6px_var(--primary-glow)]"
              transition={{ type: "spring", stiffness: 500, damping: 38 }}
            />
          ) : (
            <span className="group-hover:bg-surface-hover absolute inset-0 rounded-md transition-colors duration-200" />
          )}
          <Icon
            className={cn(
              "relative z-10 size-4 shrink-0 transition-colors",
              isActive && "text-primary",
            )}
            aria-hidden="true"
          />
          <span className="relative z-10">{label}</span>
        </>
      )}
    </NavLink>
  );
}

export function Sidebar() {
  return (
    <aside className="glass border-border flex h-full w-64 flex-col border-r px-3 py-4">
      <div className="flex items-center gap-2 px-3 pb-6">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-[image:var(--primary-gradient)] shadow-[var(--shadow-glow-primary)]">
          <span className="text-primary-foreground text-sm font-bold">L</span>
        </div>
        <span className="text-foreground text-base font-semibold tracking-tight">LUMORA</span>
      </div>

      <nav aria-label="Primary" className="flex flex-1 flex-col gap-0.5">
        {NAV_ITEMS.map((item) => (
          <NavItem key={item.to} {...item} />
        ))}
      </nav>

      <div className="border-border flex flex-col gap-2 border-t pt-3">
        <NavItem to="/app/settings" label="Settings" icon={Settings} />
        <div className="flex items-center justify-between px-3">
          <div className="flex items-center gap-2">
            <div className="bg-secondary flex h-6 w-6 items-center justify-center rounded-full text-xs font-medium">
              L
            </div>
            <span className="text-muted-foreground text-xs">Local user</span>
          </div>
          <ThemeToggle />
        </div>
      </div>
    </aside>
  );
}
