import { useMutation } from "@tanstack/react-query";
import { ChevronDown, FileCode2, Loader2, Search } from "lucide-react";
import { useState } from "react";

import { searchRepository } from "@/shared/api/repositories";
import type { SearchResultItem } from "@/shared/api/types";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { cn } from "@/shared/lib/utils";

function ResultCard({ result }: { result: SearchResultItem }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="surface-card-interactive">
      <button
        type="button"
        onClick={() => setExpanded((value) => !value)}
        className="flex w-full items-start justify-between gap-3 p-3 text-left"
      >
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <FileCode2 className="text-engineering size-3.5 shrink-0" />
            <span className="truncate font-mono text-xs">{result.file_path}</span>
            <span className="text-muted-foreground shrink-0 text-[11px]">
              L{result.start_line}–{result.end_line}
            </span>
          </div>
          {result.symbol ? (
            <p className="mt-1 truncate text-sm font-medium">
              {result.symbol}{" "}
              <span className="text-muted-foreground font-normal">· {result.kind}</span>
            </p>
          ) : (
            <p className="text-muted-foreground mt-1 text-sm">{result.kind}</p>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <span className="bg-secondary text-secondary-foreground rounded px-1.5 py-0.5 font-mono text-[11px]">
            {result.score.toFixed(2)}
          </span>
          <ChevronDown
            className={cn(
              "text-muted-foreground size-4 transition-transform",
              expanded && "rotate-180",
            )}
          />
        </div>
      </button>
      {expanded ? (
        <pre className="border-border bg-muted/50 overflow-x-auto border-t p-3 font-mono text-[11px] leading-relaxed">
          {result.content}
        </pre>
      ) : null}
    </div>
  );
}

export function SearchPanel({ repositoryId }: { repositoryId: string }) {
  const [query, setQuery] = useState("");

  const searchMutation = useMutation({
    mutationFn: (q: string) => searchRepository(repositoryId, q, 10),
  });

  return (
    <div className="flex flex-col gap-4">
      <form
        onSubmit={(event) => {
          event.preventDefault();
          if (query.trim()) searchMutation.mutate(query.trim());
        }}
        className="flex items-center gap-2"
      >
        <div className="relative flex-1">
          <Search className="text-muted-foreground absolute top-1/2 left-3 size-4 -translate-y-1/2" />
          <Input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Where is authentication implemented?"
            className="pl-9"
          />
        </div>
        <Button type="submit" disabled={searchMutation.isPending || !query.trim()}>
          {searchMutation.isPending ? <Loader2 className="size-4 animate-spin" /> : "Search"}
        </Button>
      </form>

      {searchMutation.isError ? (
        <p className="text-destructive text-sm">{searchMutation.error.message}</p>
      ) : null}

      {searchMutation.isSuccess ? (
        searchMutation.data.results.length === 0 ? (
          <p className="text-muted-foreground text-sm">No matching chunks found.</p>
        ) : (
          <div className="flex flex-col gap-2">
            {searchMutation.data.results.map((result) => (
              <ResultCard key={result.chunk_id} result={result} />
            ))}
          </div>
        )
      ) : null}

      {!searchMutation.isSuccess && !searchMutation.isPending ? (
        <p className="text-muted-foreground text-sm">
          Search retrieves the most relevant code chunks using hybrid dense + BM25 retrieval with
          reranking.
        </p>
      ) : null}
    </div>
  );
}
