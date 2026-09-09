"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import type { EventItem, TaskEventsResponse } from "@/types";
import { getTaskEvents } from "@/lib/api/tasks";

interface UseTaskEventsOptions {
  runId: string | null;
  initialEvents?: EventItem[];
  isCompleted?: boolean;
  onStatusChange?: (status: string) => void;
}

export function useTaskEvents({
  runId,
  initialEvents = [],
  isCompleted = false,
  onStatusChange,
}: UseTaskEventsOptions) {
  const [events, setEvents] = useState<EventItem[]>(initialEvents);
  const [isPolling, setIsPolling] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const isCompletedRef = useRef<boolean>(isCompleted);
  const unmountedRef = useRef<boolean>(false);
  const onStatusChangeRef = useRef(onStatusChange);

  useEffect(() => {
    isCompletedRef.current = isCompleted;
    onStatusChangeRef.current = onStatusChange;
  }, [isCompleted, onStatusChange]);

  useEffect(() => {
    if (initialEvents && initialEvents.length > 0) {
      setEvents(initialEvents);
    }
  }, [initialEvents]);

  const pollFn = useCallback(async (currentRunId: string) => {
    if (!currentRunId || isCompletedRef.current || unmountedRef.current) {
      return false;
    }

    try {
      const data: TaskEventsResponse = await getTaskEvents(currentRunId);
      if (unmountedRef.current) return false;

      if (data && Array.isArray(data.events)) {
        setEvents(data.events);

        const hasFinished = data.events.some(
          (e) =>
            (e.stage === "COMPLETED" ||
              e.stage === "FAILED" ||
              e.status === "completed" ||
              e.status === "failed") &&
            e.status !== "started" &&
            e.status !== "in_progress"
        );

        if (hasFinished) {
          isCompletedRef.current = true;
          const lastEvent = data.events[data.events.length - 1];
          onStatusChangeRef.current?.(lastEvent.status || "completed");
          return false;
        }
      }
      setError(null);
      return true;
    } catch (err) {
      if (!unmountedRef.current) {
        setError(err instanceof Error ? err.message : "Error fetching events");
      }
      // Stop polling on error (e.g. 404 Not Found or network error) to avoid spamming the backend
      return false;
    }
  }, []);

  useEffect(() => {
    unmountedRef.current = false;

    if (!runId || isCompleted) {
      setIsPolling(false);
      return;
    }

    let timer: NodeJS.Timeout | null = null;

    const runLoop = async () => {
      setIsPolling(true);
      const shouldContinue = await pollFn(runId);
      if (shouldContinue && !unmountedRef.current && !isCompletedRef.current) {
        timer = setTimeout(runLoop, 1500);
      } else if (!unmountedRef.current) {
        setIsPolling(false);
      }
    };

    runLoop();

    return () => {
      unmountedRef.current = true;
      if (timer) clearTimeout(timer);
    };
  }, [runId, isCompleted, pollFn]);

  const refreshNow = useCallback(() => {
    if (runId) {
      pollFn(runId);
    }
  }, [runId, pollFn]);

  return {
    events,
    isPolling,
    error,
    refreshNow,
  };
}
