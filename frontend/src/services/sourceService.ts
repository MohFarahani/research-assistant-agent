import { apiClient } from "@/services/documentService";
import type { SourceChunk } from "@/types/source";

export const getChunk = (docId: string, chunkId: string, query = ""): Promise<SourceChunk> =>
  apiClient
    .get(`/sources/${docId}/chunk/${chunkId}`, { params: query ? { query } : undefined })
    .then((r) => r.data);
