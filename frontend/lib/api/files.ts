import { apiClient } from "./client";
import type { FileMetadata, FileListResponse, FileDeleteResponse } from "@/types";

export async function uploadFile(file: File): Promise<FileMetadata> {
  const formData = new FormData();
  formData.append("file", file);

  return apiClient<FileMetadata>("/files/upload", {
    method: "POST",
    body: formData,
  });
}

export async function listFiles(
  limit: number = 50,
  offset: number = 0
): Promise<FileListResponse> {
  return apiClient<FileListResponse>(`/files?limit=${limit}&offset=${offset}`);
}

export async function getFileMetadata(fileId: string): Promise<FileMetadata> {
  return apiClient<FileMetadata>(`/files/${encodeURIComponent(fileId)}`);
}

export async function deleteFile(fileId: string): Promise<FileDeleteResponse> {
  return apiClient<FileDeleteResponse>(`/files/${encodeURIComponent(fileId)}`, {
    method: "DELETE",
  });
}

export function getFileDownloadUrl(fileId: string): string {
  const base =
    typeof window !== "undefined"
      ? ""
      : process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
  return `${base}/api/files/${encodeURIComponent(fileId)}/download`;
}
