import type { AIMessage as AIMessageType, CitationRef } from "@/types/chat";
import { CitationBadge } from "@/components/chat/CitationBadge";
import ReactMarkdown from "react-markdown";
import type { Components } from "react-markdown";

interface AIMessageProps {
  message: AIMessageType;
  onCitationOpen: (citation: CitationRef) => void;
}

const markdownComponents: Components = {
  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
  strong: ({ children }) => (
    <strong className="font-semibold text-zinc-100">{children}</strong>
  ),
  ul: ({ children }) => (
    <ul className="list-disc list-outside pl-4 mb-2 space-y-0.5">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="list-decimal list-outside pl-4 mb-2 space-y-0.5">{children}</ol>
  ),
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  code: ({ children }) => (
    <code className="bg-zinc-700 text-blue-300 rounded px-1 text-xs font-mono">
      {children}
    </code>
  ),
};

export function AIMessage({ message, onCitationOpen }: AIMessageProps) {
  return (
    <div className="flex justify-start mb-4 px-4 gap-3">
      <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0 mt-1">
        AI
      </div>
      <div className="max-w-[75%]">
        <div className="rounded-2xl rounded-tl-sm px-4 py-3 bg-zinc-800 text-zinc-100 text-sm leading-relaxed break-words">
          <ReactMarkdown components={markdownComponents}>
            {message.content}
          </ReactMarkdown>
        </div>
        {message.citations.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-2">
            {message.citations.map((citation) => (
              <CitationBadge
                key={citation.chunk_id}
                citation={citation}
                onOpen={onCitationOpen}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
