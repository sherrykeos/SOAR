"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useMemo,
  useRef,
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
  isHydrated: boolean;

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
  createNewSession: (title?: string, model?: string, initialMessages?: ChatMessage[]) => string;
  deleteSession: (sessionId: string) => void;
  renameSession: (sessionId: string, newTitle: string) => void;
  addMessageToSession: (sessionId: string, message: ChatMessage) => void;
  addMessagesToSession: (sessionId: string, messages: ChatMessage[]) => void;
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
const LOCAL_STORAGE_ACTIVE_SESSION_KEY = "soar_active_session_id_v1";

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

const emptySubscribe = () => () => {};

const DEFAULT_CONFIGURED_MODELS: ModelItem[] = [
  {
    id: "qwen3:1.7b",
    provider: "ollama",
    capabilities: ["general", "reasoning"],
    enabled: true,
    available: true,
    priority: 10,
    timeout: 180,
  },
  {
    id: "qwen3:4b",
    provider: "ollama",
    capabilities: ["reasoning"],
    enabled: true,
    available: true,
    priority: 20,
    timeout: 15,
  },
  {
    id: "qwen2.5-coder:1.5b",
    provider: "ollama",
    capabilities: ["coding"],
    enabled: true,
    available: true,
    priority: 15,
    timeout: 180,
  },
  {
    id: "qwen2.5vl:3b",
    provider: "ollama",
    capabilities: ["vision"],
    enabled: true,
    available: true,
    priority: 15,
    timeout: 180,
  },
];

