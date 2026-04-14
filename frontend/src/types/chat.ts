import type { SourceChunk } from "@/types/source";

export interface CitationRef {
  doc_id: string;
  chunk_id: string;
  doc_label: string;
  page: number;
}

export interface UserMessage {
  id: string;
  role: "user";
  content: string;
  timestamp: string;
}

export interface AIMessage {
  id: string;
  role: "assistant";
  content: string;
  citations: CitationRef[];
  timestamp: string;
}

export type Message = UserMessage | AIMessage;

export interface ChatRequest {
  message: string;
}

export interface ChatResponse {
  answer: string;
  citations: CitationRef[];
}

export interface LoadedCitation {
  citation: CitationRef;
  chunk: SourceChunk;
}
