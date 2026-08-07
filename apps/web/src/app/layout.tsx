import { Outlet } from "react-router-dom";

import { Nav } from "@/shared/components/nav";
import { ThemeToggle } from "@/shared/components/theme-toggle";

export function AppLayout() {
  return (
    <div className="grid min-h-svh grid-cols-[16rem_1fr] grid-rows-[auto_1fr]">
      <header className="border-border col-span-2 flex items-center justify-between border-b px-6 py-3">
        <span className="text-lg font-semibold tracking-tight">Lumora</span>
        <ThemeToggle />
      </header>

      <aside className="border-border border-r px-3 py-4">
        <Nav />
      </aside>

      <main className="overflow-y-auto px-8 py-6">
        <Outlet />
      </main>
    </div>
  );
}
