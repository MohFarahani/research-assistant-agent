"use client";

import { useSourcePanel } from "@/hooks/useSourcePanel";
import { SourceChunk } from "@/components/source/SourceChunk";
import { XMarkIcon, ChevronRightIcon } from "@/components/icons";

function SkeletonLoader() {
  return (
    <div className="space-y-3 animate-pulse">
      <div className="h-3 bg-zinc-700 rounded w-1/3" />
      <div className="h-4 bg-zinc-700 rounded w-1/2" />
      <div className="h-px bg-zinc-700 rounded" />
      <div className="h-3 bg-zinc-700 rounded w-full" />
      <div className="h-3 bg-zinc-700 rounded w-5/6" />
      <div className="h-3 bg-zinc-700 rounded w-full" />
      <div className="h-3 bg-zinc-700 rounded w-4/6" />
      <div className="h-3 bg-zinc-700 rounded w-full" />
    </div>
  );
}

export function SourcePanel() {
  const { isOpen, selectedCitation, chunk, isLoadingChunk, chunkError, closePanel } =
    useSourcePanel();

  return (
    <aside
      className={`transition-all duration-300 ease-in-out overflow-hidden flex-shrink-0 ${
        isOpen ? "w-[320px]" : "w-0"
      }`}
    >
      <div className="w-[320px] h-full flex flex-col bg-zinc-900 border-l border-zinc-700/50">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3.5 border-b border-zinc-700/50 flex-shrink-0">
          <div className="flex items-center gap-2">
            <ChevronRightIcon className="w-4 h-4 text-zinc-400" />
            <h2 className="text-sm font-semibold text-zinc-200">Source of Truth</h2>
          </div>
          <button
            onClick={closePanel}
            aria-label="Close source panel"
            className="text-zinc-400 hover:text-zinc-200 transition-colors p-1 rounded hover:bg-zinc-800"
          >
            <XMarkIcon className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {isLoadingChunk && <SkeletonLoader />}

          {chunkError && (
            <p className="text-xs text-red-400 text-center mt-8">{chunkError}</p>
          )}

          {!isLoadingChunk && !chunkError && chunk && selectedCitation && (
            <SourceChunk chunk={chunk} citation={selectedCitation} />
          )}

          {!isLoadingChunk && !chunkError && !chunk && (
            <p className="text-sm text-zinc-500 text-center mt-8">
              Click a citation badge to view the source.
            </p>
          )}
        </div>
      </div>
    </aside>
  );
}
