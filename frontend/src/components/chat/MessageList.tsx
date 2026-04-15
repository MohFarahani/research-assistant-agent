"use client";

import { useEffect, useRef } from "react";
import type { Message, CitationRef } from "@/types/chat";
import { UserMessage } from "@/components/chat/UserMessage";
import { AIMessage } from "@/components/chat/AIMessage";

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
  onCitationOpen: (citation: CitationRef, query?: string) => void;
}

function TypingIndicator() {
  return (
    <div className="flex justify-start mb-4 px-4 gap-3">
      <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0 mt-1">
        AI
      </div>
      <div className="rounded-2xl rounded-tl-sm px-4 py-3 bg-zinc-800">
        <div className="flex gap-1 items-center h-4">
          <div className="w-2 h-2 rounded-full bg-zinc-400 animate-bounce [animation-delay:_0ms]" />
          <div className="w-2 h-2 rounded-full bg-zinc-400 animate-bounce [animation-delay:_150ms]" />
          <div className="w-2 h-2 rounded-full bg-zinc-400 animate-bounce [animation-delay:_300ms]" />
        </div>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-3 text-zinc-500 px-8 text-center">
      <svg
        aria-hidden="true"
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={1.5}
        className="w-10 h-10 text-zinc-600"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
        />
      </svg>
      <p className="text-sm">Upload a document and ask a question to get started.</p>
    </div>
  );
}

export function MessageList({ messages, isLoading, onCitationOpen }: MessageListProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages, isLoading]);

  if (messages.length === 0 && !isLoading) {
    return <EmptyState />;
  }

  return (
    <div
      ref={containerRef}
      role="log"
      aria-label="Chat messages"
      aria-live="polite"
      className="flex-1 overflow-y-auto py-4 scroll-smooth"
    >
      {messages.map((msg, idx) => {
        if (msg.role === "user") {
          return <UserMessage key={msg.id} message={msg} />;
        }
        const preceding = messages.slice(0, idx).findLast((m) => m.role === "user");
        return (
          <AIMessage
            key={msg.id}
            message={msg}
            query={preceding?.content}
            onCitationOpen={onCitationOpen}
          />
        );
      })}
      {isLoading && <TypingIndicator />}
    </div>
  );
}
