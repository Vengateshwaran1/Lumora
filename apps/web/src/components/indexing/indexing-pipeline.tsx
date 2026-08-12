import { motion } from "framer-motion";
import { Check, GitBranch, Loader2, Plug, Search, X } from "lucide-react";

import { useReducedMotion } from "@/shared/hooks/use-reduced-motion";
import { cn } from "@/shared/lib/utils";

import type { FileProgressEntry, IndexingStage } from "./use-indexing-progress";

const STAGES: { key: IndexingStage; label: string; icon: typeof Plug }[] = [
  { key: "connecting", label: "Connecting", icon: Plug },
  { key: "fetching", label: "Fetching", icon: GitBranch },
  { key: "discovering", label: "Discovering files", icon: Search },
  { key: "processing", label: "Processing", icon: Loader2 },
  { key: "ready", label: "Index ready", icon: Check },
];

const PROCESSING_SUBSTAGES = [
  "Parsing",
  "Building symbol index",
  "Generating embeddings",
  "Updating knowledge",
];

function stageOrder(stage: IndexingStage): number {
  if (stage === "failed") return -1;
  return STAGES.findIndex((entry) => entry.key === stage);
}

interface IndexingPipelineProps {
  stage: IndexingStage;
  discoveredCount: number | null;
  completedCount: number;
  recentFiles: FileProgressEntry[];
  errorMessage?: string | null;
}

export function IndexingPipeline({
  stage,
  discoveredCount,
  completedCount,
  recentFiles,
  errorMessage,
}: IndexingPipelineProps) {
  const reducedMotion = useReducedMotion();
  const currentIndex = stageOrder(stage);

  if (stage === "failed") {
    return (
      <div className="border-destructive/30 bg-destructive/5 rounded-lg border p-4">
        <div className="flex items-center gap-2">
          <X className="text-destructive size-4" />
          <span className="text-destructive text-sm font-medium">Indexing failed</span>
        </div>
        {errorMessage ? (
          <p className="text-muted-foreground mt-1.5 text-xs">{errorMessage}</p>
        ) : null}
      </div>
    );
  }

  return (
    <div className="surface-card p-4">
      <ol className="flex items-center gap-1.5">
        {STAGES.map((entry, index) => {
          const done = index < currentIndex || stage === "ready";
          const active = index === currentIndex && stage !== "ready";
          return (
            <li key={entry.key} className="flex flex-1 items-center gap-1.5 last:flex-none">
              <div className="flex flex-col items-center gap-1.5">
                <div
                  className={cn(
                    "flex size-7 items-center justify-center rounded-full border text-xs transition-all duration-300 ease-[var(--ease-premium)]",
                    done &&
                      "bg-success border-success text-success-foreground shadow-[0_0_10px_var(--success-glow)]",
                    active &&
                      !done &&
                      "border-engineering text-engineering shadow-[0_0_12px_var(--engineering-glow)]",
                    !done && !active && "border-border text-muted-foreground",
                  )}
                >
                  {done ? (
                    <Check className="size-3.5" />
                  ) : (
                    <entry.icon
                      className={cn("size-3.5", active && !reducedMotion && "animate-spin")}
                    />
                  )}
                </div>
                <span
                  className={cn(
                    "text-[11px] font-medium whitespace-nowrap",
                    done && "text-foreground",
                    active && "text-engineering",
                    !done && !active && "text-muted-foreground",
                  )}
                >
                  {entry.label}
                </span>
              </div>
              {index < STAGES.length - 1 ? (
                <div className={cn("h-px flex-1", done ? "bg-success" : "bg-border")} />
              ) : null}
            </li>
          );
        })}
      </ol>

      {stage === "discovering" && discoveredCount !== null ? (
        <p className="text-muted-foreground mt-4 text-xs">
          <span className="text-foreground font-medium">{discoveredCount}</span> file
          {discoveredCount === 1 ? "" : "s"} changed since last index.
        </p>
      ) : null}

      {stage === "processing" ? (
        <div className="mt-4 space-y-3">
          <div className="flex flex-wrap gap-x-4 gap-y-1">
            {PROCESSING_SUBSTAGES.map((label) => (
              <span key={label} className="text-ai-activity flex items-center gap-1.5 text-xs">
                <motion.span
                  className="bg-ai-activity size-1 rounded-full"
                  animate={reducedMotion ? undefined : { opacity: [0.3, 1, 0.3] }}
                  transition={{ duration: 1.4, repeat: Infinity, ease: "easeInOut" }}
                />
                {label}
              </span>
            ))}
          </div>
          <p className="text-muted-foreground text-xs">
            {discoveredCount !== null ? (
              <>
                <span className="text-foreground font-medium">{completedCount}</span> /{" "}
                <span className="text-foreground font-medium">{discoveredCount}</span> files
                processed
              </>
            ) : (
              "Processing files…"
            )}
          </p>
          {recentFiles.length > 0 ? (
            <ul className="max-h-28 space-y-1 overflow-y-auto font-mono text-[11px]">
              {recentFiles.map((file, index) => (
                <li
                  key={`${file.path}-${index}`}
                  className="text-muted-foreground flex items-center gap-1.5"
                >
                  <Check className="text-success size-3 shrink-0" />
                  <span className="truncate">{file.path}</span>
                  <span className="shrink-0 opacity-60">{file.status}</span>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
