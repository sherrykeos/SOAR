const API_BASE_URL =
  typeof window === "undefined"
    ? process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000"
    : "";

export class ApiError extends Error {
  status: number;
  data?: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

export interface ApiClientOptions extends RequestInit {
  timeoutMs?: number;
}

export async function apiClient<T>(
  endpoint: string,
  options: ApiClientOptions = {}
): Promise<T> {
  const normalizedEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const prefix = normalizedEndpoint.startsWith("/api") ? "" : "/api";
  const url = `${API_BASE_URL}${prefix}${normalizedEndpoint}`;

  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const timeoutMs = options.timeoutMs ?? 60000;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(url, {
      ...options,
      headers,
      signal: options.signal || controller.signal,
    });

    clearTimeout(timeoutId);

    if (!res.ok) {
      let errorData: unknown = null;
      let errorMsg = `HTTP ${res.status}: ${res.statusText}`;

      try {
        errorData = await res.json();
        if (
          errorData &&
          typeof errorData === "object" &&
          "message" in errorData &&
          typeof (errorData as { message: unknown }).message === "string"
        ) {
          errorMsg = (errorData as { message: string }).message;
        } else if (
          errorData &&
          typeof errorData === "object" &&
          "detail" in errorData
        ) {
          const detail = (errorData as { detail: unknown }).detail;
          errorMsg = typeof detail === "string" ? detail : JSON.stringify(detail);
        }
      } catch {
        // Next.js rewrites can return a plain-text proxy error.
        try {
          const text = await res.text();
          if (text.trim()) errorMsg = text.trim();
        } catch {
          // Keep the status-based message.
        }
      }

      throw new ApiError(errorMsg, res.status, errorData);
    }

    if (res.status === 204) {
      return {} as T;
    }

    return (await res.json()) as T;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof ApiError) {
      throw error;
    }
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError("Request timed out after 30 seconds.", 408);
    }
    throw new ApiError(
      error instanceof Error ? error.message : "Network error. Backend may be offline.",
      0
    );
  }
}
