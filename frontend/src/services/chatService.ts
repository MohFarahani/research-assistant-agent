import { apiClient } from "@/services/documentService";
import type { ChatResponse } from "@/types/chat";

export const sendMessage = (message: string): Promise<ChatResponse> =>
  apiClient.post("/chat", { message }, { timeout: 60_000 }).then((r) => r.data);
