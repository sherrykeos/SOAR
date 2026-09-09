"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ListTodo,
  Search,
  CheckCircle2,
  AlertCircle,
  Clock,
  ArrowRight,
  Plus,
  Info,
} from "lucide-react";
import { useWorkbench } from "@/context/WorkbenchContext";
import { formatTimestamp, formatDuration } from "@/lib/utils/formatters";
import { EmptyState } from "@/components/ui/EmptyState";

export default function TasksHistoryPage() {
  const router = useRouter();
  const { sessionTasks, setActiveRunId } = useWorkbench();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const filteredTasks = sessionTasks.filter((task) => {
    const matchesSearch =
      task.task.toLowerCase().includes(search.toLowerCase()) ||
      task.run_id.toLowerCase().includes(search.toLowerCase()) ||
      task.model.toLowerCase().includes(search.toLowerCase());

    const matchesStatus =
      statusFilter === "all" || task.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-6xl mx-auto w-full font-sans">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#202A22]">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-[#F1F5ED]">
            Task History
          </h1>
          <p className="text-xs text-[#9BA79D] mt-1">
            Browse and inspect autonomous tasks executed through the SOAR orchestrator.
          </p>
        </div>

        <Link
          href="/app"
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-[#B8F23D] text-[#070A08] font-semibold text-xs hover:bg-[#D5FF78] transition shadow-sm self-start sm:self-auto"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>New Task</span>
        </Link>
      </div>

      {/* Persistence Architecture Notice */}
      <div className="p-3 rounded-lg bg-[#0D120F] border border-[#202A22] text-xs font-mono text-[#9BA79D] flex items-center gap-2.5">
        <Info className="w-4 h-4 text-[#B8F23D] shrink-0" />
        <span>
          Displaying runs recorded in this workstation session. Persistent multi-session task store is architected for future backend database synchronization.
        </span>
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-[#657066] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search tasks by prompt, run ID, or model..."
            className="w-full bg-[#0D120F] border border-[#202A22] rounded-lg pl-9 pr-4 py-2 text-xs text-[#F1F5ED] placeholder:text-[#657066] focus:outline-none focus:border-[#B8F23D]/50 font-mono"
          />
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <button
            onClick={() => setStatusFilter("all")}
            className={`px-3 py-2 rounded-lg border transition ${
              statusFilter === "all"
                ? "bg-[#171E18] text-[#D5FF78] border-[#B8F23D]/40"
                : "bg-[#0D120F] text-[#9BA79D] border-[#202A22] hover:text-[#F1F5ED]"
            }`}
          >
            All ({sessionTasks.length})
          </button>
          <button
            onClick={() => setStatusFilter("completed")}
            className={`px-3 py-2 rounded-lg border transition ${
              statusFilter === "completed"
                ? "bg-[#171E18] text-[#4ADE80] border-[#22C55E]/40"
                : "bg-[#0D120F] text-[#9BA79D] border-[#202A22] hover:text-[#F1F5ED]"
            }`}
          >
            Completed
          </button>
          <button
            onClick={() => setStatusFilter("failed")}
            className={`px-3 py-2 rounded-lg border transition ${
              statusFilter === "failed"
                ? "bg-[#171E18] text-[#FCA5A5] border-[#EF4444]/40"
                : "bg-[#0D120F] text-[#9BA79D] border-[#202A22] hover:text-[#F1F5ED]"
            }`}
          >
            Failed
          </button>
        </div>
      </div>

      {/* Task List Table */}
      {filteredTasks.length === 0 ? (
        <EmptyState
          icon={<ListTodo className="w-6 h-6" />}
          title="No tasks found"
          description={
            search
              ? "No tasks match your search filter."
              : "No work has been executed yet in this session. Start a new job."
          }
          action={
            <Link
              href="/app"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#121812] border border-[#202A22] hover:border-[#B8F23D]/40 text-xs font-mono text-[#F1F5ED] hover:text-[#D5FF78] transition"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Create Task</span>
            </Link>
          }
        />
      ) : (
        <div className="rounded-xl bg-[#0D120F] border border-[#202A22] overflow-hidden font-mono text-xs">
          <div className="divide-y divide-[#202A22]">
            {filteredTasks.map((task) => (
              <div
                key={task.run_id}
                onClick={() => {
                  setActiveRunId(task.run_id);
                  router.push(`/app/tasks/${encodeURIComponent(task.run_id)}`);
                }}
                className="p-4 hover:bg-[#121812] transition-colors cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-3"
              >
                <div className="flex items-start gap-3 min-w-0">
                  <div className="mt-0.5 shrink-0">
                    {task.status === "completed" ? (
                      <CheckCircle2 className="w-4 h-4 text-[#22C55E]" />
                    ) : task.status === "failed" ? (
                      <AlertCircle className="w-4 h-4 text-[#EF4444]" />
                    ) : (
                      <Clock className="w-4 h-4 text-[#B8F23D] animate-pulse" />
                    )}
                  </div>

                  <div className="min-w-0">
                    <div className="text-xs font-semibold text-[#F1F5ED] truncate font-sans">
                      {task.task}
                    </div>
                    <div className="flex flex-wrap items-center gap-2 text-[11px] text-[#657066] mt-1">
                      <span className="text-[#9BA79D]">{task.run_id}</span>
                      <span>·</span>
                      <span className="text-[#D5FF78]">{task.model}</span>
                      {task.duration_seconds !== undefined && task.duration_seconds > 0 && (
                        <>
                          <span>·</span>
                          <span>{formatDuration(task.duration_seconds)}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0 self-end sm:self-center">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold border ${
                      task.status === "completed"
                        ? "bg-[#22C55E]/10 text-[#4ADE80] border-[#22C55E]/30"
                        : task.status === "failed"
                        ? "bg-[#EF4444]/10 text-[#FCA5A5] border-[#EF4444]/30"
                        : "bg-[#B8F23D]/10 text-[#D5FF78] border-[#B8F23D]/30"
                    }`}
                  >
                    {task.status}
                  </span>
                  <span className="text-[#657066] text-[11px]">
                    {formatTimestamp(task.created_at)}
                  </span>
                  <ArrowRight className="w-3.5 h-3.5 text-[#657066] group-hover:text-[#F1F5ED]" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
