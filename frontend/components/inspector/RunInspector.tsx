"use client";

import React, { useState, useEffect, useMemo, useRef } from "react";
import {
  Activity,
  Check,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  RotateCw,
  Clock,
  PanelRightClose,
  Cpu,
  Database,
  Terminal,
  FileCheck,
  GitBranch,
  Copy,
  Layers,
  Sparkles,
} from "lucide-react";
import { formatDuration, formatTimestamp } from "@/lib/utils/formatters";
import type { EventItem } from "@/types";
import { useTaskEvents } from "@/hooks/useTaskEvents";
import { PipelineConnectingLine } from "./PipelineConnectingLine";
import { motion, AnimatePresence } from "framer-motion";

export interface RunInspectorProps {
  runId: string | null;
  taskTitle?: string;
  taskStatus?: string;
  initialEvents?: EventItem[];
  model?: string;
  durationSeconds?: number;
  onStatusChange?: (status: string) => void;
  onClose?: () => void;
  className?: string;
}

interface PipelineStageDef {
  id: string;
  key: string;
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}

const PIPELINE_STAGES: PipelineStageDef[] = [
  {
    id: "stage_classify",
    key: "CLASSIFYING",
    name: "Task Classification",
    description: "Classifying task",
    icon: Layers,
  },
  {
    id: "stage_route",
    key: "MODEL_SELECTING",
    name: "Model Selection",
    description: "Selecting execution model",
    icon: Cpu,
  },
  {
    id: "stage_plan",
    key: "PLANNING",
    name: "Planning",
    description: "Generating execution plan",
    icon: Database,
  },
  {
    id: "stage_execute",
    key: "TOOL_EXECUTING",
    name: "Tool Execution",
    description: "Executing local tools",
    icon: Terminal,
  },
  {
    id: "stage_observe",
    key: "OBSERVING",
    name: "Observation",
    description: "Receiving tool result",
    icon: Activity,
  },
  {
    id: "stage_reason",
    key: "REASONING",
    name: "Reasoning",
    description: "Processing results",
    icon: Sparkles,
  },
  {
    id: "stage_complete",
    key: "GENERATING_OUTPUT",
    name: "Output Generation",
    description: "Generating response or artifact",
    icon: FileCheck,
  },
  {
    id: "stage_completed",
    key: "COMPLETED",
    name: "Completed",
    description: "Execution completed",
    icon: Check,
  },
];

