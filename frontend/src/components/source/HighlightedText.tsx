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
    <p className="text-sm leading-relaxed">
      {segments.map((seg, i) =>
        seg.highlighted ? (
          <span key={i} className="bg-yellow-400/30 text-yellow-200 rounded px-0.5">
            {seg.text}
          </span>
        ) : (
          <span key={i} className="text-zinc-300">
            {seg.text}
          </span>
        )
      )}
    </p>
  );
}
