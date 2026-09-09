"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  ArrowUp,
  Paperclip,
  X,
  FileText,
  RotateCcw,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Bot,
  User,
  Activity,
  Layers,
  FileSearch,
  FlaskConical,
  ClipboardList,
  Code2,
  Clock,
  Cpu,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";
import { useWorkbench } from "@/context/WorkbenchContext";
import { useToast } from "@/components/ui/Toast";
import { createTask, getTaskEvents } from "@/lib/api/tasks";
import { uploadFile } from "@/lib/api/files";
import { formatDuration, formatTimestamp } from "@/lib/utils/formatters";
import { MarkdownMessage } from "./MarkdownMessage";
import type { ClientTaskRecord, EventItem } from "@/types";
import { motion, AnimatePresence } from "framer-motion";

export function ChatInterface() {
  const {
    sessionTasks,
    activeRunId,
    setActiveRunId,
    addSessionTask,
    updateSessionTask,
    getTaskByRunId,
    models,
    defaultModel,
    selectedModel,
    setSelectedModel,
    setInspectorOpen,
  } = useWorkbench();

  const { success, error } = useToast();

  const [prompt, setPrompt] = useState("");
  const [isExecuting, setIsExecuting] = useState(false);
  const [attachedFiles, setAttachedFiles] = useState<{ id?: string; name: string; size?: number }[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [modelDropdownOpen, setModelDropdownOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const [thoughtExpanded, setThoughtExpanded] = useState(true);

  // Live events for currently executing or active task
  const [liveEvents, setLiveEvents] = useState<EventItem[]>([]);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Resolve currently displayed task
  const currentTask: ClientTaskRecord | undefined = activeRunId
    ? getTaskByRunId(activeRunId)
    : sessionTasks[0];

  const displayEvents = liveEvents.length > 0 ? liveEvents : (currentTask?.events || []);

  // Auto-scroll to bottom of messages when events or task updates
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [currentTask?.answer, displayEvents.length, isExecuting]);

  // Adjust textarea height automatically
  const handlePromptChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setPrompt(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  };

  const currentRunId = currentTask?.run_id;
  const currentStatus = currentTask?.status;

  // Poll events if task is in-progress
  useEffect(() => {
    if (!currentRunId || currentStatus === "completed" || currentStatus === "failed") {
      return;
    }

    let active = true;

    const poll = async () => {
      try {
        const res = await getTaskEvents(currentRunId);
        if (active && res && Array.isArray(res.events)) {
          setLiveEvents(res.events);
          updateSessionTask(currentRunId, { events: res.events });

          // Terminal events check
          const lastEvent = res.events[res.events.length - 1];
          if (lastEvent?.status === "completed" || lastEvent?.status === "failed") {
            setIsExecuting(false);
          }
        }
      } catch {
        // gracefully ignored
      }
    };

    poll();
    const interval = setInterval(poll, 1200);

    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [currentRunId, currentStatus, updateSessionTask]);

  // Handle file uploads
  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      try {
        const uploaded = await uploadFile(file);
        setAttachedFiles((prev) => [
          ...prev,
          {
            id: uploaded.file_id,
            name: uploaded.original_filename || file.name,
            size: uploaded.size_bytes || file.size,
          },
        ]);
        success("File attached", file.name);
      } catch {
        // Fallback local reference
        setAttachedFiles((prev) => [
          ...prev,
          {
            name: file.name,
            size: file.size,
          },
        ]);
      }
    }
    setIsUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const removeAttachedFile = (index: number) => {
    setAttachedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  // Execute task submission
  const handleSubmit = async () => {
    const query = prompt.trim();
    if (!query || isExecuting) return;

    setIsExecuting(true);
    setLiveEvents([]);

    const taskModel = selectedModel === "auto" ? defaultModel : selectedModel;
    const attachedFileNames = attachedFiles.map((f) => f.name);
    let finalTaskPrompt = query;
    if (attachedFileNames.length > 0) {
      finalTaskPrompt += `\n\n[Referenced Workspace Files: ${attachedFileNames.join(", ")}]`;
    }

    try {
      const res = await createTask({
        task: finalTaskPrompt,
        model: taskModel === "auto" ? null : taskModel,
      });

      const initialEvents: EventItem[] = (res.events || []).map(
        (e: Record<string, unknown>, idx: number) => ({
          event_id: String(e.event_id || `evt-${idx}`),
          run_id: res.run_id,
          stage: String(e.stage || "TASK_EXECUTION"),
          status: String(e.status || "completed"),
          message: String(e.message || ""),
          timestamp: String(e.timestamp || new Date().toISOString()),
          metadata: (e.metadata as Record<string, unknown>) || {},
        })
      );

      const newTaskRecord: ClientTaskRecord = {
        run_id: res.run_id,
        task: query,
        status: res.status === "failed" ? "failed" : "completed",
        model: res.model || taskModel,
        attached_files: attachedFileNames,
        answer: res.answer || "",
        created_at: new Date().toISOString(),
        execution_mode: res.execution_mode || "sandbox",
        events: initialEvents,
      };

      addSessionTask(newTaskRecord);
      setActiveRunId(res.run_id);
      setPrompt("");
      setAttachedFiles([]);
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }

      if (res.answer) {
        setIsExecuting(false);
      }
    } catch (err) {
      error("Execution Failed", err instanceof Error ? err.message : "Backend unavailable");
      setIsExecuting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const copyAnswer = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRetryPrompt = (prevPrompt: string) => {
    setPrompt(prevPrompt);
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  // 4 Default Starter Prompts
  const starterPrompts = [
    {
      title: "Security & Vulnerability Audit",
      description: "Scan code or logs for CVE exposure, secrets, and OWASP violations.",
      prompt: "Perform a comprehensive security audit of our application code, identifying potential vulnerabilities, hardcoded secrets, and unsafe dependencies.",
      icon: FileSearch,
    },
    {
      title: "Catalyst Performance Analysis",
      description: "Extract sensor time-series logs and summarize deactivation trends.",
      prompt: "Retrieve operational telemetry and analyze catalyst deactivation rates in refinery hydrocracker reactor unit 4 against ISO standards.",
      icon: FlaskConical,
    },
    {
      title: "Maintenance Procedure Checklist",
      description: "Draft step-by-step preventative inspection guide.",
      prompt: "Compile a detailed preventative maintenance and inspection checklist for high-pressure centrifugal turbine compressors.",
      icon: ClipboardList,
    },
    {
      title: "Build Data Anomaly Script",
      description: "Generate and test a sandboxed Python vibration parser.",
      prompt: "Write a complete Python script to parse CSV vibration logs, detect anomalies exceeding 4.5 mm/s, and output a clean summary JSON.",
      icon: Code2,
    },
  ];

  return (
    <div className="flex-1 flex flex-col h-[calc(100vh-3.5rem)] min-w-0 bg-[#070A08] relative font-sans">
      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 md:px-8 space-y-6">
        <div className="max-w-3xl mx-auto w-full space-y-6">
          {/* Welcome Screen when no active conversation exists */}
          {!currentTask ? (
            <div className="py-8 md:py-16 text-center space-y-6">
              <div className="inline-flex p-3 rounded-2xl bg-[#0D120F] border border-[#202A22] shadow-xl relative">
                <Sparkles className="w-8 h-8 text-[#B8F23D]" />
                <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-[#B8F23D] animate-ping" />
              </div>

              <div className="space-y-2">
                <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-[#F1F5ED]">
                  Sovereign Intelligence Engine
                </h1>
                <p className="text-sm text-[#9BA79D] max-w-md mx-auto leading-relaxed">
                  On-premise execution with zero external network traffic. Ask SOAR to research, analyze, create, build, or plan.
                </p>
              </div>

              {/* Starter Prompt Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-left pt-4">
                {starterPrompts.map((card) => {
                  const Icon = card.icon;
                  return (
                    <button
                      key={card.title}
                      onClick={() => {
                        setPrompt(card.prompt);
                        textareaRef.current?.focus();
                      }}
                      className="p-3.5 rounded-xl bg-[#0D120F] border border-[#202A22] hover:border-[#B8F23D]/50 hover:bg-[#121812] transition-all group cursor-pointer text-left flex items-start gap-3"
                    >
                      <div className="p-2 rounded-lg bg-[#121812] group-hover:bg-[#171E18] text-[#B8F23D] shrink-0 border border-[#202A22] transition-colors">
                        <Icon className="w-4 h-4" />
                      </div>
                      <div className="min-w-0">
                        <div className="text-xs font-semibold text-[#F1F5ED] group-hover:text-[#D5FF78] transition-colors">
                          {card.title}
                        </div>
                        <div className="text-[11px] text-[#657066] line-clamp-2 mt-0.5 leading-snug">
                          {card.description}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          ) : (
            /* Active Conversation Thread */
            <div className="space-y-6">
              {/* 1. User Message Card */}
              <div className="flex items-start gap-3 justify-end">
                <div className="max-w-2xl bg-[#0D120F] border border-[#202A22] rounded-2xl p-4 shadow-md space-y-2 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <span className="font-mono text-[10px] uppercase font-bold text-[#657066]">
                      YOU
                    </span>
                    <div className="w-6 h-6 rounded-full bg-[#121812] border border-[#202A22] flex items-center justify-center text-[#9BA79D]">
                      <User className="w-3.5 h-3.5" />
                    </div>
                  </div>

                  {/* Attached Files Pills */}
                  {currentTask.attached_files && currentTask.attached_files.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 justify-end pt-1">
                      {currentTask.attached_files.map((file) => (
                        <div
                          key={file}
                          className="flex items-center gap-1.5 px-2 py-1 rounded bg-[#121812] border border-[#202A22] text-[11px] text-[#9BA79D]"
                        >
                          <FileText className="w-3 h-3 text-[#B8F23D]" />
                          <span className="truncate max-w-[160px]">{file}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  <p className="text-sm text-[#F1F5ED] whitespace-pre-wrap leading-relaxed font-sans text-left">
                    {currentTask.task}
                  </p>
                </div>
              </div>

              {/* 2. Assistant Response Card */}
              <div className="flex items-start gap-3 justify-start">
                <div className="w-8 h-8 rounded-xl bg-[#0D120F] border border-[#202A22] flex items-center justify-center shrink-0 mt-1 shadow-md">
                  <Bot className="w-4 h-4 text-[#B8F23D]" />
                </div>

                <div className="flex-1 min-w-0 space-y-3">
                  {/* Thought & Pipeline Checkpoint Accordion (Claude/ChatGPT style) */}
                  {(displayEvents.length > 0 || isExecuting) && (
                    <div className="rounded-xl bg-[#0D120F] border border-[#202A22] overflow-hidden text-xs font-mono">
                      <button
                        onClick={() => setThoughtExpanded(!thoughtExpanded)}
                        className="w-full flex items-center justify-between p-3 bg-[#0A0E0C] hover:bg-[#121812] transition-colors cursor-pointer text-left"
                      >
                        <div className="flex items-center gap-2 min-w-0">
                          <Activity
                            className={`w-3.5 h-3.5 ${
                              isExecuting ? "text-[#B8F23D] animate-spin" : "text-[#9BA79D]"
                            }`}
                          />
                          <span className="font-bold text-[#F1F5ED] truncate">
                            {isExecuting
                              ? `Executing Pipeline (${displayEvents.length} stages)`
                              : `Workflow Completed (${displayEvents.length} stages)`}
                          </span>
                        </div>

                        <div className="flex items-center gap-2">
                          <span className="text-[10px] text-[#657066]">
                            {currentTask.duration_seconds
                              ? formatDuration(currentTask.duration_seconds)
                              : ""}
                          </span>
                          {thoughtExpanded ? (
                            <ChevronUp className="w-3.5 h-3.5 text-[#657066]" />
                          ) : (
                            <ChevronDown className="w-3.5 h-3.5 text-[#657066]" />
                          )}
                        </div>
                      </button>

                      <AnimatePresence>
                        {thoughtExpanded && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="p-3 border-t border-[#202A22] space-y-2 bg-[#0D120F]"
                          >
                            <div className="space-y-1.5">
                              {displayEvents.map((evt, idx) => (
                                <div
                                  key={evt.event_id || idx}
                                  className="flex items-center justify-between text-[11px] p-1.5 rounded bg-[#070A08] border border-[#202A22]/50"
                                >
                                  <div className="flex items-center gap-2 truncate">
                                    {evt.status === "completed" ? (
                                      <CheckCircle2 className="w-3.5 h-3.5 text-[#22C55E] shrink-0" />
                                    ) : evt.status === "failed" ? (
                                      <AlertCircle className="w-3.5 h-3.5 text-[#EF4444] shrink-0" />
                                    ) : (
                                      <Clock className="w-3.5 h-3.5 text-[#B8F23D] shrink-0 animate-pulse" />
                                    )}
                                    <span className="text-[#F1F5ED] font-semibold truncate">
                                      {evt.stage.replace(/_/g, " ")}
                                    </span>
                                  </div>
                                  <span className="text-[10px] text-[#657066] shrink-0 ml-2" suppressHydrationWarning>
                                    {formatTimestamp(evt.timestamp)}
                                  </span>
                                </div>
                              ))}
                            </div>

                            {/* View in Inspector Action */}
                            <div className="pt-2 flex justify-end">
                              <button
                                onClick={() => setInspectorOpen(true)}
                                className="flex items-center gap-1.5 text-[11px] text-[#B8F23D] hover:text-[#D5FF78] hover:underline cursor-pointer"
                              >
                                <Layers className="w-3 h-3" />
                                <span>Inspect in DAG Panel →</span>
                              </button>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  )}

                  {/* Generated Answer Content */}
                  <div className="p-4 md:p-5 rounded-2xl bg-[#0D120F] border border-[#202A22] shadow-xl">
                    {currentTask.answer ? (
                      <MarkdownMessage content={currentTask.answer} />
                    ) : isExecuting ? (
                      <div className="flex items-center gap-2 py-4 text-xs font-mono text-[#9BA79D]">
                        <span className="w-2 h-2 rounded-full bg-[#B8F23D] animate-ping" />
                        <span>Synthesizing response inside sovereign environment...</span>
                      </div>
                    ) : (
                      <div className="text-xs text-[#657066] font-mono">
                        Pipeline execution completed. Check checkpoints above for stage summaries.
                      </div>
                    )}

                    {/* Action Bar Beneath Response */}
                    {currentTask.answer && (
                      <div className="flex flex-wrap items-center justify-between gap-3 pt-4 mt-4 border-t border-[#202A22] text-xs font-mono">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => copyAnswer(currentTask.answer || "")}
                            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#121812] border border-[#202A22] hover:border-[#B8F23D]/40 text-[#9BA79D] hover:text-[#F1F5ED] transition cursor-pointer text-[11px]"
                            title="Copy answer"
                          >
                            {copied ? (
                              <>
                                <Check className="w-3 h-3 text-[#22C55E]" />
                                <span className="text-[#22C55E]">Copied</span>
                              </>
                            ) : (
                              <>
                                <Copy className="w-3 h-3" />
                                <span>Copy</span>
                              </>
                            )}
                          </button>

                          <button
                            onClick={() => handleRetryPrompt(currentTask.task)}
                            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#121812] border border-[#202A22] hover:border-[#B8F23D]/40 text-[#9BA79D] hover:text-[#F1F5ED] transition cursor-pointer text-[11px]"
                            title="Fork / Retry prompt"
                          >
                            <RotateCcw className="w-3 h-3" />
                            <span>Retry</span>
                          </button>

                          <button
                            onClick={() => setInspectorOpen(true)}
                            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#121812] border border-[#202A22] hover:border-[#B8F23D]/40 text-[#9BA79D] hover:text-[#F1F5ED] transition cursor-pointer text-[11px]"
                            title="Toggle Inspector"
                          >
                            <Activity className="w-3 h-3 text-[#B8F23D]" />
                            <span>DAG View</span>
                          </button>
                        </div>

                        {/* Model & duration tag */}
                        <div className="flex items-center gap-2 text-[10px] text-[#657066]">
                          <span className="text-[#D5FF78]">{currentTask.model}</span>
                          {currentTask.duration_seconds && (
                            <>
                              <span>·</span>
                              <span>{formatDuration(currentTask.duration_seconds)}</span>
                            </>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Pinned Bottom Input Container (ChatGPT / Claude style) */}
      <div className="p-4 md:p-6 bg-gradient-to-t from-[#070A08] via-[#070A08]/90 to-transparent shrink-0">
        <div className="max-w-3xl mx-auto w-full space-y-2">
          {/* Main Floating Input Card */}
          <div className="rounded-2xl bg-[#0D120F] border border-[#202A22] focus-within:border-[#B8F23D]/50 focus-within:ring-1 focus-within:ring-[#B8F23D]/20 shadow-2xl transition-all overflow-hidden p-3 space-y-2">
            {/* Attached Files Tray */}
            {attachedFiles.length > 0 && (
              <div className="flex flex-wrap gap-1.5 pb-2 border-b border-[#202A22]/60">
                {attachedFiles.map((file, idx) => (
                  <div
                    key={idx}
                    className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-[#121812] border border-[#202A22] text-xs font-mono text-[#F1F5ED]"
                  >
                    <FileText className="w-3.5 h-3.5 text-[#B8F23D]" />
                    <span className="truncate max-w-[180px]">{file.name}</span>
                    <button
                      onClick={() => removeAttachedFile(idx)}
                      className="p-0.5 rounded text-[#657066] hover:text-[#EF4444] transition"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Prompt Textarea */}
            <textarea
              ref={textareaRef}
              value={prompt}
              onChange={handlePromptChange}
              onKeyDown={handleKeyDown}
              placeholder="Ask SOAR to research, analyze, create, build, or plan... (Enter to send, Shift+Enter for newline)"
              rows={1}
              className="w-full bg-transparent border-0 resize-none text-sm text-[#F1F5ED] placeholder-[#657066] focus:outline-none leading-relaxed max-h-48 min-h-[44px]"
            />

            {/* Bottom Controls Strip */}
            <div className="flex items-center justify-between pt-1">
              <div className="flex items-center gap-2">
                {/* File Attachment Action */}
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  onChange={handleFileSelect}
                  className="hidden"
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isUploading}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#121812] border border-[#202A22] hover:border-[#B8F23D]/40 text-[#9BA79D] hover:text-[#F1F5ED] transition cursor-pointer text-xs font-mono"
                  title="Attach workspace files"
                >
                  <Paperclip className={`w-3.5 h-3.5 ${isUploading ? "animate-spin text-[#B8F23D]" : ""}`} />
                  <span className="hidden sm:inline text-[11px]">Attach</span>
                </button>

                {/* Model Selector Dropdown Pill */}
                <div className="relative">
                  <button
                    onClick={() => setModelDropdownOpen(!modelDropdownOpen)}
                    className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#121812] border border-[#202A22] hover:border-[#B8F23D]/40 text-xs font-mono text-[#D5FF78] transition cursor-pointer"
                  >
                    <Cpu className="w-3 h-3 text-[#B8F23D]" />
                    <span className="text-[11px] truncate max-w-[120px]">
                      {selectedModel === "auto" ? `Auto (${defaultModel})` : selectedModel}
                    </span>
                    <ChevronDown className="w-3 h-3 text-[#657066]" />
                  </button>

                  {modelDropdownOpen && (
                    <div className="absolute left-0 bottom-full mb-2 w-56 rounded-xl bg-[#0D120F] border border-[#202A22] shadow-2xl p-1.5 z-40 font-mono text-xs space-y-0.5">
                      <div className="px-2 py-1 text-[10px] text-[#657066] uppercase font-bold">
                        SELECT INFERENCE MODEL
                      </div>
                      <button
                        onClick={() => {
                          setSelectedModel("auto");
                          setModelDropdownOpen(false);
                        }}
                        className={`w-full text-left px-2 py-1.5 rounded-lg transition ${
                          selectedModel === "auto"
                            ? "bg-[#171E18] text-[#D5FF78] font-bold"
                            : "text-[#9BA79D] hover:bg-[#121812] hover:text-[#F1F5ED]"
                        }`}
                      >
                        Auto (Default: {defaultModel})
                      </button>
                      {models.map((m) => (
                        <button
                          key={m.id}
                          onClick={() => {
                            setSelectedModel(m.id);
                            setModelDropdownOpen(false);
                          }}
                          className={`w-full text-left px-2 py-1.5 rounded-lg transition flex items-center justify-between ${
                            selectedModel === m.id
                              ? "bg-[#171E18] text-[#D5FF78] font-bold"
                              : "text-[#9BA79D] hover:bg-[#121812] hover:text-[#F1F5ED]"
                          }`}
                        >
                          <span className="truncate">{m.id}</span>
                          <span className="text-[10px] text-[#657066] uppercase">{m.provider}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Submit / Send Button */}
              <div className="flex items-center gap-2">
                <button
                  onClick={handleSubmit}
                  disabled={!prompt.trim() || isExecuting}
                  className={`p-2 rounded-xl flex items-center justify-center transition-all cursor-pointer ${
                    prompt.trim() && !isExecuting
                      ? "bg-[#B8F23D] text-[#070A08] hover:bg-[#D5FF78] shadow-md shadow-[#B8F23D]/20 scale-100"
                      : "bg-[#121812] text-[#657066] border border-[#202A22] cursor-not-allowed opacity-50"
                  }`}
                  title="Send message (Enter)"
                >
                  {isExecuting ? (
                    <span className="w-4 h-4 border-2 border-[#070A08] border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <ArrowUp className="w-4 h-4 stroke-[2.5]" />
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Subtitle Disclaimer */}
          <div className="text-center text-[10px] text-[#657066] font-mono">
            SOAR runs locally · No external network traffic · Sovereign on-premise execution
          </div>
        </div>
      </div>
    </div>
  );
}
