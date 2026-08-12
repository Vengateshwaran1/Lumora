import { Code2, FileCode2, Folder } from "lucide-react";

import { PreviewBadge } from "@/shared/components/preview-badge";

const PREVIEW_TREE = [
  { path: "src/", type: "dir" as const, depth: 0 },
  { path: "payments/", type: "dir" as const, depth: 1 },
  { path: "retry_handler.py", type: "file" as const, depth: 2 },
  { path: "idempotency.py", type: "file" as const, depth: 2 },
  { path: "webhooks/", type: "dir" as const, depth: 1 },
  { path: "github.py", type: "file" as const, depth: 2 },
  { path: "tests/", type: "dir" as const, depth: 0 },
];

export function CodePage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Code</h1>
          <p className="text-muted-foreground text-sm">
            Browse files, symbols, and dependencies directly — powered by the same index behind
            Knowledge search.
          </p>
        </div>
        <PreviewBadge />
      </div>

      <div className="surface-card grid grid-cols-1 gap-4 p-6 sm:grid-cols-[220px_1fr]">
        <div className="flex flex-col gap-1">
          {PREVIEW_TREE.map((entry) => (
            <div
              key={entry.path}
              className="text-muted-foreground flex items-center gap-1.5 text-xs"
              style={{ paddingLeft: `${entry.depth * 12}px` }}
            >
              {entry.type === "dir" ? (
                <Folder className="size-3.5 shrink-0" />
              ) : (
                <FileCode2 className="text-engineering size-3.5 shrink-0" />
              )}
              {entry.path}
            </div>
          ))}
        </div>
        <div className="border-border bg-muted/30 flex flex-col items-center justify-center gap-2 rounded-md border border-dashed p-10 text-center">
          <Code2 className="text-muted-foreground size-8" />
          <p className="text-foreground text-sm font-medium">
            Full source viewer arrives in a later milestone
          </p>
          <p className="text-muted-foreground max-w-sm text-xs">
            For now, browse indexed content through <span className="font-medium">Knowledge</span>{" "}
            search or ask <span className="font-medium">AI Chat</span> about specific files and
            symbols.
          </p>
        </div>
      </div>
    </div>
  );
}
