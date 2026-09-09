"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useMemo,
  useSyncExternalStore,
} from "react";
import type {
  ModelItem,
  HealthResponse,
  ClientTaskRecord,
  ChatSession,
  ChatMessage,
} from "@/types";
import { getHealth } from "@/lib/api/health";
import { listModels } from "@/lib/api/models";

interface WorkbenchContextType {
  // Health
  health: HealthResponse | null;
  isBackendOnline: boolean;
  checkHealth: () => Promise<void>;

  // Models
  models: ModelItem[];
  defaultModel: string;
  selectedModel: string;
  setSelectedModel: (model: string) => void;
  isLoadingModels: boolean;
  refreshModels: () => Promise<void>;

  // Chat Sessions (Multi-chat system)
  sessions: ChatSession[];
  activeSessionId: string | null;
  setActiveSessionId: (id: string | null) => void;
  createNewSession: (title?: string, model?: string) => string;
  deleteSession: (sessionId: string) => void;
  renameSession: (sessionId: string, newTitle: string) => void;
  addMessageToSession: (sessionId: string, message: ChatMessage) => void;
  updateMessageInSession: (
    sessionId: string,
    messageId: string,
    updates: Partial<ChatMessage>
  ) => void;
  getActiveSession: () => ChatSession | undefined;

  // Session Tasks (Legacy & cross-compatibility)
  sessionTasks: ClientTaskRecord[];
  activeRunId: string | null;
  setActiveRunId: (runId: string | null) => void;
  addSessionTask: (task: ClientTaskRecord) => void;
  updateSessionTask: (runId: string, updates: Partial<ClientTaskRecord>) => void;
  getTaskByRunId: (runId: string) => ClientTaskRecord | undefined;

  // Command Palette
  commandPaletteOpen: boolean;
  setCommandPaletteOpen: (open: boolean) => void;

  // Mobile navigation
  mobileSidebarOpen: boolean;
  setMobileSidebarOpen: (open: boolean) => void;

  // Collapsible panels
  sidebarCollapsed: boolean;
  setSidebarCollapsed: React.Dispatch<React.SetStateAction<boolean>>;
  inspectorOpen: boolean;
  setInspectorOpen: React.Dispatch<React.SetStateAction<boolean>>;
}

const WorkbenchContext = createContext<WorkbenchContextType | undefined>(undefined);

const LOCAL_STORAGE_SESSIONS_KEY = "soar_chat_sessions_v2";
const LOCAL_STORAGE_TASKS_KEY = "soar_session_tasks_v1";

function subscribeStore(callback: () => void) {
  if (typeof window === "undefined") return () => {};
  window.addEventListener("storage", callback);
  window.addEventListener("soar-store-change", callback);
  return () => {
    window.removeEventListener("storage", callback);
    window.removeEventListener("soar-store-change", callback);
  };
}

function getSessionsSnapshot(): string {
  if (typeof window === "undefined") return "[]";
  try {
    return localStorage.getItem(LOCAL_STORAGE_SESSIONS_KEY) || "[]";
  } catch {
    return "[]";
  }
}

function getTasksSnapshot(): string {
  if (typeof window === "undefined") return "[]";
  try {
    return localStorage.getItem(LOCAL_STORAGE_TASKS_KEY) || "[]";
  } catch {
    return "[]";
  }
}

function getServerSnapshot(): string {
  return "[]";
}

