import { Bell, ChevronRight, Search, User } from "lucide-react";
import { Link, useLocation } from "react-router-dom";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/shared/components/ui/dropdown-menu";

import { useCommandPaletteStore } from "./command-palette-store";
import { NAV_ITEMS } from "./nav-items";

function useBreadcrumbs() {
  const location = useLocation();
  const segments = location.pathname.split("/").filter(Boolean);

  return segments.map((segment, index) => {
    const to = "/" + segments.slice(0, index + 1).join("/");
    const navMatch = NAV_ITEMS.find((item) => item.to === to);
    const label = navMatch?.label ?? decodeURIComponent(segment).replace(/-/g, " ");
    return { to, label };
  });
}

export function Topbar() {
  const crumbs = useBreadcrumbs().filter((crumb) => crumb.label.toLowerCase() !== "app");
  const setOpen = useCommandPaletteStore((state) => state.setOpen);

  return (
    <header className="glass border-border sticky top-0 z-30 flex h-14 shrink-0 items-center justify-between gap-4 border-b px-6">
      <nav
        aria-label="Breadcrumb"
        className="text-muted-foreground flex min-w-0 items-center gap-1.5 text-sm"
      >
        <Link to="/app" className="hover:text-foreground shrink-0 font-medium">
          Lumora
        </Link>
        {crumbs.map((crumb, index) => (
          <span key={crumb.to} className="flex min-w-0 items-center gap-1.5">
            <ChevronRight className="size-3.5 shrink-0" aria-hidden="true" />
            {index === crumbs.length - 1 ? (
              <span className="text-foreground truncate font-medium capitalize">{crumb.label}</span>
            ) : (
              <Link to={crumb.to} className="hover:text-foreground truncate capitalize">
                {crumb.label}
              </Link>
            )}
          </span>
        ))}
      </nav>

      <div className="flex shrink-0 items-center gap-2">
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="border-border bg-background text-muted-foreground hover:text-foreground hover:border-primary/40 flex cursor-pointer items-center gap-2 rounded-md border px-3 py-1.5 text-sm transition-all duration-200 ease-[var(--ease-premium)] hover:shadow-[0_0_0_1px_var(--primary-glow-soft)]"
        >
          <Search className="size-3.5" aria-hidden="true" />
          <span className="hidden sm:inline">Search…</span>
          <kbd className="bg-muted text-muted-foreground ml-2 hidden rounded border px-1.5 py-0.5 font-mono text-[10px] sm:inline">
            {navigator.platform.includes("Mac") ? "⌘K" : "Ctrl K"}
          </kbd>
        </button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              aria-label="Notifications"
              className="text-muted-foreground hover:text-foreground hover:bg-surface-hover relative flex h-8 w-8 cursor-pointer items-center justify-center rounded-md transition-all duration-200 ease-[var(--ease-premium)] active:scale-90"
            >
              <Bell className="size-4" aria-hidden="true" />
              <span className="bg-primary absolute top-1.5 right-1.5 size-1.5 rounded-full" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-72">
            <DropdownMenuLabel>Notifications</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="flex-col items-start gap-0.5">
              <span className="text-sm font-medium">Index completed</span>
              <span className="text-muted-foreground text-xs">
                acme/payments finished indexing.
              </span>
            </DropdownMenuItem>
            <DropdownMenuItem className="flex-col items-start gap-0.5">
              <span className="text-sm font-medium">Awaiting your approval</span>
              <span className="text-muted-foreground text-xs">PR #917 is ready for review.</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              aria-label="Profile"
              className="border-border bg-secondary text-secondary-foreground hover:border-primary/40 flex h-8 w-8 cursor-pointer items-center justify-center rounded-full border text-xs font-medium transition-all duration-200 ease-[var(--ease-premium)] active:scale-90"
            >
              <User className="size-4" aria-hidden="true" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Local user</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link to="/app/settings">Settings</Link>
            </DropdownMenuItem>
            <DropdownMenuItem disabled>Sign out (auth arrives in M6)</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
