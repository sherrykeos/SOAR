"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
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
}

const WorkbenchContext = createContext<WorkbenchContextType | undefined>(undefined);

const LOCAL_STORAGE_TASKS_KEY = "soar_session_tasks_v1";

export function WorkbenchProvider({ children }: { children: React.ReactNode }) {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isBackendOnline, setIsBackendOnline] = useState<boolean>(true);

  const [models, setModels] = useState<ModelItem[]>([]);
  const [defaultModel, setDefaultModel] = useState<string>("auto");
  const [selectedModel, setSelectedModel] = useState<string>("auto");
  const [isLoadingModels, setIsLoadingModels] = useState<boolean>(true);

  // Lazy initialize from localStorage
  const [sessionTasks, setSessionTasks] = useState<ClientTaskRecord[]>(() => {
    if (typeof window === "undefined") return [];
    try {
      const stored = localStorage.getItem(LOCAL_STORAGE_TASKS_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed)) return parsed;
      }
    } catch {
      // ignore
    }
    return [];
  });

  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState<boolean>(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState<boolean>(false);

  // Save session tasks to localStorage
  const persistTasks = useCallback((tasks: ClientTaskRecord[]) => {
    try {
      localStorage.setItem(LOCAL_STORAGE_TASKS_KEY, JSON.stringify(tasks.slice(-50)));
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
      // If backend is offline, maintain empty or existing
    } finally {
      setIsLoadingModels(false);
    }
  }, []);

  // Periodic health check & initial model fetch
  useEffect(() => {
    let isSubscribed = true;

    const initialize = async () => {
      try {
        const h = await getHealth();
        if (isSubscribed) {
          setHealth(h);
          setIsBackendOnline(true);
        }
      } catch {
        if (isSubscribed) setIsBackendOnline(false);
      }

      try {
        const m = await listModels();
        if (isSubscribed) {
          setModels(m.models || []);
          if (m.default_model) setDefaultModel(m.default_model);
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
      setSessionTasks((prev) => {
        const updated = [task, ...prev.filter((t) => t.run_id !== task.run_id)];
        persistTasks(updated);
        return updated;
      });
      setActiveRunId(task.run_id);
    },
    [persistTasks]
  );

  const updateSessionTask = useCallback(
    (runId: string, updates: Partial<ClientTaskRecord>) => {
      setSessionTasks((prev) => {
        const updated = prev.map((t) =>
          t.run_id === runId ? { ...t, ...updates } : t
        );
        persistTasks(updated);
        return updated;
      });
    },
    [persistTasks]
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
