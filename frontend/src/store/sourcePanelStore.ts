import { create } from "zustand";
import { getChunk } from "@/services/sourceService";
import type { CitationRef } from "@/types/chat";
import type { SourceChunk } from "@/types/source";

interface SourcePanelStore {
  isOpen: boolean;
  selectedCitation: CitationRef | null;
  chunk: SourceChunk | null;
  isLoadingChunk: boolean;
  chunkError: string | null;
  openPanel: (citation: CitationRef) => Promise<void>;
  closePanel: () => void;
}

export const useSourcePanelStore = create<SourcePanelStore>((set, get) => ({
  isOpen: false,
  selectedCitation: null,
  chunk: null,
  isLoadingChunk: false,
  chunkError: null,

  openPanel: async (citation: CitationRef) => {
    set({
      isOpen: true,
      selectedCitation: citation,
      chunk: null,
      isLoadingChunk: true,
      chunkError: null,
    });

    try {
      const chunk = await getChunk(citation.doc_id, citation.chunk_id);
      // Guard against race condition: only set if this citation is still selected
      if (get().selectedCitation?.chunk_id === citation.chunk_id) {
        set({ chunk, isLoadingChunk: false });
      }
    } catch {
      if (get().selectedCitation?.chunk_id === citation.chunk_id) {
        set({ chunkError: "Failed to load source. Please try again.", isLoadingChunk: false });
      }
    }
  },

  closePanel: () =>
    set({ isOpen: false, selectedCitation: null, chunk: null, chunkError: null }),
}));
