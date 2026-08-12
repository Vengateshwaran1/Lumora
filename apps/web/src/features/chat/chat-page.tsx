import { useSearchParams } from "react-router-dom";

import { ContextColumn } from "./context-column";
import { ConversationsColumn } from "./conversations-column";
import { InvestigationColumn } from "./investigation-column";
import { useChatStore } from "./store";

export function ChatPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const repositoryId = searchParams.get("repo");

  const conversations = useChatStore((state) => state.conversations);
  const activeId = useChatStore((state) => state.activeId);
  const createConversation = useChatStore((state) => state.createConversation);

  const activeConversation = conversations.find((conv) => conv.id === activeId);

  return (
    <div className="flex h-[calc(100svh-8.5rem)] flex-col gap-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">AI Chat</h1>
        <p className="text-muted-foreground text-sm">
          Investigate your codebase with cited, evidence-backed answers.
        </p>
      </div>

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-0 md:grid-cols-[220px_1fr_260px]">
        <ConversationsColumn
          repositoryId={repositoryId}
          onRepositoryChange={(id) => setSearchParams({ repo: id })}
        />
        <InvestigationColumn
          repositoryId={repositoryId}
          conversation={activeConversation}
          onCreateConversation={() => createConversation(repositoryId!)}
        />
        <ContextColumn conversation={activeConversation} />
      </div>
    </div>
  );
}
