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
import type { ModelItem, HealthResponse, ClientTaskRecord } from "@/types";
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

  // Session Tasks
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

const LOCAL_STORAGE_TASKS_KEY = "soar_session_tasks_v1";

function subscribeTasks(callback: () => void) {
  if (typeof window === "undefined") return () => {};
  window.addEventListener("storage", callback);
  window.addEventListener("soar-tasks-change", callback);
  return () => {
    window.removeEventListener("storage", callback);
    window.removeEventListener("soar-tasks-change", callback);
  };
}

function getTasksSnapshot(): string {
  if (typeof window === "undefined") return "[]";
  try {
    return localStorage.getItem(LOCAL_STORAGE_TASKS_KEY) || "[]";
  } catch {
    return "[]";
  }
}

function getServerTasksSnapshot(): string {
  return "[]";
}

export function WorkbenchProvider({ children }: { children: React.ReactNode }) {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isBackendOnline, setIsBackendOnline] = useState<boolean>(true);

  const [models, setModels] = useState<ModelItem[]>([]);
  const [defaultModel, setDefaultModel] = useState<string>("auto");
  const [selectedModel, setSelectedModel] = useState<string>("auto");
  const [isLoadingModels, setIsLoadingModels] = useState<boolean>(true);

  const rawTasksJson = useSyncExternalStore(
    subscribeTasks,
    getTasksSnapshot,
    getServerTasksSnapshot
  );

  const sessionTasks = useMemo<ClientTaskRecord[]>(() => {
    try {
      const parsed = JSON.parse(rawTasksJson);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }, [rawTasksJson]);

  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState<boolean>(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState<boolean>(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const [inspectorOpen, setInspectorOpen] = useState<boolean>(true);

  // Save session tasks to localStorage & notify store subscribers
  const persistTasks = useCallback((tasks: ClientTaskRecord[]) => {
    try {
      localStorage.setItem(LOCAL_STORAGE_TASKS_KEY, JSON.stringify(tasks.slice(0, 50)));
      window.dispatchEvent(new Event("soar-tasks-change"));
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

  const addSessionTask = useCallback(
    (task: ClientTaskRecord) => {
      const updated = [task, ...sessionTasks.filter((t) => t.run_id !== task.run_id)];
      persistTasks(updated);
      setActiveRunId(task.run_id);
    },
    [sessionTasks, persistTasks]
  );

  const updateSessionTask = useCallback(
    (runId: string, updates: Partial<ClientTaskRecord>) => {
      const updated = sessionTasks.map((t) =>
        t.run_id === runId ? { ...t, ...updates } : t
      );
      persistTasks(updated);
    },
    [sessionTasks, persistTasks]
  );

  const getTaskByRunId = useCallback(
    (runId: string) => {
      return sessionTasks.find((t) => t.run_id === runId);
    },
    [sessionTasks]
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
