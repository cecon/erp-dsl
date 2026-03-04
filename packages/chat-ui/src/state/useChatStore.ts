import { create } from "zustand";
import type { Message } from "../types/chat";

interface ChatState {
  messages: Message[];
  isStreaming: boolean;
  activeAgentId: string | null;

  addMessage: (message: Message) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  appendStreamToken: (messageId: string, token: string) => void;
  setStreaming: (isStreaming: boolean) => void;
  setActiveAgent: (agentId: string | null) => void;
  clearMessages: () => void;
  removeMessage: (id: string) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isStreaming: false,
  activeAgentId: null,

  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),

  updateMessage: (id, updates) =>
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, ...updates } : msg,
      ),
    })),

  appendStreamToken: (messageId, token) =>
    set((state) => ({
      messages: state.messages.map((msg) => {
        if (msg.id !== messageId) return msg;
        const textContent = msg.content.find((c) => c.type === "text");
        if (textContent && textContent.type === "text") {
          return {
            ...msg,
            content: msg.content.map((c) =>
              c.type === "text" ? { ...c, text: c.text + token } : c,
            ),
          };
        }
        return {
          ...msg,
          content: [...msg.content, { type: "text" as const, text: token }],
        };
      }),
    })),

  setStreaming: (isStreaming) => set({ isStreaming }),

  setActiveAgent: (agentId) => set({ activeAgentId: agentId }),

  clearMessages: () => set({ messages: [] }),

  removeMessage: (id) =>
    set((state) => ({
      messages: state.messages.filter((msg) => msg.id !== id),
    })),
}));
