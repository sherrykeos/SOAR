"use client";

import React from "react";
import Link from "next/link";
import {
  Sparkles,
  FileSearch,
  FlaskConical,
  ClipboardList,
  Code2,
  Clock,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  RotateCw,
} from "lucide-react";
import { TaskComposer } from "@/components/tasks/TaskComposer";
import { RunInspector } from "@/components/inspector/RunInspector";
import { useWorkbench } from "@/context/WorkbenchContext";
import { formatTimestamp, formatDuration } from "@/lib/utils/formatters";

export default function WorkbenchHomePage() {
  const {
    sessionTasks,
    activeRunId,
    setActiveRunId,
    getTaskByRunId,
    isBackendOnline,
    checkHealth,
  } = useWorkbench();

  const activeTask = activeRunId ? getTaskByRunId(activeRunId) : sessionTasks[0];

  const suggestions = [
    {
      label: "Analyze Inspection Report",
      icon: FileSearch,
      prompt:
        "Analyze the uploaded ultrasonic scan report, check tolerance thresholds against ISO standards, and draft an approval memo.",
    },
    {
      label: "Research Catalyst Performance",
      icon: FlaskConical,
      prompt:
        "Retrieve internal operational logs and summarize catalyst deactivation rates in refinery hydrocracker reactor unit 4.",
    },
    {
      label: "Generate Maintenance Checklist",
      icon: ClipboardList,
      prompt:
        "Compile a comprehensive preventative maintenance procedure checklist for high-pressure centrifugal turbine compressors.",
    },
    {
      label: "Build Data Processing Script",
      icon: Code2,
      prompt:
        "Write and test a Python script to parse CSV vibration logs, detect anomalies exceeding 4.5 mm/s, and output a clean JSON summary.",
    },
  ];

  const handleSelectSuggestion = (promptText: string) => {
    // Fill into composer if possible or trigger
    const textarea = document.querySelector("textarea");
    if (textarea) {
      textarea.value = promptText;
      textarea.focus();
      // Dispatch input event to sync React state
      textarea.dispatchEvent(new Event("input", { bubbles: true }));
    }
  };

  return (
    <div className="flex-1 flex flex-col xl:flex-row min-w-0 min-h-[calc(100vh-3.5rem)]">
      {/* Center Main Workspace Area */}
      <div className="flex-1 flex flex-col min-w-0 p-4 sm:p-6 lg:p-8 space-y-6 overflow-y-auto">
        {/* Header Greeting */}
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-xs font-mono text-[#B8F23D]">
            <Sparkles className="w-3.5 h-3.5" />
            <span>SOVEREIGN WORKBENCH</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#F1F5ED]">
            Give SOAR something to work on.
          </h1>
          <p className="text-xs sm:text-sm text-[#9BA79D]">
            Turn complex engineering, research, and analysis tasks into verified deliverables on your machine.
          </p>
        </div>

        {/* Backend Warning Banner if offline */}
        {!isBackendOnline && (
          <div className="p-3.5 rounded-xl bg-[#EF4444]/10 border border-[#EF4444]/30 flex items-center justify-between gap-3 text-xs font-mono text-[#EF4444]">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>
                SOAR backend is offline. Start your local FastAPI server at{" "}
                <code>http://localhost:8000</code>.
              </span>
            </div>
            <button
              onClick={checkHealth}
              className="px-2.5 py-1 rounded bg-[#EF4444]/20 hover:bg-[#EF4444]/30 border border-[#EF4444]/40 text-[#F1F5ED] text-[11px] transition shrink-0 flex items-center gap-1"
            >
              <RotateCw className="w-3 h-3" />
              <span>Retry</span>
            </button>
          </div>
        )}

        {/* Primary Task Composer */}
        <div className="space-y-2">
          <TaskComposer
            onTaskStarted={(task) => {
              setActiveRunId(task.run_id);
            }}
          />
        </div>

        {/* Suggested Quick Actions */}
        <div className="space-y-2.5">
          <div className="text-[11px] font-mono text-[#657066] uppercase tracking-wider font-semibold">
            Suggested Quick Actions
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {suggestions.map((s) => {
              const Icon = s.icon;
              return (
                <button
                  key={s.label}
                  onClick={() => handleSelectSuggestion(s.prompt)}
                  className="p-3 rounded-lg bg-[#0D120F] border border-[#202A22] hover:border-[#B8F23D]/40 hover:bg-[#121812] transition-all text-left group flex items-start gap-3 cursor-pointer"
                >
                  <div className="p-2 rounded bg-[#121812] border border-[#202A22] text-[#9BA79D] group-hover:text-[#B8F23D] group-hover:border-[#B8F23D]/30 transition shrink-0 mt-0.5">
                    <Icon className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-[#F1F5ED] group-hover:text-white transition">
                      {s.label}
                    </div>
                    <div className="text-[11px] text-[#657066] line-clamp-2 mt-0.5 leading-snug">
                      {s.prompt}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Active Task Result View (if an active task is selected) */}
        {activeTask && (
          <div className="p-5 rounded-xl bg-[#0D120F] border border-[#202A22] space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-[#202A22]">
              <div>
                <span className="text-[10px] font-mono uppercase text-[#B8F23D] tracking-wider font-bold">
                  ACTIVE TASK RESULT
                </span>
                <h3 className="text-sm font-semibold text-[#F1F5ED] mt-0.5">
                  {activeTask.task}
                </h3>
              </div>
              <div className="flex items-center gap-2 font-mono text-[11px]">
                <span
                  className={`px-2 py-0.5 rounded uppercase font-bold text-[10px] ${
                    activeTask.status === "completed"
                      ? "bg-[#22C55E]/15 text-[#4ADE80] border border-[#22C55E]/30"
                      : activeTask.status === "failed"
                      ? "bg-[#EF4444]/15 text-[#FCA5A5] border border-[#EF4444]/30"
                      : "bg-[#B8F23D]/15 text-[#D5FF78] border border-[#B8F23D]/30"
                  }`}
                >
                  {activeTask.status}
                </span>
                <Link
                  href={`/app/tasks/${activeTask.run_id}`}
                  className="text-[#9BA79D] hover:text-[#D5FF78] flex items-center gap-1 transition"
                >
                  <span>Full View</span>
                  <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
            </div>

            {/* Answer Display */}
            <div className="p-4 rounded-lg bg-[#070A08] border border-[#202A22] text-xs text-[#F1F5ED] leading-relaxed whitespace-pre-wrap font-mono">
              {activeTask.answer || "Executing pipeline..."}
            </div>

            {/* Task Footnote */}
            <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono text-[#657066]">
              <span>Model: <strong className="text-[#9BA79D]">{activeTask.model}</strong></span>
              <span>Created: {formatTimestamp(activeTask.created_at)}</span>
              {activeTask.duration_seconds !== undefined && activeTask.duration_seconds > 0 && (
                <span>Duration: {formatDuration(activeTask.duration_seconds)}</span>
              )}
            </div>
          </div>
        )}

        {/* Recent Session Tasks */}
        <div className="space-y-3 pt-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono text-[#657066] uppercase tracking-wider font-semibold">
              Recent Session Runs ({sessionTasks.length})
            </span>
            {sessionTasks.length > 0 && (
              <Link
                href="/app/tasks"
                className="text-xs font-mono text-[#9BA79D] hover:text-[#D5FF78] flex items-center gap-1 transition"
              >
                <span>View all</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            )}
          </div>

          {sessionTasks.length === 0 ? (
            <div className="p-8 rounded-xl bg-[#0D120F]/50 border border-[#202A22] text-center font-mono text-xs text-[#657066]">
              No tasks have been executed in this session yet. Submit a job above.
            </div>
          ) : (
            <div className="space-y-2">
              {sessionTasks.slice(0, 4).map((task) => {
                const isSelected = activeRunId === task.run_id;
                return (
                  <div
                    key={task.run_id}
                    onClick={() => setActiveRunId(task.run_id)}
                    className={`p-3.5 rounded-lg border transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                      isSelected
                        ? "bg-[#121812] border-[#B8F23D]/40 shadow-sm"
                        : "bg-[#0D120F] border-[#202A22] hover:border-[#2B382D] hover:bg-[#121812]/50"
                    }`}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      {task.status === "completed" ? (
                        <CheckCircle2 className="w-4 h-4 text-[#22C55E] shrink-0" />
                      ) : task.status === "failed" ? (
                        <AlertCircle className="w-4 h-4 text-[#EF4444] shrink-0" />
                      ) : (
                        <Clock className="w-4 h-4 text-[#B8F23D] shrink-0 animate-pulse" />
                      )}
                      <div className="min-w-0">
                        <div className="text-xs font-semibold text-[#F1F5ED] truncate">
                          {task.task}
                        </div>
                        <div className="text-[11px] font-mono text-[#657066] flex items-center gap-2 mt-0.5">
                          <span>{task.run_id}</span>
                          <span>·</span>
                          <span className="text-[#9BA79D]">{task.model}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 font-mono text-[11px] shrink-0">
                      <span className="text-[#657066]" suppressHydrationWarning>
                        {formatTimestamp(task.created_at)}
                      </span>
                      <Link
                        href={`/app/tasks/${task.run_id}`}
                        onClick={(e) => e.stopPropagation()}
                        className="p-1 rounded text-[#9BA79D] hover:text-[#D5FF78] transition"
                        title="View details"
                      >
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Right Column: Run Inspector Sidebar */}
      <div className="w-full xl:w-96 shrink-0 xl:border-l border-[#202A22] bg-[#0D120F]">
        <RunInspector
          runId={activeTask ? activeTask.run_id : null}
          taskTitle={activeTask?.task}
          taskStatus={activeTask?.status}
          initialEvents={activeTask?.events || []}
          model={activeTask?.model}
          durationSeconds={activeTask?.duration_seconds}
        />
      </div>
    </div>
  );
}
