import { apiClient } from "@/services/documentService";
import type { SourceChunk } from "@/types/source";

export const getChunk = (docId: string, chunkId: string): Promise<SourceChunk> =>
  apiClient.get(`/sources/${docId}/chunk/${chunkId}`).then((r) => r.data);
