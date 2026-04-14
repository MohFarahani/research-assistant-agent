"use client";

import type { CitationRef } from "@/types/chat";
import { useChat } from "@/hooks/useChat";
import { MessageList } from "@/components/chat/MessageList";
import { ChatInput } from "@/components/chat/ChatInput";
import { DotsHorizontalIcon, XMarkIcon, MenuIcon } from "@/components/icons";

interface ChatAreaProps {
  onCitationOpen: (citation: CitationRef) => void;
  onToggleSidebar: () => void;
  className?: string;
}

export function ChatArea({ onCitationOpen, onToggleSidebar, className = "" }: ChatAreaProps) {
  const { messages, sendUserMessage, isLoading, error } = useChat();

  return (
    <section className={`flex flex-col h-full min-w-0 ${className}`}>
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-3.5 border-b border-zinc-700/50 flex-shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={onToggleSidebar}
            aria-label="Toggle document sidebar"
            className="md:hidden text-zinc-400 hover:text-zinc-200 p-1.5 rounded-lg hover:bg-zinc-800 transition-colors"
          >
            <MenuIcon className="w-5 h-5" />
          </button>
          <h1 className="text-base font-semibold text-zinc-100">
            <span className="font-bold">Research</span> Assistant
          </h1>
        </div>
        <div className="flex items-center gap-1">
          <button
            aria-label="More options"
            className="text-zinc-400 hover:text-zinc-200 p-1.5 rounded-lg hover:bg-zinc-800 transition-colors"
          >
            <DotsHorizontalIcon className="w-4 h-4" />
          </button>
          <button
            aria-label="Close"
            className="text-zinc-400 hover:text-zinc-200 p-1.5 rounded-lg hover:bg-zinc-800 transition-colors"
          >
            <XMarkIcon className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Messages */}
      <MessageList
        messages={messages}
        isLoading={isLoading}
        onCitationOpen={onCitationOpen}
      />

      {/* Error banner */}
      {error && (
        <div className="mx-4 mb-2 px-3 py-2 bg-red-900/30 border border-red-700/50 rounded-lg text-xs text-red-400">
          {error}
        </div>
      )}

      {/* Input */}
      <ChatInput onSend={sendUserMessage} isLoading={isLoading} />
    </section>
  );
}
