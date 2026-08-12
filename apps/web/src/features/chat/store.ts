import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { Citation } from "@/shared/api/types";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  createdAt: string;
}

export interface Conversation {
  id: string;
  repositoryId: string;
  title: string;
  messages: ChatMessage[];
  createdAt: string;
}

interface ChatStore {
  conversations: Conversation[];
  activeId: string | null;
  createConversation: (repositoryId: string) => string;
  setActive: (id: string | null) => void;
  appendMessage: (conversationId: string, message: ChatMessage) => void;
  removeConversation: (id: string) => void;
}

/** Client-side conversation history — `POST /repositories/{id}/chat` takes
 * only `{question}`, no server-side thread state or streaming, so every
 * turn is an independent call and the thread itself lives here. */
export const useChatStore = create<ChatStore>()(
  persist(
    (set, get) => ({
      conversations: [],
      activeId: null,
      createConversation: (repositoryId) => {
        const id = `conv-${crypto.randomUUID()}`;
        set((state) => ({
          conversations: [
            {
              id,
              repositoryId,
              title: "New investigation",
              messages: [],
              createdAt: new Date().toISOString(),
            },
            ...state.conversations,
          ],
          activeId: id,
        }));
        return id;
      },
      setActive: (id) => set({ activeId: id }),
      appendMessage: (conversationId, message) =>
        set((state) => ({
          conversations: state.conversations.map((conv) =>
            conv.id === conversationId
              ? {
                  ...conv,
                  messages: [...conv.messages, message],
                  title:
                    conv.title === "New investigation" && message.role === "user"
                      ? message.content.slice(0, 60)
                      : conv.title,
                }
              : conv,
          ),
        })),
      removeConversation: (id) =>
        set((state) => ({
          conversations: state.conversations.filter((conv) => conv.id !== id),
          activeId: get().activeId === id ? null : get().activeId,
        })),
    }),
    { name: "lumora.chat" },
  ),
);
