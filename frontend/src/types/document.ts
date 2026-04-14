export type DocumentStatus = "processing" | "ready" | "error";

export interface Document {
  id: string;
  filename: string;
  page_count: number;
  status: DocumentStatus;
  created_at: string;
}

export interface UploadResponse {
  id: string;
  filename: string;
  status: DocumentStatus;
}
