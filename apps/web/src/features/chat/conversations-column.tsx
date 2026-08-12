import { MessageSquarePlus, Trash2 } from "lucide-react";

import { RepositorySelect } from "@/components/repository-select";
import { Button } from "@/shared/components/ui/button";
import { cn } from "@/shared/lib/utils";

import { useChatStore } from "./store";

interface ConversationsColumnProps {
  repositoryId: string | null;
  onRepositoryChange: (id: string) => void;
}

export function ConversationsColumn({
  repositoryId,
  onRepositoryChange,
}: ConversationsColumnProps) {
  const conversations = useChatStore((state) => state.conversations);
  const activeId = useChatStore((state) => state.activeId);
  const setActive = useChatStore((state) => state.setActive);
  const createConversation = useChatStore((state) => state.createConversation);
  const removeConversation = useChatStore((state) => state.removeConversation);

  const scoped = conversations.filter((conv) => conv.repositoryId === repositoryId);

  return (
    <div className="border-border flex h-full flex-col gap-3 border-r pr-4">
      <RepositorySelect value={repositoryId} onChange={onRepositoryChange} />

      <Button
        variant="secondary"
        size="sm"
        disabled={!repositoryId}
        onClick={() => repositoryId && createConversation(repositoryId)}
      >
        <MessageSquarePlus className="size-3.5" />
        New investigation
      </Button>

      <div className="flex flex-1 flex-col gap-1 overflow-y-auto">
        {scoped.length === 0 ? (
          <p className="text-muted-foreground px-1 text-xs">
            No conversations yet for this repository.
          </p>
        ) : (
          scoped.map((conv) => (
            <button
              key={conv.id}
              type="button"
              onClick={() => setActive(conv.id)}
              className={cn(
                "group flex items-center justify-between gap-2 rounded-md px-2.5 py-2 text-left text-sm transition-colors",
                activeId === conv.id
                  ? "bg-secondary text-secondary-foreground"
                  : "text-muted-foreground hover:bg-secondary/50 hover:text-foreground",
              )}
            >
              <span className="truncate">{conv.title}</span>
              <span
                role="button"
                tabIndex={-1}
                onClick={(event) => {
                  event.stopPropagation();
                  removeConversation(conv.id);
                }}
                className="shrink-0 opacity-0 group-hover:opacity-100"
              >
                <Trash2 className="hover:text-destructive size-3.5" />
              </span>
            </button>
          ))
        )}
      </div>
    </div>
  );
}
