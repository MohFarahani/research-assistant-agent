import type { CitationRef } from "@/types/chat";

interface CitationBadgeProps {
  citation: CitationRef;
  onOpen: (citation: CitationRef) => void;
}

export function CitationBadge({ citation, onOpen }: CitationBadgeProps) {
  return (
    <button
      onClick={() => onOpen(citation)}
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-blue-600/20 text-blue-400 border border-blue-600/40 hover:bg-blue-600/40 hover:text-blue-300 transition-colors duration-150 cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 focus:ring-offset-zinc-800"
    >
      [{citation.doc_label}, Page {citation.page}]
    </button>
  );
}
