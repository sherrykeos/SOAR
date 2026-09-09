import { apiClient } from "./client";
import type { ModelListResponse } from "@/types";

export async function listModels(): Promise<ModelListResponse> {
  return apiClient<ModelListResponse>("/models");
}