export function WorkbenchProvider({ children }: { children: React.ReactNode }) {
  const isHydrated = useSyncExternalStore(
    emptySubscribe,
    () => true,
    () => false
  );
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isBackendOnline, setIsBackendOnline] = useState<boolean>(true);

  const [models, setModels] = useState<ModelItem[]>(DEFAULT_CONFIGURED_MODELS);
  const [defaultModel, setDefaultModel] = useState<string>("qwen3:1.7b");
  const [selectedModel, setSelectedModel] = useState<string>("auto");
  const [isLoadingModels, setIsLoadingModels] = useState<boolean>(false);

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

  const [selectedSessionId, setSelectedSessionIdState] = useState<string | null>(() => {
    if (typeof window === "undefined") return null;
    try {
      return localStorage.getItem(LOCAL_STORAGE_ACTIVE_SESSION_KEY) || null;
    } catch {
      return null;
    }
  });

  const setActiveSessionId = useCallback((id: string | null) => {
    setSelectedSessionIdState(id);
    try {
      if (typeof window !== "undefined") {
        if (id) {
          localStorage.setItem(LOCAL_STORAGE_ACTIVE_SESSION_KEY, id);
        } else {
          localStorage.removeItem(LOCAL_STORAGE_ACTIVE_SESSION_KEY);
        }
      }
    } catch {
      // ignore
    }
  }, []);

  // Compute effective activeSessionId without setting state inside an effect
  const activeSessionId = useMemo(() => {
    if (selectedSessionId && sessions.some((s) => s.id === selectedSessionId)) {
      return selectedSessionId;
    }
    return sessions[0]?.id || null;
  }, [selectedSessionId, sessions]);

  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState<boolean>(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState<boolean>(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const [inspectorOpen, setInspectorOpen] = useState<boolean>(true);

  // In-memory ref to prevent stale closures when mutating sessions in quick succession
  const sessionsRef = useRef<ChatSession[]>([]);

  useEffect(() => {
    sessionsRef.current = sessions;
  }, [sessions]);

  // Persist sessions
  const persistSessions = useCallback((updated: ChatSession[]) => {
    try {
      sessionsRef.current = updated;
      if (typeof window !== "undefined") {
        localStorage.setItem(LOCAL_STORAGE_SESSIONS_KEY, JSON.stringify(updated.slice(0, 100)));
        window.dispatchEvent(new Event("soar-store-change"));
      }
    } catch {
      // ignore
    }
  }, []);

  // Synchronous accessor for latest session list
  const getLatestSessions = useCallback((): ChatSession[] => {
    if (sessionsRef.current && sessionsRef.current.length > 0) {
      return sessionsRef.current;
    }
    if (typeof window !== "undefined") {
      try {
        const raw = localStorage.getItem(LOCAL_STORAGE_SESSIONS_KEY);
        if (raw) {
          const parsed = JSON.parse(raw);
          if (Array.isArray(parsed)) {
            sessionsRef.current = parsed;
            return parsed;
          }
        }
      } catch {
        // ignore
      }
    }
    return sessions;
  }, [sessions]);

  // Persist tasks
  const persistTasks = useCallback((tasks: ClientTaskRecord[]) => {
    try {
      localStorage.setItem(LOCAL_STORAGE_TASKS_KEY, JSON.stringify(tasks.slice(0, 50)));
      window.dispatchEvent(new Event("soar-store-change"));
    } catch {
      // ignore
    }
  }, []);

  // In-flight guards to avoid duplicated requests in React StrictMode
  const isCheckingHealthRef = useRef<boolean>(false);
  const isLoadingModelsRef = useRef<boolean>(false);
  const hasInitializedRef = useRef<boolean>(false);

  // Check backend health
  const checkHealth = useCallback(async () => {
    if (isCheckingHealthRef.current) return;
    isCheckingHealthRef.current = true;
    try {
      const res = await getHealth();
      setHealth(res);
      setIsBackendOnline(true);
    } catch {
      setIsBackendOnline(false);
    } finally {
      isCheckingHealthRef.current = false;
    }
  }, []);

  // Fetch models from GET /api/models
  const refreshModels = useCallback(async () => {
    if (isLoadingModelsRef.current) return;
    isLoadingModelsRef.current = true;
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
      isLoadingModelsRef.current = false;
    }
  }, []);

  // Initial data loading
  useEffect(() => {
    if (hasInitializedRef.current) return;
    hasInitializedRef.current = true;

    let isSubscribed = true;

    const initialize = async () => {
      await checkHealth();
      if (!isSubscribed) return;
      await refreshModels();
    };

    initialize();

    const interval = setInterval(() => {
      checkHealth();
    }, 15000);

    return () => {
      isSubscribed = false;
      clearInterval(interval);
    };
  }, [checkHealth, refreshModels]);

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
    (title?: string, modelChoice?: string, initialMessages?: ChatMessage[]): string => {
      const current = getLatestSessions();
      const newId = `session_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
      const newSession: ChatSession = {
        id: newId,
        title: title || "New Chat",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        model: modelChoice || selectedModel || defaultModel,
        messages: initialMessages || [],
      };

      // Filter out any empty placeholder sessions to keep session list clean
      const filtered = current.filter((s) => s.messages.length > 0);
      const updated = [newSession, ...filtered];
      persistSessions(updated);
      setActiveSessionId(newId);

      if (initialMessages && initialMessages.length > 0) {
        const lastRunId = [...initialMessages].reverse().find((m) => m.run_id)?.run_id;
        if (lastRunId) setActiveRunId(lastRunId);
      } else {
        setActiveRunId(null);
      }

      return newId;
    },
    [getLatestSessions, selectedModel, defaultModel, persistSessions, setActiveSessionId]
  );

  const deleteSession = useCallback(
    (sessionId: string) => {
      const current = getLatestSessions();
      const updated = current.filter((s) => s.id !== sessionId);
      persistSessions(updated);

      if (activeSessionId === sessionId) {
        if (updated.length > 0) {
          setActiveSessionId(updated[0].id);
        } else {
          setActiveSessionId(null);
        }
      }
    },
    [getLatestSessions, activeSessionId, persistSessions, setActiveSessionId]
  );

  const renameSession = useCallback(
    (sessionId: string, newTitle: string) => {
      const current = getLatestSessions();
      const updated = current.map((s) =>
        s.id === sessionId
          ? { ...s, title: newTitle.trim() || s.title, updated_at: new Date().toISOString() }
          : s
      );
      persistSessions(updated);
    },
    [getLatestSessions, persistSessions]
  );

  const addMessagesToSession = useCallback(
    (sessionId: string, newMessages: ChatMessage[]) => {
      if (!newMessages || newMessages.length === 0) return;
      const current = getLatestSessions();
      const targetSession = current.find((s) => s.id === sessionId);

      if (!targetSession) {
        const firstUser = newMessages.find((m) => m.role === "user");
        const title = firstUser
          ? firstUser.content.slice(0, 36) + (firstUser.content.length > 36 ? "..." : "")
          : "New Chat";
        const newSession: ChatSession = {
          id: sessionId,
          title,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          model: newMessages[0]?.model || selectedModel || defaultModel,
          messages: newMessages,
        };
        persistSessions([newSession, ...current]);
        setActiveSessionId(sessionId);
        const lastRunId = [...newMessages].reverse().find((m) => m.run_id)?.run_id;
        if (lastRunId) setActiveRunId(lastRunId);
        return;
      }

      let sessionTitle = targetSession.title;
      const firstUser = newMessages.find((m) => m.role === "user");
      if (
        (sessionTitle === "New Chat" || sessionTitle === "Untitled Session" || !sessionTitle) &&
        firstUser
      ) {
        sessionTitle = firstUser.content.slice(0, 36) + (firstUser.content.length > 36 ? "..." : "");
      }

      const updated = current.map((s) => {
        if (s.id === sessionId) {
          return {
            ...s,
            title: sessionTitle,
            updated_at: new Date().toISOString(),
            messages: [...s.messages, ...newMessages],
          };
        }
        return s;
      });

      persistSessions(updated);
      const lastRunId = [...newMessages].reverse().find((m) => m.run_id)?.run_id;
      if (lastRunId) setActiveRunId(lastRunId);
    },
    [getLatestSessions, selectedModel, defaultModel, persistSessions, setActiveSessionId]
  );

  const addMessageToSession = useCallback(
    (sessionId: string, message: ChatMessage) => {
      addMessagesToSession(sessionId, [message]);
    },
    [addMessagesToSession]
  );

  const updateMessageInSession = useCallback(
    (sessionId: string, messageId: string, updates: Partial<ChatMessage>) => {
      const current = getLatestSessions();
      const updated = current.map((s) => {
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
    [getLatestSessions, persistSessions]
  );

  const getActiveSession = useCallback((): ChatSession | undefined => {
    const current = getLatestSessions();
    if (activeSessionId) {
      const found = current.find((s) => s.id === activeSessionId);
      if (found) return found;
    }
    return current[0];
  }, [getLatestSessions, activeSessionId]);

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
        isHydrated,
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
        addMessagesToSession,
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