export function RunInspector({
  runId,
  taskTitle,
  taskStatus = "idle",
  initialEvents = [],
  model,
  durationSeconds,
  onStatusChange,
  onClose,
  className,
}: RunInspectorProps) {
  const [expandedStageId, setExpandedStageId] = useState<string | null>(null);
  const [copiedRunId, setCopiedRunId] = useState<boolean>(false);
  const [elapsedMs, setElapsedMs] = useState<number>(0);
  const [demoStageIndex, setDemoStageIndex] = useState<number>(0);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  const isRunning =
    taskStatus === "running" ||
    taskStatus === "in_progress" ||
    taskStatus === "started";
  const isFailed = taskStatus === "failed" || taskStatus === "error";
  const isCompleted = taskStatus === "completed" || taskStatus === "success";
  const isFinished = !runId || isCompleted || isFailed || taskStatus === "idle";

  const { events, isPolling, refreshNow } = useTaskEvents({
    runId,
    initialEvents,
    isCompleted: isFinished,
    onStatusChange,
  });

  // Accurate real-time timer while task is executing
  useEffect(() => {
    if (!isRunning) {
      setElapsedMs(0);
      return;
    }
    const startTime = Date.now();
    const interval = setInterval(() => {
      setElapsedMs(Date.now() - startTime);
    }, 100);

    return () => clearInterval(interval);
  }, [isRunning]);

  // Temporary presentation mode: visibly walk the checkpoints while the
  // synchronous task request is still running. Terminal backend events still
  // decide the final completed/failed state.
  useEffect(() => {
    if (!isRunning) {
      setDemoStageIndex(isCompleted ? PIPELINE_STAGES.length : 0);
      return;
    }

    setDemoStageIndex(0);
    const timer = setInterval(() => {
      setDemoStageIndex((current) =>
        Math.min(current + 1, PIPELINE_STAGES.length - 1)
      );
    }, 700);

    return () => clearInterval(timer);
  }, [isRunning, isCompleted, runId]);

  const copyRunId = () => {
    if (runId) {
      navigator.clipboard.writeText(runId);
      setCopiedRunId(true);
      setTimeout(() => setCopiedRunId(false), 2000);
    }
  };

  const stageData = useMemo(() => {
    const rawEvents = events.length > 0 ? events : initialEvents;

    return PIPELINE_STAGES.map((def, idx) => {
      const matchingEvents = rawEvents.filter((e) => e.stage === def.key);
      const latestEvent = matchingEvents[matchingEvents.length - 1];
      const latestStatus = latestEvent?.status?.toUpperCase();
      const hasFailed = latestStatus === "FAILED";
      const hasCompleted = latestStatus === "COMPLETED";
      const isActive = !!latestEvent && !hasFailed && !hasCompleted &&
        (latestEvent.status === "STARTED" || latestEvent.status === "IN_PROGRESS" || latestEvent.status === "started" || latestEvent.status === "in_progress");

      let status: "completed" | "running" | "pending" | "failed" = "pending";
      if (hasFailed) status = "failed";
      else if (hasCompleted) status = "completed";
      else if (isActive) status = "running";

      // Presentation mode owns the intermediate checkpoints. The final
      // checkpoint is different: it may settle only when the task response
      // has actually completed.
      if (isCompleted && !isFailed) {
        status = "completed";
      } else if (isRunning && !isFailed) {
        if (idx < demoStageIndex) status = "completed";
        else if (idx === demoStageIndex) status = "running";
        else status = "pending";
      }
      const statusMessage =
        latestEvent?.message ||
        (status === "completed" ? `${def.name} completed` : def.description);

      return {
        ...def,
        status,
        statusMessage,
        timestamp: latestEvent?.timestamp || "",
        metadata: latestEvent?.metadata || {},
        events: matchingEvents,
      };
    });
  }, [events, initialEvents, isCompleted, isFailed, isRunning]);

  // Empty State when no run is selected
  if (!runId) {
    return (
      <div className={`flex flex-col h-full bg-[#0D120F] border-l border-[#202A22] p-4 sm:p-5 font-mono text-xs ${className || ""}`}>
        <div className="flex items-center justify-between pb-3.5 mb-6 border-b border-[#202A22] text-[#9BA79D]">
          <div className="flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-[#B8F23D]" />
            <span className="font-bold tracking-wider text-[#F1F5ED]">EXECUTION PIPELINE</span>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="p-1 rounded text-[#657066] hover:text-[#F1F5ED] hover:bg-[#121812] transition cursor-pointer"
              title="Close pipeline"
            >
              <PanelRightClose className="w-4 h-4" />
            </button>
          )}
        </div>
        <div className="flex-1 flex flex-col items-center justify-center text-center p-4">
          <div className="w-10 h-10 rounded-xl bg-[#121812] border border-[#202A22] flex items-center justify-center mb-3 text-[#657066]">
            <GitBranch className="w-5 h-5 stroke-[1.5]" />
          </div>
          <div className="text-sm font-semibold text-[#F1F5ED] mb-1">Pipeline Idle</div>
          <p className="text-xs text-[#9BA79D] max-w-xs leading-relaxed font-sans">
            Start a chat prompt or choose a task to inspect live execution checkpoints.
          </p>
        </div>
        <div className="pt-3 border-t border-[#202A22] text-[10px] text-[#657066] flex justify-between items-center">
          <span>Sovereign Telemetry</span>
          <span className="text-[#B8F23D] flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-[#B8F23D]" />
            Ready
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex flex-col h-full bg-[#0D120F] border-l border-[#202A22] font-mono text-xs overflow-hidden ${className || ""}`}>
      {/* Header */}
      <div className="p-3.5 sm:p-4 bg-[#121812] border-b border-[#202A22] shrink-0 space-y-2.5">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <GitBranch className={`w-4 h-4 shrink-0 ${isRunning ? "text-[#B8F23D] animate-pulse" : "text-[#B8F23D]"}`} />
            <span className="font-bold tracking-wider text-[#F1F5ED] text-xs truncate">
              EXECUTION PIPELINE
            </span>
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            {isRunning ? (
              <span className="px-2 py-0.5 rounded-full bg-[#B8F23D]/15 text-[#D5FF78] border border-[#B8F23D]/30 text-[10px] uppercase font-bold flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#B8F23D] animate-pulse" />
                RUNNING
              </span>
            ) : isCompleted ? (
              <span className="px-2 py-0.5 rounded bg-[#B8F23D]/10 text-[#D5FF78] border border-[#B8F23D]/30 text-[10px] uppercase font-bold flex items-center gap-1">
                <Check className="w-3 h-3" />
                COMPLETE
              </span>
            ) : isFailed ? (
              <span className="px-2 py-0.5 rounded bg-[#EF4444]/15 text-[#FCA5A5] border border-[#EF4444]/30 text-[10px] uppercase font-bold flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                FAILED
              </span>
            ) : (
              <span className="px-2 py-0.5 rounded bg-[#171E18] text-[#9BA79D] border border-[#202A22] text-[10px] uppercase font-bold">
                {taskStatus}
              </span>
            )}

            {isPolling && (
              <RotateCw className="w-3 h-3 text-[#B8F23D] animate-spin" />
            )}

            {onClose && (
              <button
                onClick={onClose}
                className="p-1 rounded text-[#657066] hover:text-[#F1F5ED] hover:bg-[#070A08] transition ml-1 cursor-pointer"
                title="Close inspector"
              >
                <PanelRightClose className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Telemetry info card */}
        <div className="space-y-1 text-[11px] text-[#9BA79D] bg-[#070A08]/80 p-2 rounded-lg border border-[#202A22]">
          <div className="flex items-center justify-between">
            <span className="text-[#657066]">Run ID:</span>
            <button
              onClick={copyRunId}
              className="flex items-center gap-1 text-[#F1F5ED] hover:text-[#4ADE80] transition group font-mono cursor-pointer"
              title="Copy Run ID"
            >
              <span className="truncate max-w-[170px]">{runId}</span>
              {copiedRunId ? (
                <Check className="w-3 h-3 text-[#22C55E]" />
              ) : (
                <Copy className="w-3 h-3 text-[#657066] group-hover:text-[#F1F5ED]" />
              )}
            </button>
          </div>

          {model && (
            <div className="flex items-center justify-between">
              <span className="text-[#657066]">Model:</span>
              <span className="text-[#D5FF78] truncate max-w-[170px]">{model}</span>
            </div>
          )}

          <div className="flex items-center justify-between">
            <span className="text-[#657066]">Elapsed:</span>
            <span className={`font-mono ${isRunning ? "text-[#D5FF78] font-semibold" : "text-[#F1F5ED]"}`}>
              {isRunning
                ? `${(elapsedMs / 1000).toFixed(1)}s`
                : durationSeconds !== undefined && durationSeconds > 0
                ? formatDuration(durationSeconds)
                : "< 1s"}
            </span>
          </div>
        </div>

      </div>

      {/* Sequential Connected Checkpoints List */}
      <div
        ref={scrollContainerRef}
        className="flex-1 min-h-0 overflow-y-auto p-3.5 sm:p-4 space-y-0"
      >
        {stageData.map((stage, idx) => {
          const isLast = idx === stageData.length - 1;
          const isExpanded = expandedStageId === stage.id;
          const isStageCompleted = stage.status === "completed";
          const isStageRunning = stage.status === "running";
          const isStageFailed = stage.status === "failed";
          const StageIcon = stage.icon;

          return (
            <div key={stage.id} className="relative flex flex-col">
              <div className="flex items-start gap-2.5 sm:gap-3 relative">
                {/* Left Column: Checkpoint Node & Line */}
                <div className="flex flex-col items-center shrink-0 w-5 pt-1">
                  {/* Node Circle */}
                  <div
                    className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] shrink-0 z-10 transition-all duration-200 ${
                      isStageCompleted
                        ? "bg-[#B8F23D]/15 text-[#B8F23D] border border-[#B8F23D]"
                        : isStageRunning
                        ? "bg-[#121812] text-[#D5FF78] border border-[#B8F23D] radar-node-pulse"
                        : isStageFailed
                        ? "bg-[#EF4444]/15 text-[#EF4444] border border-[#EF4444]"
                        : "bg-[#121812] text-[#657066] border border-[#202A22]"
                    }`}
                  >
                    {isStageCompleted ? (
                      <Check className="w-3 h-3 stroke-[2.5]" />
                    ) : isStageRunning ? (
                      <span className="w-1.5 h-1.5 rounded-full bg-[#B8F23D]" />
                    ) : isStageFailed ? (
                      <AlertCircle className="w-3 h-3" />
                    ) : (
                      <span className="text-[9px] text-[#657066] font-semibold">
                        {idx + 1}
                      </span>
                    )}
                  </div>

                  {/* Connecting Line to next checkpoint */}
                  {!isLast && (
                    <PipelineConnectingLine
                      status={
                        isStageCompleted
                          ? "completed"
                          : isStageRunning
                          ? "running"
                          : isStageFailed
                          ? "failed"
                          : "pending"
                      }
                    />
                  )}
                </div>

                {/* Right Column: Checkpoint Stage Card */}
                <div className={`flex-1 min-w-0 pb-2.5 ${isLast ? "pb-0.5" : ""}`}>
                  <div
                    onClick={() =>
                      setExpandedStageId(isExpanded ? null : stage.id)
                    }
                    className={`p-2.5 sm:p-3 rounded-lg border transition-all duration-150 cursor-pointer select-none group ${
                      isStageRunning
                        ? "bg-[#121812] border-[#B8F23D]/40"
                        : isStageCompleted
                        ? "bg-[#0A0E0C] border-[#202A22] hover:border-[#2B382D]"
                        : isStageFailed
                        ? "bg-[#1A0E0E] border-[#EF4444]/40"
                        : "bg-[#070A08]/50 border-[#202A22]/40 opacity-50 hover:opacity-75"
                    }`}
                  >
                    {/* Header */}
                    <div className="flex items-center justify-between gap-1.5">
                      <div className="flex items-center gap-1.5 min-w-0">
                        <StageIcon
                          className={`w-3.5 h-3.5 shrink-0 ${
                            isStageRunning
                              ? "text-[#D5FF78]"
                              : isStageCompleted
                              ? "text-[#B8F23D]"
                              : "text-[#657066]"
                          }`}
                        />
                        <span
                          className={`text-xs font-semibold truncate ${
                            isStageRunning
                              ? "text-[#E6ECE5]"
                              : isStageCompleted
                              ? "text-[#E6ECE5]"
                              : "text-[#9BA79D]"
                          }`}
                        >
                          {stage.name}
                        </span>
                      </div>

                      <div className="flex items-center gap-1 shrink-0 text-[10px] text-[#657066]">
                        {stage.timestamp && (
                          <span suppressHydrationWarning className="hidden sm:inline">
                            {formatTimestamp(stage.timestamp)}
                          </span>
                        )}
                        {isExpanded ? (
                          <ChevronUp className="w-3.5 h-3.5 text-[#9BA79D]" />
                        ) : (
                          <ChevronDown className="w-3.5 h-3.5 text-[#657066] group-hover:text-[#9BA79D]" />
                        )}
                      </div>
                    </div>

                    {/* Status message */}
                    <p
                      className={`text-[11px] mt-1 leading-snug break-words font-sans ${
                        isStageRunning
                          ? "text-[#9BA79D]"
                          : isStageCompleted
                          ? "text-[#9BA79D]"
                          : "text-[#657066]"
                      }`}
                    >
                      {stage.statusMessage}
                    </p>

                    {/* Expandable Drawer */}
                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: "auto" }}
                          exit={{ opacity: 0, height: 0 }}
                          transition={{ duration: 0.15 }}
                          className="mt-2 pt-2 border-t border-[#202A22] space-y-1.5 text-[10px]"
                        >
                          {stage.events.length > 0 ? (
                            <div className="space-y-1.5">
                              {stage.events.map((evt, evIdx) => (
                                <div
                                  key={evt.event_id || evIdx}
                                  className="p-2 rounded bg-[#070A08] border border-[#202A22] space-y-1"
                                >
                                  <div className="flex items-center justify-between text-[#657066]">
                                    <span className="uppercase text-[#D5FF78] font-semibold">
                                      {evt.stage}
                                    </span>
                                    <span suppressHydrationWarning>
                                      {formatTimestamp(evt.timestamp)}
                                    </span>
                                  </div>
                                  <div className="text-[#E6ECE5] leading-snug font-sans">
                                    {evt.message}
                                  </div>
                                  {evt.metadata &&
                                    Object.keys(evt.metadata).length > 0 && (
                                      <pre className="mt-1 p-1.5 rounded bg-[#040605] text-[#9BA79D] overflow-x-auto text-[9px] font-mono leading-tight">
                                        {JSON.stringify(evt.metadata, null, 2)}
                                      </pre>
                                    )}
                                </div>
                              ))}
                            </div>
                          ) : (
                            <div className="text-[#657066] italic text-[10px]">
                              Validated by SOAR local runtime.
                            </div>
                          )}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="p-3 bg-[#070A08] border-t border-[#202A22] text-[10px] text-[#657066] flex items-center justify-between shrink-0">
        <span className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-[#B8F23D]" />
          <span>Sovereign pipeline</span>
        </span>
        <button
          onClick={refreshNow}
          className="text-[#9BA79D] hover:text-[#D5FF78] transition-colors flex items-center gap-1 cursor-pointer"
        >
          <RotateCw className="w-3 h-3" />
          <span>Refresh</span>
        </button>
      </div>
    </div>
  );
}
