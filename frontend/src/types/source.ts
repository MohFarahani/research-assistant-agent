export interface HighlightRange {
  start: number;
  end: number;
}

export interface SourceChunk {
  doc_id: string;
  chunk_id: string;
  page: number;
  text: string;
  highlight_ranges: HighlightRange[];
}
