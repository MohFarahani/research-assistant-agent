import axios from "axios";
import type { Document, UploadResponse } from "@/types/document";
import type { UsageStatus } from "@/types/usage";

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  timeout: 30_000,
  withCredentials: true, // send user_id cookie on every request
});

export const listDocuments = (): Promise<Document[]> =>
  apiClient.get("/documents").then((r) => r.data);

export const getUsage = (): Promise<UsageStatus> =>
  apiClient.get("/usage").then((r) => r.data);

export const uploadDocument = (file: File): Promise<UploadResponse> => {
  const fd = new FormData();
  fd.append("file", file);
  return apiClient.post("/documents/upload", fd).then((r) => r.data);
};
