"use client";

import React, { useState } from "react";
import {
  Activity,
  Check,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  AlertTriangle,
  RotateCw,
  Layers,
  Clock,
} from "lucide-react";
import { formatDuration, formatTimestamp } from "@/lib/utils/formatters";
import type { EventItem } from "@/types";
import { useTaskEvents } from "@/hooks/useTaskEvents";
import { motion, AnimatePresence } from "framer-motion";

export interface RunInspectorProps {
  runId: string | null;
  taskTitle?: string;
  taskStatus?: string;
  initialEvents?: EventItem[];
  model?: string;
  durationSeconds?: number;
  onStatusChange?: (status: string) => void;
  className?: string;
}

export function RunInspector({
  runId,
  taskStatus = "idle",
  initialEvents = [],
  model,
  durationSeconds,
  onStatusChange,
  className,
}: RunInspectorProps) {
  const [expandedEventId, setExpandedEventId] = useState<string | null>(null);

  const { events, isPolling, refreshNow } = useTaskEvents({
    runId,
    initialEvents,
    isCompleted: taskStatus === "completed" || taskStatus === "failed",
    onStatusChange,
  });

  const getStageColor = (status: string) => {
    const s = (status || "").toLowerCase();
    if (s === "completed" || s === "success") {
      return {
        bg: "bg-[#22C55E]/15",
        text: "text-[#22C55E]",
        border: "border-[#22C55E]/40",
        badge: "bg-[#22C55E]/10 text-[#4ADE80] border-[#22C55E]/30",
      };
    }
    if (s === "running" || s === "started" || s === "in_progress") {
      return {
        bg: "bg-[#B8F23D]/20",
        text: "text-[#B8F23D]",
        border: "border-[#B8F23D]",
        badge: "bg-[#B8F23D]/10 text-[#D5FF78] border-[#B8F23D]/30",
      };
    }
    if (s === "warning" || s === "recovery") {
      return {
        bg: "bg-[#F59E0B]/20",
        text: "text-[#F59E0B]",
        border: "border-[#F59E0B]",
        badge: "bg-[#F59E0B]/10 text-[#FCD34D] border-[#F59E0B]/30",
      };
    }
    if (s === "failed" || s === "error") {
      return {
        bg: "bg-[#EF4444]/20",
        text: "text-[#EF4444]",
        border: "border-[#EF4444]",
        badge: "bg-[#EF4444]/10 text-[#FCA5A5] border-[#EF4444]/30",
      };
    }
    return {
      bg: "bg-[#171E18]",
      text: "text-[#657066]",
      border: "border-[#202A22]",
      badge: "bg-[#171E18] text-[#9BA79D] border-[#202A22]",
    };
  };

  if (!runId) {
    return (
      <div className="flex flex-col h-full bg-[#0D120F] border-l border-[#202A22] p-6 font-mono text-xs">
        <div className="flex items-center gap-2 pb-4 mb-8 border-b border-[#202A22] text-[#9BA79D]">
          <Activity className="w-4 h-4 text-[#657066]" />
          <span className="font-bold tracking-wider text-[#F1F5ED]">RUN INSPECTOR</span>
        </div>
        <div className="flex-1 flex flex-col items-center justify-center text-center p-4">
          <Layers className="w-8 h-8 text-[#657066] mb-3 stroke-[1.5]" />
          <div className="text-sm font-semibold text-[#F1F5ED] mb-1">No Active Run</div>
          <p className="text-xs text-[#9BA79D] max-w-xs leading-relaxed">
            Execute a job from the Task Composer or select a run from history to inspect checkpoints.
          </p>
        </div>
        <div className="pt-4 border-t border-[#202A22] text-[10px] text-[#657066] flex justify-between">
          <span>Telemetry daemon</span>
          <span className="text-[#22C55E]">Ready</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex flex-col h-full bg-[#0D120F] border-l border-[#202A22] font-mono text-xs ${className || ""}`}>
      {/* Header */}
      <div className="p-4 bg-[#121812] border-b border-[#202A22] shrink-0">
        <div className="flex items-center justify-between gap-2 mb-2">
          <div className="flex items-center gap-2 min-w-0">
            <Activity className="w-4 h-4 text-[#B8F23D] shrink-0" />
            <span className="font-bold tracking-wider text-[#F1F5ED] truncate">
              RUN INSPECTOR
            </span>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <span
              className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold border ${
                getStageColor(taskStatus).badge
              }`}
            >
              {taskStatus}
            </span>
            {isPolling && (
              <RotateCw className="w-3.5 h-3.5 text-[#B8F23D] animate-spin" />
            )}
          </div>
        </div>

        <div className="space-y-1 text-[11px] text-[#9BA79D]">
          <div className="flex items-center justify-between">
            <span className="text-[#657066]">Run ID:</span>
            <span className="text-[#F1F5ED] select-all font-semibold">{runId}</span>
          </div>
          {model && (
            <div className="flex items-center justify-between">
              <span className="text-[#657066]">Model:</span>
              <span className="text-[#D5FF78]">{model}</span>
            </div>
          )}
          {durationSeconds !== undefined && durationSeconds > 0 && (
            <div className="flex items-center justify-between">
              <span className="text-[#657066]">Duration:</span>
              <span className="text-[#F1F5ED]">{formatDuration(durationSeconds)}</span>
            </div>
          )}
        </div>
      </div>

      {/* Events Timeline */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {events.length === 0 ? (
          <div className="py-12 text-center text-[#657066] space-y-2">
            <Clock className="w-6 h-6 mx-auto animate-pulse" />
            <div>Waiting for pipeline execution events...</div>
          </div>
        ) : (
          <div className="relative pl-3 space-y-3 before:absolute before:left-1 before:top-2 before:bottom-2 before:w-px before:bg-[#202A22]">
            {events.map((event, idx) => {
              const style = getStageColor(event.status);
              const isExpanded = expandedEventId === (event.event_id || String(idx));
              const isEventRunning =
                event.status === "started" || event.status === "in_progress";

              return (
                <div
                  key={event.event_id || idx}
                  className="relative group text-left"
                >
                  {/* Status Indicator Icon */}
                  <span
                    className={`absolute -left-3 top-1 flex items-center justify-center w-4 h-4 rounded-full ${
                      style.bg
                    } ${style.text} ${style.border} border bg-[#0D120F] shrink-0 z-10 ${
                      isEventRunning ? "animate-pulse" : ""
                    }`}
                  >
                    {event.status === "completed" ? (
                      <Check className="w-2.5 h-2.5" />
                    ) : event.status === "failed" ? (
                      <AlertCircle className="w-2.5 h-2.5" />
                    ) : event.status === "warning" ? (
                      <AlertTriangle className="w-2.5 h-2.5" />
                    ) : (
                      <span className="w-1 h-1 rounded-full bg-current" />
                    )}
                  </span>

                  {/* Stage Card */}
                  <div
                    className={`p-3 rounded-lg border transition-all duration-200 cursor-pointer ${
                      isEventRunning
                        ? "bg-[#121812] border-[#B8F23D]/40"
                        : "bg-[#0A0E0C] border-[#202A22] hover:border-[#2B382D]"
                    }`}
                    onClick={() =>
                      setExpandedEventId(
                        isExpanded ? null : event.event_id || String(idx)
                      )
                    }
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-bold text-[#F1F5ED]">
                          {event.stage.replace(/_/g, " ")}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-[10px] text-[#657066]">
                        <span suppressHydrationWarning>{formatTimestamp(event.timestamp)}</span>
                        {isExpanded ? (
                          <ChevronUp className="w-3.5 h-3.5" />
                        ) : (
                          <ChevronDown className="w-3.5 h-3.5" />
                        )}
                      </div>
                    </div>

                    <p className="text-[11px] text-[#9BA79D] mt-1 leading-snug break-words">
                      {event.message}
                    </p>

                    {/* Metadata view */}
                    <AnimatePresence>
                      {isExpanded && event.metadata && Object.keys(event.metadata).length > 0 && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: "auto" }}
                          exit={{ opacity: 0, height: 0 }}
                          className="mt-2.5 pt-2 border-t border-[#202A22] space-y-1 text-[10px] text-[#657066]"
                        >
                          {Object.entries(event.metadata).map(([k, v]) => (
                            <div key={k} className="flex items-start justify-between gap-2">
                              <span className="text-[#657066] uppercase">{k}:</span>
                              <span className="text-[#F1F5ED] text-right font-mono truncate max-w-[200px]">
                                {typeof v === "object" ? JSON.stringify(v) : String(v)}
                              </span>
                            </div>
                          ))}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="p-3 bg-[#070A08] border-t border-[#202A22] text-[10px] text-[#657066] flex items-center justify-between shrink-0">
        <span>Verified checkpoints</span>
        <button
          onClick={refreshNow}
          className="text-[#9BA79D] hover:text-[#B8F23D] transition-colors flex items-center gap-1"
        >
          <RotateCw className="w-3 h-3" />
          <span>Refresh</span>
        </button>
      </div>
    </div>
  );
}
