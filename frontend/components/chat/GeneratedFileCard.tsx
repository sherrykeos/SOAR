"use client";

import { FileText, Download, ExternalLink } from "lucide-react";
import type { GeneratedFile } from "@/types";

interface GeneratedFileCardProps {
  file: GeneratedFile;
}

function getDownloadUrl(fileId: string): string {
  return `/api/files/${encodeURIComponent(fileId)}/download`;
}

function getFileLabel(mimeType?: string | null): string {
  if (!mimeType) return "File";
  if (mimeType.includes("pdf")) return "PDF";
  if (
    mimeType.includes("wordprocessingml") ||
    mimeType.includes("docx") ||
    mimeType.includes("vnd.openxmlformats")
  )
    return "DOCX";
  return "File";
}

export function GeneratedFileCard({ file }: GeneratedFileCardProps) {
  const downloadUrl = getDownloadUrl(file.file_id);
  const fileLabel = getFileLabel(file.mime_type);

  return (
    <div className="flex items-center justify-between gap-3 px-4 py-3 rounded-xl bg-[#0D120F] border border-[#B8F23D]/20 mt-3">
      <div className="flex items-center gap-3 min-w-0">
        <div className="p-2 rounded-lg bg-[#121812] border border-[#202A22] shrink-0">
          <FileText className="w-4 h-4 text-[#B8F23D]" />
        </div>
        <div className="min-w-0">
          <div className="text-xs font-semibold text-[#F1F5ED] truncate max-w-[220px]">
            {file.filename}
          </div>
          <div className="text-[10px] font-mono text-[#657066] uppercase mt-0.5">
            {fileLabel} &middot; Generated
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2 shrink-0">
        <a
          href={downloadUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#121812] border border-[#202A22] hover:border-[#B8F23D]/40 text-[#9BA79D] hover:text-[#F1F5ED] transition text-[11px] font-mono cursor-pointer"
          title="Open file"
        >
          <ExternalLink className="w-3 h-3" />
          <span>Open</span>
        </a>

        <a
          href={downloadUrl}
          download={file.filename}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#B8F23D]/10 border border-[#B8F23D]/30 hover:bg-[#B8F23D]/20 text-[#B8F23D] hover:text-[#D5FF78] transition text-[11px] font-mono cursor-pointer"
          title="Download file"
        >
          <Download className="w-3 h-3" />
          <span>Download</span>
        </a>
      </div>
    </div>
  );
}
