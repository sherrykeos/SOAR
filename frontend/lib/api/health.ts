import { apiClient } from "./client";
import type { HealthResponse } from "@/types";

export async function getHealth(): Promise<HealthResponse> {
  return apiClient<HealthResponse>("/health");
}
