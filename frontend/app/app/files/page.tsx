"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  FolderOpen,
  UploadCloud,
  FileText,
  Download,
  Trash2,
  FileCode2,
  Image as ImageIcon,
  FileSpreadsheet,
  RotateCw,
  Search,
  Eye,
} from "lucide-react";
import {
  listFiles,
  uploadFile,
  deleteFile,
  getFileDownloadUrl,
} from "@/lib/api/files";
import { formatBytes, formatDate } from "@/lib/utils/formatters";
import type { FileMetadata } from "@/types";
import { useToast } from "@/components/ui/Toast";
import { EmptyState } from "@/components/ui/EmptyState";
import { Modal } from "@/components/ui/Modal";

export default function FileManagerPage() {
  const { success, error } = useToast();

  const [files, setFiles] = useState<FileMetadata[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [search, setSearch] = useState("");

  // Delete modal state
  const [fileToDelete, setFileToDelete] = useState<FileMetadata | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // File preview modal state
  const [previewFile, setPreviewFile] = useState<FileMetadata | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadFiles = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await listFiles(100, 0);
      setFiles(res.files || []);
    } catch (err) {
      error("Failed to list files", err instanceof Error ? err.message : "Backend offline");
    } finally {
      setIsLoading(false);
    }
  }, [error]);

  useEffect(() => {
    let isSubscribed = true;
    const fetchCatalog = async () => {
      try {
        const res = await listFiles(100, 0);
        if (isSubscribed) {
          setFiles(res.files || []);
          setIsLoading(false);
        }
      } catch {
        if (isSubscribed) {
          setIsLoading(false);
        }
      }
    };
    fetchCatalog();
    return () => {
      isSubscribed = false;
    };
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files;
    if (!selectedFiles || selectedFiles.length === 0) return;

    setIsUploading(true);
    let successCount = 0;

    for (let i = 0; i < selectedFiles.length; i++) {
      const f = selectedFiles[i];
      try {
        const uploaded = await uploadFile(f);
        setFiles((prev) => [uploaded, ...prev]);
        successCount++;
      } catch (err) {
        error(
          `Failed to upload ${f.name}`,
          err instanceof Error ? err.message : "File rejected"
        );
      }
    }

    if (successCount > 0) {
      success("Files uploaded", `${successCount} file(s) saved to local storage`);
    }

    setIsUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleConfirmDelete = async () => {
    if (!fileToDelete) return;
    setIsDeleting(true);
    try {
      await deleteFile(fileToDelete.file_id);
      setFiles((prev) => prev.filter((f) => f.file_id !== fileToDelete.file_id));
      success("File deleted", fileToDelete.original_filename);
      setFileToDelete(null);
    } catch (err) {
      error("Delete failed", err instanceof Error ? err.message : "Could not delete file");
    } finally {
      setIsDeleting(false);
    }
  };

  const getFileIcon = (filename: string, mime?: string | null) => {
    const ext = filename.split(".").pop()?.toLowerCase();
    if (ext === "pdf" || mime?.includes("pdf")) {
      return <FileText className="w-4 h-4 text-[#EF4444]" />;
    }
    if (["xlsx", "xls", "csv"].includes(ext || "") || mime?.includes("sheet")) {
      return <FileSpreadsheet className="w-4 h-4 text-[#22C55E]" />;
    }
    if (["png", "jpg", "jpeg", "webp"].includes(ext || "") || mime?.includes("image")) {
      return <ImageIcon className="w-4 h-4 text-[#60A5FA]" />;
    }
    if (["py", "ts", "js", "json", "yaml"].includes(ext || "")) {
      return <FileCode2 className="w-4 h-4 text-[#A78BFA]" />;
    }
    return <FileText className="w-4 h-4 text-[#9BA79D]" />;
  };

  const filteredFiles = files.filter((f) => {
    const matchesSearch = f.original_filename
      .toLowerCase()
      .includes(search.toLowerCase());
    return matchesSearch;
  });

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-6xl mx-auto w-full font-sans">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#202A22]">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-[#F1F5ED]">
            Managed Files
          </h1>
          <p className="text-xs text-[#9BA79D] mt-1">
            Local storage sandbox. Files are processed on-premise with SHA256 cryptographic tracking.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <input
            ref={fileInputRef}
            type="file"
            multiple
            onChange={handleFileUpload}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-[#B8F23D] text-[#070A08] font-semibold text-xs hover:bg-[#D5FF78] transition shadow-sm cursor-pointer disabled:opacity-50"
          >
            <UploadCloud className="w-4 h-4" />
            <span>{isUploading ? "Uploading..." : "Upload File"}</span>
          </button>
          <button
            onClick={loadFiles}
            className="p-2 rounded-lg bg-[#121812] border border-[#202A22] text-[#9BA79D] hover:text-[#F1F5ED] hover:border-[#2B382D] transition cursor-pointer"
            title="Refresh files"
          >
            <RotateCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Drag & Drop Quick Zone */}
      <div
        onClick={() => fileInputRef.current?.click()}
        className="p-6 rounded-xl bg-[#0D120F] border border-[#202A22] border-dashed hover:border-[#B8F23D]/50 hover:bg-[#121812]/60 transition-all cursor-pointer text-center group"
      >
        <UploadCloud className="w-8 h-8 text-[#657066] group-hover:text-[#B8F23D] transition-colors mx-auto mb-2" />
        <div className="text-xs font-semibold text-[#F1F5ED] group-hover:text-white transition">
          Click or drop local files to upload
        </div>
        <p className="text-[11px] font-mono text-[#657066] mt-1">
          Supports PDF, DOCX, XLSX, CSV, Images, Code (Max 50 MB / file)
        </p>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-[#657066] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search files..."
            className="w-full bg-[#0D120F] border border-[#202A22] rounded-lg pl-9 pr-4 py-2 text-xs text-[#F1F5ED] placeholder:text-[#657066] focus:outline-none focus:border-[#B8F23D]/50 font-mono"
          />
        </div>

        <div className="text-xs font-mono text-[#657066] self-end sm:self-center">
          Total stored: <strong className="text-[#F1F5ED]">{files.length}</strong> files
        </div>
      </div>

      {/* Files List Table */}
      {isLoading ? (
        <div className="p-12 text-center text-[#657066] font-mono text-xs space-y-2">
          <RotateCw className="w-6 h-6 mx-auto animate-spin text-[#B8F23D]" />
          <div>Loading local storage catalog...</div>
        </div>
      ) : filteredFiles.length === 0 ? (
        <EmptyState
          icon={<FolderOpen className="w-6 h-6" />}
          title="No files found"
          description={
            search
              ? "No files match your search query."
              : "No files currently in local storage. Upload a document to use in tasks."
          }
          action={
            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-3.5 py-1.5 rounded-lg bg-[#121812] border border-[#202A22] hover:border-[#B8F23D]/40 text-xs font-mono text-[#F1F5ED] hover:text-[#D5FF78] transition flex items-center gap-1.5 cursor-pointer"
            >
              <UploadCloud className="w-3.5 h-3.5" />
              <span>Upload Document</span>
            </button>
          }
        />
      ) : (
        <div className="rounded-xl bg-[#0D120F] border border-[#202A22] overflow-hidden font-mono text-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-[#202A22] bg-[#121812] text-[#657066] uppercase text-[10px] tracking-wider">
                  <th className="py-3 px-4">Filename</th>
                  <th className="py-3 px-4">Size</th>
                  <th className="py-3 px-4 hidden md:table-cell">SHA256</th>
                  <th className="py-3 px-4 hidden sm:table-cell">Uploaded</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#202A22]/60">
                {filteredFiles.map((file) => (
                  <tr
                    key={file.file_id}
                    className="hover:bg-[#121812]/50 transition-colors"
                  >
                    <td className="py-3 px-4 flex items-center gap-2.5 min-w-[200px]">
                      {getFileIcon(file.original_filename, file.mime_type)}
                      <span className="font-semibold text-[#F1F5ED] truncate max-w-[240px]">
                        {file.original_filename}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-[#9BA79D]">
                      {formatBytes(file.size_bytes)}
                    </td>
                    <td className="py-3 px-4 text-[#657066] hidden md:table-cell select-all font-mono text-[11px]">
                      {file.sha256 ? `${file.sha256.substring(0, 12)}...` : "--"}
                    </td>
                    <td className="px-4 py-3 text-right text-xs text-[#9BA79D]" suppressHydrationWarning>
                      {formatDate(file.created_at)}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        {/* Preview / Inspect */}
                        <button
                          onClick={() => setPreviewFile(file)}
                          className="p-1.5 rounded hover:bg-[#171E18] text-[#9BA79D] hover:text-[#F1F5ED] transition cursor-pointer"
                          title="View metadata"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </button>

                        {/* Download */}
                        <a
                          href={getFileDownloadUrl(file.file_id)}
                          download={file.original_filename}
                          className="p-1.5 rounded hover:bg-[#171E18] text-[#9BA79D] hover:text-[#D5FF78] transition"
                          title="Download binary"
                        >
                          <Download className="w-3.5 h-3.5" />
                        </a>

                        {/* Delete */}
                        <button
                          onClick={() => setFileToDelete(file)}
                          className="p-1.5 rounded hover:bg-[#EF4444]/15 text-[#657066] hover:text-[#EF4444] transition cursor-pointer"
                          title="Delete file"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* File Details / Preview Modal */}
      {previewFile && (
        <Modal
          isOpen={!!previewFile}
          onClose={() => setPreviewFile(null)}
          title="File Metadata & Integrity"
          description={previewFile.original_filename}
          maxWidth="md"
        >
          <div className="space-y-4 font-mono text-xs">
            <div className="p-3 rounded-lg bg-[#070A08] border border-[#202A22] space-y-2">
              <div className="flex justify-between">
                <span className="text-[#657066]">File ID:</span>
                <span className="text-[#F1F5ED] select-all">{previewFile.file_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#657066]">Size:</span>
                <span className="text-[#F1F5ED]">{formatBytes(previewFile.size_bytes)} ({previewFile.size_bytes} bytes)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#657066]">MIME Type:</span>
                <span className="text-[#F1F5ED]">{previewFile.mime_type || "application/octet-stream"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#657066]">Created:</span>
                <span className="text-[#F1F5ED]">{formatDate(previewFile.created_at)}</span>
              </div>
              <div className="pt-2 border-t border-[#202A22]">
                <div className="text-[#657066] text-[10px] uppercase mb-1">SHA256 Hash:</div>
                <div className="text-[11px] text-[#D5FF78] break-all select-all bg-[#0D120F] p-2 rounded border border-[#202A22]">
                  {previewFile.sha256}
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <a
                href={getFileDownloadUrl(previewFile.file_id)}
                download={previewFile.original_filename}
                className="px-4 py-2 rounded-lg bg-[#B8F23D] text-[#070A08] font-bold text-xs hover:bg-[#D5FF78] transition flex items-center gap-1.5"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download File</span>
              </a>
            </div>
          </div>
        </Modal>
      )}

      {/* Delete Confirmation Modal */}
      {fileToDelete && (
        <Modal
          isOpen={!!fileToDelete}
          onClose={() => setFileToDelete(null)}
          title="Delete Local File?"
          description="This action removes the file from SOAR local storage immediately."
          maxWidth="sm"
        >
          <div className="space-y-4 font-mono text-xs">
            <p className="text-[#9BA79D]">
              Are you sure you want to permanently delete{" "}
              <strong className="text-[#F1F5ED]">{fileToDelete.original_filename}</strong>?
            </p>

            <div className="flex justify-end gap-2 pt-3 border-t border-[#202A22]">
              <button
                onClick={() => setFileToDelete(null)}
                disabled={isDeleting}
                className="px-3 py-1.5 rounded-lg bg-[#121812] border border-[#202A22] text-[#9BA79D] hover:text-[#F1F5ED] transition cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmDelete}
                disabled={isDeleting}
                className="px-3 py-1.5 rounded-lg bg-[#EF4444] text-white font-bold hover:bg-[#DC2626] transition flex items-center gap-1.5 cursor-pointer"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>{isDeleting ? "Deleting..." : "Delete File"}</span>
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
