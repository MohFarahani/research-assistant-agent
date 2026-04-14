import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listDocuments, uploadDocument } from "@/services/documentService";
import type { Document, UploadResponse } from "@/types/document";

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

export function useUploadDocument() {
  const queryClient = useQueryClient();
  return useMutation<UploadResponse, Error, File>({
    mutationFn: uploadDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}
