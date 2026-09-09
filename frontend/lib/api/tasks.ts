import { apiClient } from "./client";
import type { TaskRequest, TaskResponse, TaskEventsResponse } from "@/types";

export async function createTask(req: TaskRequest): Promise<TaskResponse> {
  return apiClient<TaskResponse>("/tasks", {
    method: "POST",
    body: JSON.stringify(req),
    timeoutMs: 180000,
  });
}

export async function getTaskEvents(runId: string): Promise<TaskEventsResponse> {
  return apiClient<TaskEventsResponse>(`/tasks/${encodeURIComponent(runId)}/events`);
}
