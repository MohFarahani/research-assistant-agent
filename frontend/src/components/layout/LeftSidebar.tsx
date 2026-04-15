"use client";

import { useState } from "react";
import { useDocuments, useUploadDocument } from "@/hooks/useDocuments";
import { UploadButton } from "@/components/documents/UploadButton";
import { DocumentList } from "@/components/documents/DocumentList";

interface LeftSidebarProps {
  className?: string;
  expanded?: boolean;
}

export function LeftSidebar({ className = "", expanded = false }: LeftSidebarProps) {
  const { data: documents = [], isLoading, isError } = useDocuments();
  const { mutate: upload, isPending } = useUploadDocument();
  const [activeDocumentId, setActiveDocumentId] = useState<string | null>(null);

  return (
    <aside
      className={`flex flex-col h-full bg-zinc-900 border-r border-zinc-700/50 ${className}`}
    >
      <div className="p-3 lg:p-4 border-b border-zinc-700/50 flex-shrink-0">
        <h2 className={`text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3 ${expanded ? "block" : "hidden lg:block"}`}>
          Documents
        </h2>
        {/* Full button when expanded (mobile drawer) or on lg+ */}
        {expanded ? (
          <UploadButton onUpload={upload} isPending={isPending} />
        ) : (
          <>
            <div className="hidden lg:block">
              <UploadButton onUpload={upload} isPending={isPending} />
            </div>
            <div className="lg:hidden flex justify-center">
              <button
                onClick={() => {
                  const input = document.getElementById("file-upload-compact") as HTMLInputElement;
                  input?.click();
                }}
                disabled={isPending}
                aria-label="Upload document"
                className="w-10 h-10 flex items-center justify-center rounded-xl bg-blue-600 hover:bg-blue-500 text-white transition-colors disabled:opacity-60"
              >
                <input
                  id="file-upload-compact"
                  type="file"
                  accept=".pdf,.doc,.docx,.txt"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      upload(file);
                      e.target.value = "";
                    }
                  }}
                  className="sr-only"
                />
                {isPending ? (
                  <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="17 8 12 3 7 8" />
                    <line x1="12" y1="3" x2="12" y2="15" />
                  </svg>
                )}
              </button>
            </div>
          </>
        )}
      </div>
      <div className="flex-1 overflow-y-auto p-2">
        {/* Full list when expanded (mobile drawer) or on lg+ */}
        {expanded ? (
          <DocumentList
            documents={documents}
            isLoading={isLoading}
            isError={isError}
            activeDocumentId={activeDocumentId}
            onSelectDocument={setActiveDocumentId}
          />
        ) : (
          <>
            {/* Icon-only list on tablet */}
            <div className="lg:hidden space-y-1">
              {documents.map((doc) => (
                <div key={doc.id} className="relative group/tooltip">
                  <button
                    onClick={() => setActiveDocumentId(doc.id)}
                    aria-label={doc.filename}
                    className={`w-full flex justify-center p-2 rounded-lg transition-colors ${
                      doc.id === activeDocumentId
                        ? "bg-blue-600/20 text-blue-300"
                        : "hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200"
                    }`}
                  >
                    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                    </svg>
                  </button>
                  <div className="pointer-events-none absolute left-full top-1/2 -translate-y-1/2 ml-2 z-50 hidden group-hover/tooltip:block">
                    <div className="bg-zinc-800 text-zinc-100 text-xs rounded-md px-2.5 py-1.5 whitespace-nowrap max-w-[200px] truncate shadow-lg border border-zinc-700">
                      {doc.filename}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            {/* Full list on desktop */}
            <div className="hidden lg:block">
              <DocumentList
                documents={documents}
                isLoading={isLoading}
                isError={isError}
                activeDocumentId={activeDocumentId}
                onSelectDocument={setActiveDocumentId}
              />
            </div>
          </>
        )}
      </div>
    </aside>
  );
}
