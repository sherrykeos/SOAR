"use client";

import React from "react";
import { ChatInterface } from "@/components/chat/ChatInterface";
import { RunInspector } from "@/components/inspector/RunInspector";
import { useWorkbench } from "@/context/WorkbenchContext";
import { AlertCircle, RefreshCw } from "lucide-react";

export default function WorkbenchHomePage() {
  const {
    sessionTasks,
    activeRunId,
    getTaskByRunId,
    inspectorOpen,
    setInspectorOpen,
    isBackendOnline,
    checkHealth,
  } = useWorkbench();

  const activeTask = activeRunId ? getTaskByRunId(activeRunId) : sessionTasks[0];

  return (
    <div className="flex-1 flex flex-col xl:flex-row min-w-0 min-h-0 h-full overflow-hidden">
      {/* Center Conversational Chat Workspace */}
      <div className="flex-1 flex flex-col min-w-0 min-h-0 h-full overflow-hidden relative">
        {/* Backend Warning Banner if offline */}
        {!isBackendOnline && (
          <div className="p-3 bg-[#EF4444]/10 border-b border-[#EF4444]/30 flex items-center justify-between gap-3 text-xs font-mono text-[#EF4444] shrink-0 z-10 px-4 sm:px-6">
            <div className="flex items-center gap-2 truncate">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span className="truncate">
                SOAR backend offline. Confirm server is running at <code>http://127.0.0.1:8000</code>.
              </span>
            </div>
            <button
              onClick={checkHealth}
              className="flex items-center gap-1 px-2.5 py-1 rounded bg-[#EF4444]/20 hover:bg-[#EF4444]/30 text-white transition shrink-0 cursor-pointer"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Retry</span>
            </button>
          </div>
        )}

        {/* Chat Interface (ChatGPT / Claude style) */}
        <ChatInterface />
      </div>

      {/* Collapsible Right Sidebar: Run Inspector & Checkpoint DAG */}
      {inspectorOpen && (
        <>
          {/* Mobile / Tablet backdrop overlay */}
          <div
            onClick={() => setInspectorOpen(false)}
            className="xl:hidden fixed inset-0 bg-black/60 backdrop-blur-xs z-20"
            aria-hidden="true"
          />

          <div className="fixed inset-y-14 right-0 z-30 w-full sm:w-96 xl:relative xl:inset-y-0 xl:w-96 shrink-0 xl:border-l border-[#202A22] bg-[#0D120F] h-[calc(100vh-3.5rem)] xl:h-full overflow-hidden transition-all duration-200 shadow-2xl flex flex-col">
            <RunInspector
              runId={activeTask?.run_id || activeRunId || null}
              taskStatus={activeTask?.status || "idle"}
              initialEvents={activeTask?.events || []}
              model={activeTask?.model}
              durationSeconds={activeTask?.duration_seconds}
              onClose={() => setInspectorOpen(false)}
            />
          </div>
        </>
      )}
    </div>
  );
}
