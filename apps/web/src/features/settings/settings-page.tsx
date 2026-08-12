import { ThemeToggle } from "@/shared/components/theme-toggle";
import { Separator } from "@/shared/components/ui/separator";

import { useRepositories } from "@/shared/api/repositories";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export function SettingsPage() {
  const reposQuery = useRepositories();
  const repos = reposQuery.data ?? [];

  return (
    <div className="flex max-w-2xl flex-col gap-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="text-muted-foreground text-sm">Application preferences and connections.</p>
      </div>

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-medium">Appearance</h2>
        <div className="surface-card flex items-center justify-between p-4">
          <div>
            <p className="text-sm font-medium">Theme</p>
            <p className="text-muted-foreground text-xs">Light, dark, or match your system.</p>
          </div>
          <ThemeToggle />
        </div>
      </section>

      <Separator />

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-medium">Connected repositories</h2>
        {repos.length === 0 ? (
          <p className="text-muted-foreground text-sm">No repositories connected yet.</p>
        ) : (
          <div className="flex flex-col gap-2">
            {repos.map((repo) => (
              <div key={repo.id} className="surface-card flex items-center justify-between p-3">
                <span className="truncate font-mono text-xs">{repo.url}</span>
              </div>
            ))}
          </div>
        )}
      </section>

      <Separator />

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-medium">About</h2>
        <div className="surface-card flex flex-col gap-2 p-4 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">API base URL</span>
            <span className="font-mono text-xs">{API_BASE_URL}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Milestone</span>
            <span>M3 — Planning Agent</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Authentication</span>
            <span>Not yet enabled — arrives in M6</span>
          </div>
        </div>
      </section>
    </div>
  );
}
