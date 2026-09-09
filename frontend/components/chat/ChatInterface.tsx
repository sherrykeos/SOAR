"use client";

import React, { useState, useRef, useEffect, useMemo } from "react";
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
  PanelLeft,
  PanelRight,
  Plus,
  Trash2,
  Edit2,
  MessageSquare,
} from "lucide-react";
import { useWorkbench } from "@/context/WorkbenchContext";
import { useToast } from "@/components/ui/Toast";
import { createTask, getTaskEvents } from "@/lib/api/tasks";
import { uploadFile } from "@/lib/api/files";
import { formatDuration, formatTimestamp } from "@/lib/utils/formatters";
import { MarkdownMessage } from "./MarkdownMessage";
import { GeneratedFileCard } from "./GeneratedFileCard";
import type { ChatMessage, EventItem } from "@/types";
import { motion, AnimatePresence } from "framer-motion";

export function ChatInterface() {
  const {
    isHydrated,
    activeSessionId,
    setActiveSessionId,
    createNewSession,
    deleteSession,
    renameSession,
    addMessagesToSession,
    updateMessageInSession,
    getActiveSession,
    models,
    defaultModel,
    selectedModel,
    setSelectedModel,
    sidebarCollapsed,
    setSidebarCollapsed,
    inspectorOpen,
    setInspectorOpen,
    setActiveRunId,
  } = useWorkbench();

  const { success, error } = useToast();

  const [prompt, setPrompt] = useState("");
  const [isExecuting, setIsExecuting] = useState(false);
  const [executingMsgId, setExecutingMsgId] = useState<string | null>(null);
  const [attachedFiles, setAttachedFiles] = useState<{ id?: string; name: string; size?: number }[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [modelDropdownOpen, setModelDropdownOpen] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [expandedThoughts, setExpandedThoughts] = useState<Record<string, boolean>>({});
  const [isRenaming, setIsRenaming] = useState(false);
  const [newTitleText, setNewTitleText] = useState("");

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const modelDropdownRef = useRef<HTMLDivElement>(null);

  // Close model dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        modelDropdownRef.current &&
        !modelDropdownRef.current.contains(event.target as Node)
      ) {
        setModelDropdownOpen(false);
      }
    };
    if (modelDropdownOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [modelDropdownOpen]);

  // Active session
  const activeSession = getActiveSession();
  const currentMessages = useMemo(
    () => activeSession?.messages || [],
    [activeSession?.messages]
  );

  const handleCreateNewChat = () => {
    if (activeSession && activeSession.messages.length === 0) {
      textareaRef.current?.focus();
      return;
    }
    const newId = createNewSession();
    setActiveSessionId(newId);
    setPrompt("");
    textareaRef.current?.focus();
  };

  const handleRenameSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (activeSession && newTitleText.trim()) {
      renameSession(activeSession.id, newTitleText.trim());
    }
    setIsRenaming(false);
  };

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [currentMessages.length, isExecuting, executingMsgId]);

  // Adjust textarea height automatically
  const handlePromptChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setPrompt(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  };

  // Poll events for actively executing message
  useEffect(() => {
    if (!isExecuting || !executingMsgId || !activeSessionId) return;

    const targetMsg = currentMessages.find((m) => m.id === executingMsgId);
    const runId = targetMsg?.run_id;
    if (!runId) return;

    let active = true;
    let consecutiveErrors = 0;
    let interval: NodeJS.Timeout | null = null;

    const poll = async () => {
      try {
        const res = await getTaskEvents(runId);
        consecutiveErrors = 0;
        if (active && res && Array.isArray(res.events)) {
          updateMessageInSession(activeSessionId, executingMsgId, {
            events: res.events,
          });

          // Check if finished
          const lastEvent = res.events[res.events.length - 1];
          if (lastEvent?.status === "completed" || lastEvent?.status === "failed") {
            setIsExecuting(false);
            setExecutingMsgId(null);
            if (interval) clearInterval(interval);
          }
        }
      } catch {
        consecutiveErrors += 1;
        // Stop polling after consecutive errors (e.g., 404 Not Found)
        if (consecutiveErrors >= 2 && interval) {
          clearInterval(interval);
        }
      }
    };

    poll();
    interval = setInterval(poll, 1500);

    return () => {
      active = false;
      if (interval) clearInterval(interval);
    };
  }, [isExecuting, executingMsgId, activeSessionId, currentMessages, updateMessageInSession]);

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

  // Submit multi-turn message in active chat session
  const handleSubmit = async () => {
    const query = prompt.trim();
    if (!query || isExecuting) return;

    const requestedModel = selectedModel === "auto" ? null : selectedModel;
    const attachedFileNames = attachedFiles.map((f) => f.name);

    // 1. Prepare User Message
    const userMsgId = `msg_user_${Date.now()}`;
    const userMessage: ChatMessage = {
      id: userMsgId,
      role: "user",
      content: query,
      created_at: new Date().toISOString(),
      attached_files: attachedFileNames,
    };

    // 2. Prepare placeholder Assistant Message (run_id populated once backend returns)
    const asstMsgId = `msg_asst_${Date.now()}`;
    const asstMessage: ChatMessage = {
      id: asstMsgId,
      run_id: undefined,
      role: "assistant",
      content: "",
      created_at: new Date().toISOString(),
      status: "running",
      model: selectedModel === "auto" ? "auto" : selectedModel,
      events: [],
    };

    // 3. Atomically attach to session or create new session
    let sessionId = activeSessionId;
    const currSession = getActiveSession();

    if (!sessionId || !currSession || currSession.messages.length === 0) {
      if (currSession && currSession.messages.length === 0) {
        sessionId = currSession.id;
        renameSession(sessionId, query.slice(0, 36) + (query.length > 36 ? "..." : ""));
        addMessagesToSession(sessionId, [userMessage, asstMessage]);
      } else {
        sessionId = createNewSession(
          query.slice(0, 36) + (query.length > 36 ? "..." : ""),
          selectedModel === "auto" ? defaultModel : selectedModel,
          [userMessage, asstMessage]
        );
      }
    } else {
      addMessagesToSession(sessionId, [userMessage, asstMessage]);
    }

    setPrompt("");
    setAttachedFiles([]);
    setIsExecuting(true);
    setExecutingMsgId(asstMsgId);
    setInspectorOpen(true);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    // 4. Format Multi-Turn Prompt Context
    let finalPrompt = "";
    const history = currentMessages.slice(-6); // last few turns for context
    if (history.length > 0) {
      finalPrompt += "=== CONVERSATION CONTEXT ===\n";
      history.forEach((m) => {
        finalPrompt += `${m.role === "user" ? "User" : "Assistant"}: ${m.content}\n`;
      });
      finalPrompt += `=== END CONTEXT ===\n\nUser: ${query}`;
    } else {
      finalPrompt = query;
    }

    if (attachedFileNames.length > 0) {
      finalPrompt += `\n\n[Referenced Workspace Files: ${attachedFileNames.join(", ")}]`;
    }

    try {
      const res = await createTask({
        task: finalPrompt,
        model: requestedModel,
        // Pass file_ids of successfully uploaded files so backend resolves real paths
        attached_file_ids: attachedFiles
          .filter((f) => !!f.id)
          .map((f) => f.id as string),
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

      setActiveRunId(res.run_id);

      updateMessageInSession(sessionId, asstMsgId, {
        run_id: res.run_id,
        content: res.answer || "",
        status: res.status === "failed" ? "failed" : "completed",
        // Use actual model from backend response; fall back to model field
        model:
          (res.model_details &&
            typeof res.model_details.actual === "string" &&
            res.model_details.actual) ||
          res.model ||
          (requestedModel ?? defaultModel),
        model_details: res.model_details ?? null,
        execution_mode: res.execution_mode || "direct_answer",
        events: initialEvents,
        generated_files: res.generated_files ?? [],
        duration_seconds:
          typeof res.model_details === "object" &&
          res.model_details !== null &&
          "duration_seconds" in res.model_details &&
          typeof res.model_details.duration_seconds === "number"
            ? res.model_details.duration_seconds
            : undefined,
      });
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Backend unavailable";
      updateMessageInSession(sessionId, asstMsgId, {
        content: `Error executing request: ${errorMsg}`,
        status: "failed",
      });
      error("Execution Failed", errorMsg);
    } finally {
      setIsExecuting(false);
      setExecutingMsgId(null);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const copyMessage = (msgId: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(msgId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleRetryPrompt = (prevPrompt: string) => {
    setPrompt(prevPrompt);
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  const toggleThought = (msgId: string) => {
    setExpandedThoughts((prev) => ({
      ...prev,
      [msgId]: prev[msgId] === undefined ? false : !prev[msgId],
    }));
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
    <div className="flex-1 flex flex-col min-w-0 min-h-0 h-full bg-[#070A08] relative font-sans overflow-hidden">
      {/* Top Session Header Bar (ChatGPT / Claude style) */}
      <div className="h-12 border-b border-[#202A22] bg-[#070A08]/90 backdrop-blur px-4 flex items-center justify-between shrink-0 z-10 select-none">
        <div className="flex items-center gap-2 min-w-0">
          {sidebarCollapsed && (
            <button
              onClick={() => setSidebarCollapsed(false)}
              className="p-1.5 rounded-lg text-[#9BA79D] hover:text-[#D5FF78] hover:bg-[#121812] transition-colors cursor-pointer mr-1"
              title="Expand sidebar"
            >
              <PanelLeft className="w-4 h-4 text-[#B8F23D]" />
            </button>
          )}

          {/* Session Title (with inline click-to-rename) */}
          <div className="flex items-center gap-1.5 min-w-0">
            {isRenaming ? (
              <form onSubmit={handleRenameSubmit} className="flex items-center gap-1">
                <input
                  type="text"
                  value={newTitleText}
                  onChange={(e) => setNewTitleText(e.target.value)}
                  autoFocus
                  onBlur={() => handleRenameSubmit()}
                  className="bg-[#121812] border border-[#B8F23D]/50 text-xs text-[#F1F5ED] px-2 py-1 rounded outline-none font-medium max-w-[200px] sm:max-w-[300px]"
                />
              </form>
            ) : (
              <div
                onClick={() => {
                  if (activeSession) {
                    setNewTitleText(activeSession.title);
                    setIsRenaming(true);
                  }
                }}
                className="group flex items-center gap-1.5 cursor-pointer px-1.5 py-1 rounded hover:bg-[#121812] transition"
                title="Click to rename chat"
              >
                <MessageSquare className="w-3.5 h-3.5 text-[#B8F23D] shrink-0" />
                <span
                  suppressHydrationWarning
                  className="text-xs font-semibold text-[#F1F5ED] truncate max-w-[180px] sm:max-w-[300px]"
                >
                  {isHydrated && activeSession ? activeSession.title : "New Chat"}
                </span>
                <Edit2 className="w-3 h-3 text-[#657066] opacity-0 group-hover:opacity-100 transition" />
              </div>
            )}

            {isHydrated && activeSession?.model && (
              <span className="hidden sm:inline-block font-mono text-[10px] px-1.5 py-0.5 rounded bg-[#121812] text-[#9BA79D] border border-[#202A22]">
                {activeSession.model}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          {/* New Chat Button */}
          <button
            onClick={() => handleCreateNewChat()}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#121812] border border-[#B8F23D]/30 text-[#D5FF78] hover:border-[#B8F23D] hover:bg-[#171E18] text-xs font-semibold transition cursor-pointer"
            title="Create new chat (⌘N)"
          >
            <Plus className="w-3.5 h-3.5 text-[#B8F23D]" />
            <span className="hidden sm:inline">New Chat</span>
          </button>

          {/* Delete active chat if it has messages */}
          {isHydrated && activeSession && activeSession.messages.length > 0 && (
            <button
              onClick={() => deleteSession(activeSession.id)}
              className="p-1.5 rounded-lg text-[#657066] hover:text-[#EF4444] hover:bg-[#121812] transition cursor-pointer"
              title="Delete chat"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}

          {/* Toggle Run Inspector */}
          <button
            onClick={() => setInspectorOpen((prev) => !prev)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-mono transition cursor-pointer ${
              inspectorOpen
                ? "bg-[#171E18] border-[#B8F23D]/40 text-[#D5FF78]"
                : "bg-[#121812] border-[#202A22] text-[#9BA79D] hover:text-[#F1F5ED] hover:border-[#B8F23D]/20"
            }`}
            title={inspectorOpen ? "Hide Run Inspector & DAG" : "Show Run Inspector & DAG"}
          >
            <PanelRight className="w-3.5 h-3.5" />
            <span className="hidden md:inline text-[11px]">Inspector</span>
          </button>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 min-h-0 overflow-y-auto px-4 py-6 md:px-8 space-y-6">
        <div className="max-w-3xl mx-auto w-full space-y-6">
          {/* Welcome Screen when active session has no messages */}
          {!isHydrated || currentMessages.length === 0 ? (
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
                  On-premise execution with zero external network traffic. Start a multi-turn conversation or choose a workflow below.
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
            /* Multi-turn Conversation Stream */
            <div className="space-y-6">
              {currentMessages.map((msg) => {
                const isUser = msg.role === "user";
                const isMsgRunning = isExecuting && executingMsgId === msg.id;
                const isThoughtOpen =
                  expandedThoughts[msg.id] !== undefined
                    ? expandedThoughts[msg.id]
                    : true;

                if (isUser) {
                  return (
                    <div key={msg.id} className="flex items-start gap-3 justify-end">
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
                        {msg.attached_files && msg.attached_files.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 justify-end pt-1">
                            {msg.attached_files.map((file) => (
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
                          {msg.content}
                        </p>
                      </div>
                    </div>
                  );
                }

                // Assistant Response Turn
                return (
                  <div key={msg.id} className="flex items-start gap-3 justify-start">
                    <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-xl bg-[#0D120F] border border-[#202A22] flex items-center justify-center shrink-0 mt-1 shadow-md">
                      <Bot className="w-4 h-4 text-[#22C55E]" />
                    </div>

                    <div className="flex-1 min-w-0 space-y-2">
                      {/* Generated Answer Content */}
                      <div className="p-4 md:p-5 rounded-2xl bg-[#0D120F] border border-[#202A22] shadow-xl">
                        {msg.content ? (
                          <MarkdownMessage content={msg.content} />
                        ) : isMsgRunning ? (
                          <div className="flex items-center gap-2.5 py-3 text-xs font-mono text-[#9BA79D]">
                            <span className="w-2 h-2 rounded-full bg-[#22C55E] animate-pulse" />
                            <span>Synthesizing response inside sovereign environment...</span>
                          </div>
                        ) : (
                          <div className="text-xs text-[#657066] font-mono">
                            Task completed. Review checkpoints in the Right Inspector sidebar.
                          </div>
                        )}

                        {/* Generated file cards */}
                        {msg.generated_files && msg.generated_files.length > 0 && (
                          <div className="space-y-1 mt-2">
                            {msg.generated_files.map((gf) => (
                              <GeneratedFileCard key={gf.file_id} file={gf} />
                            ))}
                          </div>
                        )}

                        {/* Action Bar Beneath Response */}
                        {msg.content && (
                          <div className="flex flex-wrap items-center justify-between gap-3 pt-4 mt-4 border-t border-[#202A22] text-xs font-mono">
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => copyMessage(msg.id, msg.content)}
                                className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#121812] border border-[#202A22] hover:border-[#B8F23D]/40 text-[#9BA79D] hover:text-[#F1F5ED] transition cursor-pointer text-[11px]"
                                title="Copy answer"
                              >
                                {copiedId === msg.id ? (
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
                                onClick={() => {
                                  // Find prior user prompt
                                  const userMsg = currentMessages
                                    .slice(0, currentMessages.indexOf(msg))
                                    .reverse()
                                    .find((m) => m.role === "user");
                                  if (userMsg) handleRetryPrompt(userMsg.content);
                                }}
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

                            {/* Actual model used + duration */}
                            <div className="flex items-center gap-2 text-[10px] text-[#657066]">
                              <span className="text-[#D5FF78]">
                                {(msg.model_details &&
                                  typeof msg.model_details.actual === "string" &&
                                  msg.model_details.actual) ||
                                  msg.model ||
                                  defaultModel}
                              </span>
                              {msg.duration_seconds && (
                                <>
                                  <span>·</span>
                                  <span>{formatDuration(msg.duration_seconds)}</span>
                                </>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Pinned Bottom Input Container (ChatGPT / Claude style) */}
      <div className="p-4 md:p-6 bg-gradient-to-t from-[#070A08] via-[#070A08]/90 to-transparent shrink-0">
        <div className="max-w-3xl mx-auto w-full space-y-2">
          {/* Main Floating Input Card */}
          <div className="rounded-2xl bg-[#0D120F] border border-[#202A22] focus-within:border-[#B8F23D]/50 focus-within:ring-1 focus-within:ring-[#B8F23D]/20 shadow-2xl transition-all p-3 space-y-2 relative">
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
              placeholder="Message SOAR... (Enter to send, Shift+Enter for newline)"
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
                <div className="relative" ref={modelDropdownRef}>
                  <button
                    onClick={() => setModelDropdownOpen(!modelDropdownOpen)}
                    className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#121812] border border-[#202A22] hover:border-[#B8F23D]/40 text-xs font-mono text-[#D5FF78] transition cursor-pointer"
                    title="Select model for this session"
                  >
                    <Cpu className="w-3 h-3 text-[#B8F23D]" />
                    <span
                      suppressHydrationWarning
                      className="text-[11px] truncate max-w-[140px]"
                    >
                      {selectedModel === "auto"
                        ? `Auto (${defaultModel})`
                        : selectedModel}
                    </span>
                    <ChevronDown
                      className={`w-3 h-3 text-[#657066] transition-transform ${
                        modelDropdownOpen ? "rotate-180" : ""
                      }`}
                    />
                  </button>

                  {modelDropdownOpen && (
                    <div className="absolute left-0 bottom-full mb-3 w-80 rounded-xl bg-[#0D120F] border border-[#202A22] shadow-2xl p-2 z-50 font-mono text-xs space-y-1 backdrop-blur-xl">
                      <div className="px-2 py-1 text-[10px] text-[#657066] uppercase font-bold tracking-wider flex items-center justify-between border-b border-[#202A22]/50 pb-1.5 mb-1">
                        <span>SELECT INFERENCE MODEL</span>
                        <span className="text-[9px] text-[#B8F23D]">
                          {models.length + 1} AVAILABLE
                        </span>
                      </div>

                      <div className="max-h-64 overflow-y-auto space-y-1 pr-1">
                        {/* Auto (Default) */}
                        <button
                          onClick={() => {
                            setSelectedModel("auto");
                            setModelDropdownOpen(false);
                          }}
                          className={`w-full text-left p-2 rounded-lg transition flex items-center justify-between ${
                            selectedModel === "auto"
                              ? "bg-[#171E18] text-[#D5FF78] border border-[#B8F23D]/30 font-bold"
                              : "text-[#9BA79D] hover:bg-[#121812] hover:text-[#F1F5ED] border border-transparent"
                          }`}
                        >
                          <div className="flex flex-col min-w-0">
                            <div className="flex items-center gap-1.5">
                              <span className="truncate">Auto Router</span>
                              <span className="text-[9px] px-1.5 py-0.2 rounded bg-[#B8F23D]/10 text-[#B8F23D] border border-[#B8F23D]/20">
                                Recommended
                              </span>
                            </div>
                            <span className="text-[10px] text-[#657066] font-normal mt-0.5">
                              Dynamically routes to default ({defaultModel})
                            </span>
                          </div>
                          {selectedModel === "auto" && (
                            <Check className="w-3.5 h-3.5 text-[#B8F23D] shrink-0" />
                          )}
                        </button>

                        {/* Configured Models from GET /api/models */}
                        {models.map((m) => {
                          const isSelected = selectedModel === m.id;
                          const caps = Array.isArray(m.capabilities)
                            ? m.capabilities.join(", ")
                            : typeof m.capabilities === "string"
                            ? m.capabilities
                            : "";

                          return (
                            <button
                              key={m.id}
                              disabled={!m.available}
                              onClick={() => {
                                if (!m.available) return;
                                setSelectedModel(m.id);
                                setModelDropdownOpen(false);
                              }}
                              className={`w-full text-left p-2 rounded-lg transition flex items-center justify-between ${
                                !m.available
                                  ? "opacity-50 cursor-not-allowed text-[#657066]"
                                  : isSelected
                                  ? "bg-[#171E18] text-[#D5FF78] border border-[#B8F23D]/30 font-bold"
                                  : "text-[#9BA79D] hover:bg-[#121812] hover:text-[#F1F5ED] border border-transparent"
                              }`}
                            >
                              <div className="flex flex-col min-w-0 pr-2">
                                <div className="flex items-center gap-1.5">
                                  <span
                                    className={`w-1.5 h-1.5 rounded-full ${
                                      m.available ? "bg-[#22C55E]" : "bg-[#EF4444]"
                                    }`}
                                  />
                                  <span className="truncate font-semibold">{m.id}</span>
                                  {!m.available && (
                                    <span className="text-[9px] px-1 py-0.2 rounded bg-red-950/50 text-red-400 border border-red-800/40 uppercase font-mono">
                                      Offline
                                    </span>
                                  )}
                                </div>
                                <div className="flex items-center gap-2 mt-0.5 text-[10px] text-[#657066] font-normal">
                                  <span className="uppercase">{m.provider}</span>
                                  {caps && <span>· {caps}</span>}
                                </div>
                              </div>
                              {isSelected && (
                                <Check className="w-3.5 h-3.5 text-[#B8F23D] shrink-0" />
                              )}
                            </button>
                          );
                        })}
                      </div>
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
