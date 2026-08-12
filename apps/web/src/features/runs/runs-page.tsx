import { Bot } from "lucide-react";
import { Link } from "react-router-dom";

export function RunsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Agent Runs</h1>
        <p className="text-muted-foreground text-sm">
          Planning Agent runs: queued → running → awaiting approval → approved or rejected.
        </p>
      </div>

      <div className="border-border flex flex-col items-center gap-3 rounded-lg border border-dashed py-16 text-center">
        <Bot className="text-muted-foreground size-8" />
        <p className="text-foreground text-sm font-medium">No run history list yet</p>
        <p className="text-muted-foreground max-w-sm text-xs">
          There's no cross-repository run history endpoint this milestone. Open an issue and use
          "Generate plan" to start a run — you'll land on its detail page directly.
        </p>
        <Link
          to="/app/issues"
          className="bg-primary text-primary-foreground rounded-md px-3 py-1.5 text-sm font-medium"
        >
          Go to Issues
        </Link>
      </div>
    </div>
  );
}
