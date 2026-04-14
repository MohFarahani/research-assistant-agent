import type { SourceChunk as SourceChunkType } from "@/types/source";
import type { CitationRef } from "@/types/chat";
import { HighlightedText } from "@/components/source/HighlightedText";

interface SourceChunkProps {
  chunk: SourceChunkType;
  citation: CitationRef;
}

export function SourceChunk({ chunk, citation }: SourceChunkProps) {
  return (
    <div className="space-y-3">
      <div>
        <span className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
          Source
        </span>
        <p className="text-sm font-semibold text-zinc-200 mt-1">
          {citation.doc_label}, Page {chunk.page}
        </p>
      </div>
      <div className="h-px bg-zinc-700" />
      <HighlightedText text={chunk.text} highlightRanges={chunk.highlight_ranges} />
    </div>
  );
}
