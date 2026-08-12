import { FileCode2 } from "lucide-react";

import type { Conversation } from "./store";

export function ContextColumn({ conversation }: { conversation: Conversation | undefined }) {
  const lastAssistantMessage = [...(conversation?.messages ?? [])]
    .reverse()
    .find((message) => message.role === "assistant");

  const citations = lastAssistantMessage?.citations ?? [];

  return (
    <div className="border-border flex h-full flex-col gap-3 border-l pl-4">
      <h2 className="text-muted-foreground text-xs font-medium tracking-wide uppercase">Context</h2>
      {citations.length === 0 ? (
        <p className="text-muted-foreground text-xs">
          Evidence and sources for the latest answer will appear here.
        </p>
      ) : (
        <div className="flex flex-col gap-2 overflow-y-auto">
          {citations.map((citation, index) => (
            <div key={index} className="surface-card p-2.5">
              <div className="flex items-center gap-1.5">
                <FileCode2 className="text-engineering size-3.5 shrink-0" />
                <span className="truncate font-mono text-[11px]">{citation.file_path}</span>
              </div>
              <p className="text-muted-foreground mt-1 text-[11px]">
                {citation.symbol ?? citation.kind} · L{citation.start_line}–{citation.end_line} ·
                score {citation.score.toFixed(2)}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
