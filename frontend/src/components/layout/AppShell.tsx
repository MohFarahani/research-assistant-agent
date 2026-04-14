"use client";

import { useState } from "react";
import { useSourcePanel } from "@/hooks/useSourcePanel";
import { LeftSidebar } from "@/components/layout/LeftSidebar";
import { ChatArea } from "@/components/layout/ChatArea";
import { SourcePanel } from "@/components/layout/SourcePanel";
import { XMarkIcon } from "@/components/icons";

export function AppShell() {
  const { openPanel } = useSourcePanel();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-zinc-950">
      {/* Mobile sidebar overlay */}
      {isSidebarOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/60"
            onClick={() => setIsSidebarOpen(false)}
          />
          {/* Sidebar */}
          <div className="relative z-10 w-[280px] h-full flex flex-col">
            <div className="flex items-center justify-end px-3 py-2 bg-zinc-900 border-b border-zinc-700/50">
              <button
                onClick={() => setIsSidebarOpen(false)}
                aria-label="Close sidebar"
                className="text-zinc-400 hover:text-zinc-200 p-1.5 rounded-lg hover:bg-zinc-800 transition-colors"
              >
                <XMarkIcon className="w-4 h-4" />
              </button>
            </div>
            <LeftSidebar className="flex-1" />
          </div>
        </div>
      )}

      {/* Desktop sidebar */}
      <div className="hidden md:flex md:w-16 lg:w-[280px] flex-shrink-0">
        <LeftSidebar className="w-full" />
      </div>

      {/* Center chat */}
      <main className="flex-1 min-w-0 flex flex-col overflow-hidden">
        <ChatArea
          onCitationOpen={openPanel}
          onToggleSidebar={() => setIsSidebarOpen((v) => !v)}
        />
      </main>

      {/* Right source panel — desktop push layout */}
      <div className="hidden md:flex">
        <SourcePanel />
      </div>

      {/* Right source panel — mobile bottom sheet */}
      <MobileSourcePanel />
    </div>
  );
}

function MobileSourcePanel() {
  const { isOpen, selectedCitation, chunk, isLoadingChunk, chunkError, closePanel } =
    useSourcePanel();

  return (
    <div
      className={`md:hidden fixed bottom-0 left-0 right-0 z-40 bg-zinc-900 rounded-t-2xl border-t border-zinc-700/50 transition-transform duration-300 ease-in-out ${
        isOpen ? "translate-y-0" : "translate-y-full"
      }`}
      style={{ height: "60vh" }}
    >
      <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-700/50">
        <h2 className="text-sm font-semibold text-zinc-200">Source of Truth</h2>
        <button
          onClick={closePanel}
          aria-label="Close source panel"
          className="text-zinc-400 hover:text-zinc-200 p-1 rounded hover:bg-zinc-800 transition-colors"
        >
          <XMarkIcon className="w-4 h-4" />
        </button>
      </div>
      <div className="overflow-y-auto p-4" style={{ height: "calc(60vh - 49px)" }}>
        {isLoadingChunk && (
          <div className="space-y-3 animate-pulse">
            <div className="h-3 bg-zinc-700 rounded w-1/3" />
            <div className="h-4 bg-zinc-700 rounded w-1/2" />
            <div className="h-px bg-zinc-700 rounded" />
            <div className="h-3 bg-zinc-700 rounded w-full" />
            <div className="h-3 bg-zinc-700 rounded w-5/6" />
          </div>
        )}
        {chunkError && (
          <p className="text-xs text-red-400 text-center mt-8">{chunkError}</p>
        )}
        {!isLoadingChunk && !chunkError && chunk && selectedCitation && (
          // lazy import to avoid circular - inline SourceChunk rendering
          <div className="space-y-3">
            <div>
              <span className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
                Source
              </span>
              <p className="text-sm font-semibold text-zinc-200 mt-1">
                {selectedCitation.doc_label}, Page {chunk.page}
              </p>
            </div>
            <div className="h-px bg-zinc-700" />
            <p className="text-sm leading-relaxed text-zinc-300">{chunk.text}</p>
          </div>
        )}
        {!isLoadingChunk && !chunkError && !chunk && (
          <p className="text-sm text-zinc-500 text-center mt-8">
            Click a citation badge to view the source.
          </p>
        )}
      </div>
    </div>
  );
}
