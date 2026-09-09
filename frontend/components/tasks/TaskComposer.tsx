"use client";

import React, { useState, useRef } from "react";
import {
  ArrowRight,
  Paperclip,
  Cpu,
  X,
  FileText,
  Loader2,
  Sparkles,
  ChevronDown,
} from "lucide-react";
import { useWorkbench } from "@/context/WorkbenchContext";
import { useToast } from "@/components/ui/Toast";
import { createTask } from "@/lib/api/tasks";
import { uploadFile } from "@/lib/api/files";
import type { ClientTaskRecord, EventItem } from "@/types";

export interface TaskComposerProps {
  onTaskStarted?: (record: ClientTaskRecord) => void;
  className?: string;
}

export function TaskComposer({ onTaskStarted, className }: TaskComposerProps) {
  const {
    models,
    defaultModel,
    selectedModel,
    setSelectedModel,
    addSessionTask,
    setActiveRunId,
    setInspectorOpen,
    isBackendOnline,
  } = useWorkbench();

  const { success, error, info } = useToast();

  const [prompt, setPrompt] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [attachedFiles, setAttachedFiles] = useState<string[]>([]);
  const [modelDropdownOpen, setModelDropdownOpen] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);
    try {
      for (let i = 0; i < files.length; i++) {
        const f = files[i];
        const uploaded = await uploadFile(f);
        setAttachedFiles((prev) => [...prev, uploaded.original_filename]);
        success("File uploaded", uploaded.original_filename);
      }
    } catch (err) {
      error("Upload failed", err instanceof Error ? err.message : "Could not upload file");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const removeFile = (filename: string) => {
    setAttachedFiles((prev) => prev.filter((f) => f !== filename));
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();

    const trimmed = prompt.trim();
    if (!trimmed || isRunning) return;

    if (!isBackendOnline) {
      error("Backend offline", "The local SOAR backend is unreachable. Please ensure it is running.");
      return;
    }

    setIsRunning(true);

    // Append attached file references if any
    let finalPrompt = trimmed;
    if (attachedFiles.length > 0) {
      finalPrompt += `\n[Attached local files: ${attachedFiles.join(", ")}]`;
    }

    const modelOverride = selectedModel === "auto" ? null : selectedModel;

    try {
      info("Task submitted", "Dispatching to SOAR local orchestrator...");

      const response = await createTask({
        task: finalPrompt,
        model: modelOverride,
      });

      const initialEvents: EventItem[] = (response.events || []).map(
        (e: Record<string, unknown>, idx: number) => ({
          event_id: String(e.event_id || `evt-${idx}`),
          run_id: response.run_id,
          stage: String(e.stage || "TASK_EXECUTION"),
          status: String(e.status || "completed"),
          message: String(e.message || ""),
          timestamp: String(e.timestamp || new Date().toISOString()),
          metadata: (e.metadata as Record<string, unknown>) || {},
        })
      );

      const taskRecord: ClientTaskRecord = {
        run_id: response.run_id,
        task: trimmed,
        model: response.model || selectedModel,
        status: response.status === "failed" ? "failed" : "completed",
        created_at: new Date().toISOString(),
        duration_seconds:
          typeof response.model_details === "object" &&
          response.model_details !== null &&
          "duration_seconds" in response.model_details &&
          typeof response.model_details.duration_seconds === "number"
            ? response.model_details.duration_seconds
            : 0,
        answer: response.answer,
        events: initialEvents,
        attached_files: attachedFiles,
        execution_mode: response.execution_mode,
      };

      addSessionTask(taskRecord);
      setActiveRunId(response.run_id);
      setInspectorOpen(true);
      onTaskStarted?.(taskRecord);

      if (response.status === "failed") {
        error("Execution completed with error", response.answer || "Task failed");
      } else {
        success("Task completed", `Run ID: ${response.run_id}`);
      }

      setPrompt("");
      setAttachedFiles([]);
    } catch (err) {
      error(
        "Task execution failed",
        err instanceof Error ? err.message : "Internal error during task execution"
      );
    } finally {
      setIsRunning(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div
      className={`rounded-xl bg-[#0D120F] border border-[#202A22] focus-within:border-[#B8F23D]/50 focus-within:ring-1 focus-within:ring-[#B8F23D]/30 transition-all p-4 shadow-xl ${
        className || ""
      }`}
    >
      {/* Attached file chips */}
      {attachedFiles.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3 pb-2 border-b border-[#202A22]/60">
          <span className="text-[10px] font-mono text-[#657066] uppercase self-center">
            Attached:
          </span>
          {attachedFiles.map((file) => (
            <div
              key={file}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#171E18] text-[#F1F5ED] text-xs font-mono border border-[#202A22]"
            >
              <FileText className="w-3.5 h-3.5 text-[#B8F23D]" />
              <span className="truncate max-w-[200px]">{file}</span>
              <button
                type="button"
                onClick={() => removeFile(file)}
                className="text-[#657066] hover:text-[#EF4444] transition-colors ml-1"
                aria-label="Remove file"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Main Textarea */}
      <textarea
        ref={textareaRef}
        rows={3}
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Describe what you want SOAR to do... (e.g. 'Analyze inspection report and create an approval note')"
        disabled={isRunning}
        className="w-full bg-transparent text-sm text-[#F1F5ED] placeholder:text-[#657066] focus:outline-none resize-none leading-relaxed font-sans"
      />

      {/* Bottom Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-3 mt-1 border-t border-[#202A22]/50 font-mono text-xs">
        <div className="flex items-center gap-2">
          {/* File Attach Hidden Input */}
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={handleFileUpload}
          />

          {/* Attach Button */}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading || isRunning}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-[#121812] border border-[#202A22] text-[#9BA79D] hover:text-[#F1F5ED] hover:border-[#2B382D] transition-colors cursor-pointer disabled:opacity-50"
          >
            {isUploading ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin text-[#B8F23D]" />
            ) : (
              <Paperclip className="w-3.5 h-3.5" />
            )}
            <span className="text-[11px]">Attach</span>
          </button>

          {/* Model Selector Dropdown */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setModelDropdownOpen(!modelDropdownOpen)}
              disabled={isRunning}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-[#121812] border border-[#202A22] text-[#9BA79D] hover:text-[#F1F5ED] hover:border-[#2B382D] transition-colors cursor-pointer"
            >
              <Cpu className="w-3.5 h-3.5 text-[#B8F23D]" />
              <span className="text-[11px] truncate max-w-[140px]">
                {selectedModel === "auto"
                  ? `Auto (${defaultModel || "route"})`
                  : selectedModel}
              </span>
              <ChevronDown className="w-3 h-3 text-[#657066]" />
            </button>

            {modelDropdownOpen && (
              <div className="absolute bottom-full mb-1 left-0 z-50 w-56 rounded-lg bg-[#0D120F] border border-[#202A22] shadow-2xl p-1 font-mono text-xs space-y-0.5">
                <button
                  type="button"
                  onClick={() => {
                    setSelectedModel("auto");
                    setModelDropdownOpen(false);
                  }}
                  className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-left transition-colors ${
                    selectedModel === "auto"
                      ? "bg-[#171E18] text-[#D5FF78]"
                      : "text-[#9BA79D] hover:bg-[#121812] hover:text-[#F1F5ED]"
                  }`}
                >
                  <span>Auto-route (Default)</span>
                  <Sparkles className="w-3 h-3 text-[#B8F23D]" />
                </button>

                {models.map((m) => (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => {
                      setSelectedModel(m.id);
                      setModelDropdownOpen(false);
                    }}
                    className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-left transition-colors ${
                      selectedModel === m.id
                        ? "bg-[#171E18] text-[#D5FF78]"
                        : "text-[#9BA79D] hover:bg-[#121812] hover:text-[#F1F5ED]"
                    }`}
                  >
                    <span className="truncate">{m.id}</span>
                    <span className="text-[9px] text-[#657066] uppercase">
                      {m.provider}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Execute Button */}
        <button
          type="button"
          onClick={() => handleSubmit()}
          disabled={!prompt.trim() || isRunning}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#B8F23D] text-[#070A08] font-bold text-xs hover:bg-[#D5FF78] transition-all disabled:opacity-40 disabled:pointer-events-none shadow-[0_0_20px_-4px_rgba(184,242,61,0.4)] cursor-pointer"
        >
          {isRunning ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Executing...</span>
            </>
          ) : (
            <>
              <span>Execute Work</span>
              <kbd className="hidden sm:inline text-[10px] bg-[#070A08]/15 px-1 rounded font-mono">
                ⌘↵
              </kbd>
              <ArrowRight className="w-3.5 h-3.5" />
            </>
          )}
        </button>
      </div>
    </div>
  );
}
