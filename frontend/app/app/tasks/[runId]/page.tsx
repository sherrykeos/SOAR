"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  RotateCw,
  Copy,
  Check,
  Cpu,
  Clock,
  FileText,
} from "lucide-react";
import { useWorkbench } from "@/context/WorkbenchContext";
import { RunInspector } from "@/components/inspector/RunInspector";
import { getTaskEvents } from "@/lib/api/tasks";
import { formatDate, formatDuration } from "@/lib/utils/formatters";
import type { EventItem } from "@/types";

export default function TaskDetailPage() {
  const params = useParams();
  const router = useRouter();
  const runId = Array.isArray(params.runId) ? params.runId[0] : (params.runId as string);

  const { getTaskByRunId } = useWorkbench();
  const localRecord = getTaskByRunId(runId);

  const [events, setEvents] = useState<EventItem[]>(localRecord?.events || []);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let active = true;
    if (runId) {
      getTaskEvents(runId)
        .then((res) => {
          if (active && res && Array.isArray(res.events)) {
            setEvents(res.events);
          }
        })
        .catch(() => {});
    }
    return () => {
      active = false;
    };
  }, [runId]);

  const copyPrompt = () => {
    if (localRecord?.task) {
      navigator.clipboard.writeText(localRecord.task);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleRetry = () => {
    if (localRecord?.task) {
      router.push("/app");
      setTimeout(() => {
        const textarea = document.querySelector("textarea");
        if (textarea) {
          textarea.value = localRecord.task;
          textarea.focus();
          textarea.dispatchEvent(new Event("input", { bubbles: true }));
        }
      }, 100);
    }
  };

  return (
    <div className="flex-1 flex flex-col xl:flex-row min-w-0 min-h-[calc(100vh-3.5rem)]">
      {/* Left / Center Content */}
      <div className="flex-1 p-4 sm:p-6 lg:p-8 space-y-6 overflow-y-auto font-sans">
        {/* Navigation Breadcrumb */}
        <div className="flex items-center justify-between pb-4 border-b border-[#202A22]">
          <Link
            href="/app/tasks"
            className="inline-flex items-center gap-2 text-xs font-mono text-[#9BA79D] hover:text-[#F1F5ED] transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Tasks</span>
          </Link>

          <div className="flex items-center gap-2">
            <button
              onClick={handleRetry}
              className="px-3 py-1.5 rounded-lg bg-[#121812] border border-[#202A22] hover:border-[#B8F23D]/40 text-xs font-mono text-[#F1F5ED] hover:text-[#D5FF78] transition flex items-center gap-1.5 cursor-pointer"
            >
              <RotateCw className="w-3 h-3" />
              <span>Re-run Task</span>
            </button>
          </div>
        </div>

        {/* Task Title & Metadata */}
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
            <span className="px-2 py-0.5 rounded bg-[#171E18] text-[#D5FF78] border border-[#B8F23D]/30 text-[11px] font-bold">
              RUN: {runId}
            </span>
            <span
              className={`px-2 py-0.5 rounded uppercase font-bold text-[10px] ${
                localRecord?.status === "completed"
                  ? "bg-[#22C55E]/15 text-[#4ADE80] border border-[#22C55E]/30"
                  : localRecord?.status === "failed"
                  ? "bg-[#EF4444]/15 text-[#FCA5A5] border border-[#EF4444]/30"
                  : "bg-[#B8F23D]/15 text-[#D5FF78] border border-[#B8F23D]/30"
              }`}
            >
              {localRecord?.status || "INSPECT"}
            </span>
          </div>

          <h1 className="text-xl sm:text-2xl font-bold text-[#F1F5ED] leading-snug">
            {localRecord?.task || `Task Run ${runId}`}
          </h1>

          <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-[#657066] pt-1">
            {localRecord?.model && (
              <span className="flex items-center gap-1.5 text-[#9BA79D]">
                <Cpu className="w-3.5 h-3.5 text-[#B8F23D]" />
                {localRecord.model}
              </span>
            )}
            {localRecord?.created_at && (
              <span className="flex items-center gap-1.5" suppressHydrationWarning>
                <Clock className="w-3.5 h-3.5" />
                {formatDate(localRecord.created_at)}
              </span>
            )}
            {localRecord?.duration_seconds !== undefined && localRecord.duration_seconds > 0 && (
              <span>Duration: {formatDuration(localRecord.duration_seconds)}</span>
            )}
          </div>
        </div>

        {/* User Prompt Box */}
        {localRecord?.task && (
          <div className="p-4 rounded-xl bg-[#0D120F] border border-[#202A22] space-y-2 font-mono text-xs">
            <div className="flex items-center justify-between text-[#657066] text-[10px] uppercase font-bold">
              <span>USER PROMPT</span>
              <button
                onClick={copyPrompt}
                className="text-[#9BA79D] hover:text-[#F1F5ED] flex items-center gap-1 transition cursor-pointer"
              >
                {copied ? <Check className="w-3 h-3 text-[#22C55E]" /> : <Copy className="w-3 h-3" />}
                <span>{copied ? "Copied" : "Copy"}</span>
              </button>
            </div>
            <p className="text-xs text-[#F1F5ED] leading-relaxed whitespace-pre-wrap font-sans">
              {localRecord.task}
            </p>
          </div>
        )}

        {/* Answer / Output Box */}
        <div className="p-5 rounded-xl bg-[#0D120F] border border-[#202A22] space-y-3 font-mono text-xs">
          <div className="flex items-center justify-between pb-2 border-b border-[#202A22]">
            <span className="text-[10px] uppercase font-bold text-[#B8F23D]">
              GENERATED OUTPUT & RESULTS
            </span>
            {localRecord?.execution_mode && (
              <span className="text-[10px] text-[#657066] uppercase">
                Mode: {localRecord.execution_mode}
              </span>
            )}
          </div>

          <div className="p-4 rounded-lg bg-[#070A08] border border-[#202A22] text-[#F1F5ED] leading-relaxed whitespace-pre-wrap">
            {localRecord?.answer ||
              (events.length > 0
                ? "Review the execution checkpoint DAG in the right panel for incremental logs."
                : "No answer recorded for this task.")}
          </div>
        </div>

        {/* Attached or Referenced Files */}
        {localRecord?.attached_files && localRecord.attached_files.length > 0 && (
          <div className="p-4 rounded-xl bg-[#0D120F] border border-[#202A22] space-y-3 font-mono text-xs">
            <div className="text-[10px] uppercase font-bold text-[#9BA79D]">
              REFERENCED WORKSPACE FILES
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {localRecord.attached_files.map((file) => (
                <div
                  key={file}
                  className="p-2.5 rounded-lg bg-[#121812] border border-[#202A22] flex items-center gap-2 text-xs text-[#F1F5ED]"
                >
                  <FileText className="w-4 h-4 text-[#B8F23D] shrink-0" />
                  <span className="truncate">{file}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Right Column: Run Inspector */}
      <div className="w-full xl:w-96 shrink-0 xl:border-l border-[#202A22] bg-[#0D120F]">
        <RunInspector
          runId={runId}
          taskStatus={localRecord?.status || "completed"}
          initialEvents={events}
          model={localRecord?.model}
          durationSeconds={localRecord?.duration_seconds}
        />
      </div>
    </div>
  );
}
