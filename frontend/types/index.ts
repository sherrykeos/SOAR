export interface HealthResponse {
  status: string;
  app: string;
  version: string;
}

export interface TaskRequest {
  task: string;
  model?: string | null;
}

export interface TaskModelInfo {
  requested?: string | null;
  actual?: string | null;
  fallback_used?: boolean;
  fallback_reason?: string | null;
  duration_seconds?: number;
}

export interface TaskResponse {
  run_id: string;
  status: string;
  answer: string;
  model: string;
  execution_mode: string;
  citations: Array<Record<string, unknown>>;
  model_details?: Record<string, unknown> | null;
  events: Array<Record<string, unknown>>;
}

export interface EventItem {
  event_id: string;
  run_id?: string;
  stage: string;
  status: string;
  message: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export interface TaskEventsResponse {
  run_id: string;
  events: EventItem[];
}

export interface FileMetadata {
  file_id: string;
  original_filename: string;
  size_bytes: number;
  mime_type?: string | null;
  sha256: string;
  created_at: string;
}

export interface FileListResponse {
  total: number;
  files: FileMetadata[];
}

export interface FileDeleteResponse {
  status: string;
  file_id: string;
}

export interface ModelItem {
  id: string;
  provider: string;
  capabilities: string[];
  priority: number;
  enabled: boolean;
  available: boolean;
  timeout?: number | null;
}

export interface ModelListResponse {
  default_model: string;
  models: ModelItem[];
}

export interface ErrorResponse {
  error: string;
  message: string;
  details?: unknown;
}

export interface ClientTaskRecord {
  run_id: string;
  task: string;
  model: string;
  status: "submitted" | "running" | "completed" | "failed";
  created_at: string;
  duration_seconds?: number;
  answer?: string;
  events: EventItem[];
  attached_files?: string[];
  execution_mode?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  attached_files?: string[];
  run_id?: string;
  status?: "submitted" | "running" | "completed" | "failed";
  events?: EventItem[];
  duration_seconds?: number;
  model?: string;
  execution_mode?: string;
}

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  model: string;
  messages: ChatMessage[];
}

