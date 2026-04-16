import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listDocuments, uploadDocument, getUsage } from "@/services/documentService";
import type { Document, UploadResponse } from "@/types/document";
import type { UsageStatus } from "@/types/usage";

export function useDocuments() {
  return useQuery<Document[]>({
    queryKey: ["documents"],
    queryFn: listDocuments,
    staleTime: 30_000,
    refetchInterval: (query) => {
      const data = query.state.data;
      return Array.isArray(data) && data.some((d) => d.status === "processing") ? 5_000 : false;
    },
  });
}

export function useUsage() {
  return useQuery<UsageStatus>({
    queryKey: ["usage"],
    queryFn: getUsage,
    staleTime: 30_000,
    refetchInterval: 60_000,
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();
  return useMutation<UploadResponse, Error, File>({
    mutationFn: uploadDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}
