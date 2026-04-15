import type { HighlightRange } from "@/types/source";

interface HighlightedTextProps {
  text: string;
  highlightRanges: HighlightRange[];
}

interface Segment {
  text: string;
  highlighted: boolean;
}

function buildSegments(text: string, ranges: HighlightRange[]): Segment[] {
  if (ranges.length === 0) {
    return [{ text, highlighted: false }];
  }

  const sorted = [...ranges].sort((a, b) => a.start - b.start);
  const segments: Segment[] = [];
  let cursor = 0;

  for (const range of sorted) {
    if (range.start > cursor) {
      segments.push({ text: text.slice(cursor, range.start), highlighted: false });
    }
    segments.push({ text: text.slice(range.start, range.end), highlighted: true });
    cursor = range.end;
  }

  if (cursor < text.length) {
    segments.push({ text: text.slice(cursor), highlighted: false });
  }

  return segments;
}

export function HighlightedText({ text, highlightRanges }: HighlightedTextProps) {
  const segments = buildSegments(text, highlightRanges);

  return (
    <div className="text-sm leading-loose tracking-wide">
      {segments.map((seg, i) =>
        seg.highlighted ? (
          <span
            key={i}
            className="bg-amber-400/25 text-amber-200 rounded-sm px-0.5 ring-1 ring-amber-400/40 font-medium"
          >
            {seg.text}
          </span>
        ) : (
          <span key={i} className="text-zinc-400">
            {seg.text}
          </span>
        )
      )}
    </div>
  );
}
