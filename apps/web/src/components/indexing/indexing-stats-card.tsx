import type { IndexCompletedData } from "./use-indexing-progress";

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-muted-foreground text-[11px] tracking-wide uppercase">{label}</span>
      <span className="text-foreground text-sm font-semibold tabular-nums">{value}</span>
    </div>
  );
}

/** Real per-run stats from the last `index.completed` SSE payload — only
 * populated if the client was connected while the run happened; otherwise
 * omitted rather than guessed. */
export function IndexingStatsCard({ stats }: { stats: IndexCompletedData }) {
  return (
    <div className="surface-card p-4">
      <p className="text-muted-foreground mb-3 text-xs">
        Last run — {stats.no_op ? "no changes" : `${stats.duration_seconds.toFixed(1)}s`}
        {stats.fell_back_to_full_index ? " · fell back to full index" : ""}
      </p>
      <div className="grid grid-cols-3 gap-4 sm:grid-cols-6">
        <Stat label="Discovered" value={stats.files_discovered} />
        <Stat label="Added" value={stats.files_added} />
        <Stat label="Modified" value={stats.files_modified} />
        <Stat label="Deleted" value={stats.files_deleted} />
        <Stat label="Renamed" value={stats.files_renamed} />
        <Stat label="Errors" value={stats.errors} />
        <Stat label="Chunks created" value={stats.chunks_created} />
        <Stat label="Chunks deleted" value={stats.chunks_deleted} />
      </div>
    </div>
  );
}
