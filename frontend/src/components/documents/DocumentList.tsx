import type { Document } from "@/types/document";
import { DocumentIcon, SpinnerIcon, WarningIcon } from "@/components/icons";

interface DocumentListProps {
  documents: Document[];
  isLoading: boolean;
  isError: boolean;
  activeDocumentId: string | null;
  onSelectDocument: (id: string) => void;
}

function SkeletonItem() {
  return (
    <div className="animate-pulse flex items-center gap-3 px-3 py-2.5 rounded-lg">
      <div className="w-8 h-8 rounded-lg bg-zinc-700 flex-shrink-0" />
      <div className="flex-1 space-y-1.5">
        <div className="h-3 bg-zinc-700 rounded w-3/4" />
        <div className="h-2.5 bg-zinc-700 rounded w-1/3" />
      </div>
    </div>
  );
}

export function DocumentList({
  documents,
  isLoading,
  isError,
  activeDocumentId,
  onSelectDocument,
}: DocumentListProps) {
  if (isLoading) {
    return (
      <div className="space-y-1">
        <SkeletonItem />
        <SkeletonItem />
        <SkeletonItem />
      </div>
    );
  }

  if (isError) {
    return (
      <p className="text-xs text-red-400 px-3 py-2">Failed to load documents.</p>
    );
  }

  if (documents.length === 0) {
    return (
      <p className="text-xs text-zinc-500 px-3 py-4 text-center">
        No documents yet. Upload a PDF to get started.
      </p>
    );
  }

  return (
    <div className="space-y-1">
      {documents.map((doc) => {
        const isActive = doc.id === activeDocumentId;
        return (
          <button
            key={doc.id}
            onClick={() => onSelectDocument(doc.id)}
            title={doc.filename}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-colors duration-150 text-left group ${
              isActive
                ? "bg-blue-600/20 text-blue-300"
                : "hover:bg-zinc-800 text-zinc-300 hover:text-zinc-100"
            }`}
          >
            <div
              className={`w-8 h-8 flex-shrink-0 flex items-center justify-center rounded-lg ${
                isActive ? "bg-blue-600/30 text-blue-300" : "bg-zinc-700 text-zinc-400 group-hover:text-zinc-200"
              }`}
            >
              <DocumentIcon className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{doc.filename}</p>
              <p className="text-xs text-zinc-500 mt-0.5">
                {doc.page_count > 0 ? `${doc.page_count} pages` : ""}
              </p>
            </div>
            {doc.status === "processing" && (
              <SpinnerIcon className="w-3.5 h-3.5 flex-shrink-0 text-blue-400 animate-spin" />
            )}
            {doc.status === "error" && (
              <WarningIcon className="w-3.5 h-3.5 flex-shrink-0 text-red-400" />
            )}
          </button>
        );
      })}
    </div>
  );
}
