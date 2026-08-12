import { useMutation } from "@tanstack/react-query";
import { ArrowUp } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";

import { IntelligenceSignal } from "@/components/motion/intelligence-signal";
import { chatWithRepository } from "@/shared/api/repositories";
import { Textarea } from "@/shared/components/ui/textarea";
import { cn } from "@/shared/lib/utils";

import { useChatStore, type Conversation } from "./store";

function MessageBubble({ role, content }: { role: "user" | "assistant"; content: string }) {
  return (
    <div className={cn("flex", role === "user" ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[80%] rounded-lg px-3.5 py-2.5 text-sm whitespace-pre-wrap",
          role === "user"
            ? "bg-secondary text-secondary-foreground"
            : "border-ai-activity/20 bg-card border",
        )}
      >
        {content}
      </div>
    </div>
  );
}

interface InvestigationColumnProps {
  repositoryId: string | null;
  conversation: Conversation | undefined;
  onCreateConversation: () => string;
}

export function InvestigationColumn({
  repositoryId,
  conversation,
  onCreateConversation,
}: InvestigationColumnProps) {
  const [question, setQuestion] = useState("");
  const appendMessage = useChatStore((state) => state.appendMessage);
  const scrollRef = useRef<HTMLDivElement>(null);

  const chatMutation = useMutation({
    mutationFn: (params: { conversationId: string; question: string }) =>
      chatWithRepository(repositoryId!, params.question),
    onError: (error) => toast.error(error.message),
  });

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [conversation?.messages.length, chatMutation.isPending]);

  function handleSubmit() {
    if (!repositoryId || !question.trim()) return;
    const conversationId = conversation?.id ?? onCreateConversation();
    const text = question.trim();
    setQuestion("");

    appendMessage(conversationId, {
      id: `msg-${crypto.randomUUID()}`,
      role: "user",
      content: text,
      createdAt: new Date().toISOString(),
    });

    chatMutation.mutate(
      { conversationId, question: text },
      {
        onSuccess: (response) => {
          appendMessage(conversationId, {
            id: `msg-${crypto.randomUUID()}`,
            role: "assistant",
            content: response.answer,
            citations: response.citations,
            createdAt: new Date().toISOString(),
          });
        },
      },
    );
  }

  if (!repositoryId) {
    return (
      <div className="text-muted-foreground flex h-full flex-1 items-center justify-center text-sm">
        Select a repository to start investigating.
      </div>
    );
  }

  return (
    <div className="flex h-full flex-1 flex-col gap-4 px-4">
      <div ref={scrollRef} className="flex flex-1 flex-col gap-3 overflow-y-auto">
        {!conversation || conversation.messages.length === 0 ? (
          <p className="text-muted-foreground text-sm">
            Ask a question about this codebase — Lumora retrieves relevant files, symbols, and git
            history to answer with citations.
          </p>
        ) : (
          conversation.messages.map((message) => <MessageBubble key={message.id} {...message} />)
        )}
        {chatMutation.isPending ? (
          <div className="flex items-center gap-2">
            <IntelligenceSignal />
            <span className="text-muted-foreground text-xs">Investigating…</span>
          </div>
        ) : null}
      </div>

      <form
        onSubmit={(event) => {
          event.preventDefault();
          handleSubmit();
        }}
        className="surface-card focus-within:border-primary/40 flex items-end gap-2 p-2 transition-all duration-200 ease-[var(--ease-premium)] focus-within:shadow-[var(--shadow-glow-primary)]"
      >
        <Textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              handleSubmit();
            }
          }}
          placeholder="Why does payment retry create duplicate orders?"
          rows={2}
          className="resize-none border-0 shadow-none focus-visible:ring-0"
        />
        <button
          type="submit"
          disabled={!question.trim() || chatMutation.isPending}
          className="bg-primary text-primary-foreground flex size-8 shrink-0 items-center justify-center rounded-md disabled:opacity-40"
        >
          <ArrowUp className="size-4" />
        </button>
      </form>
    </div>
  );
}