export function WorkbenchProvider({ children }: { children: React.ReactNode }) {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isBackendOnline, setIsBackendOnline] = useState<boolean>(true);

  const [models, setModels] = useState<ModelItem[]>([]);
  const [defaultModel, setDefaultModel] = useState<string>("auto");
  const [selectedModel, setSelectedModel] = useState<string>("auto");
  const [isLoadingModels, setIsLoadingModels] = useState<boolean>(true);

  // Chat Sessions store
  const rawSessionsJson = useSyncExternalStore(
    subscribeStore,
    getSessionsSnapshot,
    getServerSnapshot
  );

  const sessions = useMemo<ChatSession[]>(() => {
    try {
      const parsed = JSON.parse(rawSessionsJson);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }, [rawSessionsJson]);

  // Tasks store (for legacy task views)
  const rawTasksJson = useSyncExternalStore(
    subscribeStore,
    getTasksSnapshot,
    getServerSnapshot
  );

  const directTasks = useMemo<ClientTaskRecord[]>(() => {
    try {
      const parsed = JSON.parse(rawTasksJson);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }, [rawTasksJson]);

  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState<boolean>(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState<boolean>(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const [inspectorOpen, setInspectorOpen] = useState<boolean>(true);

  // Persist sessions
  const persistSessions = useCallback((updated: ChatSession[]) => {
    try {
      localStorage.setItem(LOCAL_STORAGE_SESSIONS_KEY, JSON.stringify(updated.slice(0, 100)));
      window.dispatchEvent(new Event("soar-store-change"));
    } catch {
      // ignore
    }
  }, []);

  // Persist tasks
  const persistTasks = useCallback((tasks: ClientTaskRecord[]) => {
    try {
      localStorage.setItem(LOCAL_STORAGE_TASKS_KEY, JSON.stringify(tasks.slice(0, 50)));
      window.dispatchEvent(new Event("soar-store-change"));
    } catch {
      // ignore
    }
  }, []);

  // Check backend health
  const checkHealth = useCallback(async () => {
    try {
      const res = await getHealth();
      setHealth(res);
      setIsBackendOnline(true);
    } catch {
      setIsBackendOnline(false);
    }
  }, []);

  // Fetch models from GET /api/models
  const refreshModels = useCallback(async () => {
    setIsLoadingModels(true);
    try {
      const res = await listModels();
      setModels(res.models || []);
      if (res.default_model) {
        setDefaultModel(res.default_model);
      }
    } catch {
      // handled gracefully
    } finally {
      setIsLoadingModels(false);
    }
  }, []);

  // Initial data loading
  useEffect(() => {
    let isSubscribed = true;

    const initialize = async () => {
      await checkHealth();
      try {
        const res = await listModels();
        if (isSubscribed) {
          setModels(res.models || []);
          if (res.default_model) {
            setDefaultModel(res.default_model);
          }
          setIsLoadingModels(false);
        }
      } catch {
        if (isSubscribed) setIsLoadingModels(false);
      }
    };

    initialize();

    const interval = setInterval(() => {
      checkHealth();
    }, 15000);

    return () => {
      isSubscribed = false;
      clearInterval(interval);
    };
  }, [checkHealth]);

  // Global Command Palette Shortcut (Cmd+K / Ctrl+K)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCommandPaletteOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // --- Session Management Functions ---

  const createNewSession = useCallback(
    (title?: string, modelChoice?: string): string => {
      const newId = `session_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
      const newSession: ChatSession = {
        id: newId,
        title: title || "New Chat",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        model: modelChoice || selectedModel || defaultModel,
        messages: [],
      };

      const updated = [newSession, ...sessions];
      persistSessions(updated);
      setActiveSessionId(newId);
      setActiveRunId(null);
      return newId;
    },
    [sessions, selectedModel, defaultModel, persistSessions]
  );

  const deleteSession = useCallback(
    (sessionId: string) => {
      const updated = sessions.filter((s) => s.id !== sessionId);
      persistSessions(updated);

      if (activeSessionId === sessionId) {
        if (updated.length > 0) {
          setActiveSessionId(updated[0].id);
        } else {
          setActiveSessionId(null);
        }
      }
    },
    [sessions, activeSessionId, persistSessions]
  );

  const renameSession = useCallback(
    (sessionId: string, newTitle: string) => {
      const updated = sessions.map((s) =>
        s.id === sessionId
          ? { ...s, title: newTitle.trim() || s.title, updated_at: new Date().toISOString() }
          : s
      );
      persistSessions(updated);
    },
    [sessions, persistSessions]
  );

  const addMessageToSession = useCallback(
    (sessionId: string, message: ChatMessage) => {
      const targetSession = sessions.find((s) => s.id === sessionId);
      if (!targetSession) {
        // Create session if it doesn't exist yet
        const newSession: ChatSession = {
          id: sessionId,
          title: message.role === "user" ? message.content.slice(0, 36) : "New Chat",
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          model: message.model || selectedModel || defaultModel,
          messages: [message],
        };
        persistSessions([newSession, ...sessions]);
        setActiveSessionId(sessionId);
        if (message.run_id) setActiveRunId(message.run_id);
        return;
      }

      let sessionTitle = targetSession.title;
      if (
        (sessionTitle === "New Chat" || sessionTitle === "Untitled Session") &&
        message.role === "user"
      ) {
        sessionTitle = message.content.slice(0, 36) + (message.content.length > 36 ? "..." : "");
      }

      const updated = sessions.map((s) => {
        if (s.id === sessionId) {
          return {
            ...s,
            title: sessionTitle,
            updated_at: new Date().toISOString(),
            messages: [...s.messages, message],
          };
        }
        return s;
      });

      persistSessions(updated);
      if (message.run_id) setActiveRunId(message.run_id);
    },
    [sessions, selectedModel, defaultModel, persistSessions]
  );

  const updateMessageInSession = useCallback(
    (sessionId: string, messageId: string, updates: Partial<ChatMessage>) => {
      const updated = sessions.map((s) => {
        if (s.id === sessionId) {
          return {
            ...s,
            updated_at: new Date().toISOString(),
            messages: s.messages.map((m) =>
              m.id === messageId ? { ...m, ...updates } : m
            ),
          };
        }
        return s;
      });

      persistSessions(updated);
    },
    [sessions, persistSessions]
  );

  const getActiveSession = useCallback((): ChatSession | undefined => {
    if (activeSessionId) {
      return sessions.find((s) => s.id === activeSessionId);
    }
    return sessions[0];
  }, [sessions, activeSessionId]);

  // Derived unified task list
  const sessionTasks = useMemo<ClientTaskRecord[]>(() => {
    const fromMessages: ClientTaskRecord[] = [];
    sessions.forEach((s) => {
      s.messages.forEach((m) => {
        if (m.run_id) {
          fromMessages.push({
            run_id: m.run_id,
            task: m.content || s.title,
            model: m.model || s.model || defaultModel,
            status: m.status || "completed",
            created_at: m.created_at || s.created_at,
            duration_seconds: m.duration_seconds,
            answer: m.role === "assistant" ? m.content : undefined,
            events: m.events || [],
            attached_files: m.attached_files,
            execution_mode: m.execution_mode || "sandbox",
          });
        }
      });
    });

    const combined = [...directTasks];
    fromMessages.forEach((fm) => {
      if (!combined.some((t) => t.run_id === fm.run_id)) {
        combined.push(fm);
      }
    });

    return combined;
  }, [sessions, directTasks, defaultModel]);

  const addSessionTask = useCallback(
    (task: ClientTaskRecord) => {
      const updated = [task, ...directTasks.filter((t) => t.run_id !== task.run_id)];
      persistTasks(updated);
      setActiveRunId(task.run_id);
    },
    [directTasks, persistTasks]
  );

  const updateSessionTask = useCallback(
    (runId: string, updates: Partial<ClientTaskRecord>) => {
      const updated = directTasks.map((t) =>
        t.run_id === runId ? { ...t, ...updates } : t
      );
      persistTasks(updated);

      // Also update matching message in sessions if present
      sessions.forEach((s) => {
        const msg = s.messages.find((m) => m.run_id === runId);
        if (msg) {
          updateMessageInSession(s.id, msg.id, updates);
        }
      });
    },
    [directTasks, persistTasks, sessions, updateMessageInSession]
  );

  const getTaskByRunId = useCallback(
    (runId: string) => {
      const fromDirect = directTasks.find((t) => t.run_id === runId);
      if (fromDirect) return fromDirect;

      for (const s of sessions) {
        for (const m of s.messages) {
          if (m.run_id === runId) {
            return {
              run_id: m.run_id,
              task: m.content,
              model: m.model || s.model,
              status: m.status || "completed",
              created_at: m.created_at,
              duration_seconds: m.duration_seconds,
              answer: m.content,
              events: m.events || [],
              attached_files: m.attached_files,
              execution_mode: m.execution_mode,
            };
          }
        }
      }
      return undefined;
    },
    [directTasks, sessions]
  );

  return (
    <WorkbenchContext.Provider
      value={{
        health,
        isBackendOnline,
        checkHealth,
        models,
        defaultModel,
        selectedModel,
        setSelectedModel,
        isLoadingModels,
        refreshModels,
        sessions,
        activeSessionId,
        setActiveSessionId,
        createNewSession,
        deleteSession,
        renameSession,
        addMessageToSession,
        updateMessageInSession,
        getActiveSession,
        sessionTasks,
        activeRunId,
        setActiveRunId,
        addSessionTask,
        updateSessionTask,
        getTaskByRunId,
        commandPaletteOpen,
        setCommandPaletteOpen,
        mobileSidebarOpen,
        setMobileSidebarOpen,
        sidebarCollapsed,
        setSidebarCollapsed,
        inspectorOpen,
        setInspectorOpen,
      }}
    >
      {children}
    </WorkbenchContext.Provider>
  );
}

export function useWorkbench() {
  const context = useContext(WorkbenchContext);
  if (!context) {
    throw new Error("useWorkbench must be used within a WorkbenchProvider");
  }
  return context;
}
