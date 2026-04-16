import { useState, useCallback } from "react";
import axios from "axios";
import { sendMessage } from "@/services/chatService";
import type { Message, UserMessage, AIMessage } from "@/types/chat";

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendUserMessage = useCallback(async (content: string) => {
    const trimmed = content.trim();
    if (!trimmed) return;

    const userMsg: UserMessage = {
      id: generateId(),
      role: "user",
      content: trimmed,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await sendMessage(trimmed);
      const aiMsg: AIMessage = {
        id: generateId(),
        role: "assistant",
        content: response.answer,
        citations: response.citations,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 429) {
        const data = err.response.data as {
          reset_at: string;
          detail: string;
        };
        const resetTime = new Date(data.reset_at);
        const timeStr = resetTime.toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        });
        setError(`Daily usage limit reached. Resets at ${timeStr} UTC.`);
      } else {
        setError("Failed to get a response. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { messages, sendUserMessage, isLoading, error };
}
