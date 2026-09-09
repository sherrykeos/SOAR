"use client";

import React from "react";
import {
  FileText,
  ScanEye,
  Terminal,
  Database,
  FileCode,
  ShieldCheck,
  Lock,
} from "lucide-react";

export default function ToolsRegistryPage() {
  const tools = [
    {
      id: "pdf_reader",
      name: "PDF & Document Parser",
      category: "Document Processing",
      desc: "Reads local PDF, DOCX, and text files. Extracts text streams, structural outlines, and tabular records directly into memory.",
      sandbox: "Filesystem Read-Only",
      icon: FileText,
      status: "Available Locally",
    },
    {
      id: "vision_processor",
      name: "Multimodal OCR & Vision",
      category: "Vision & OCR",
      desc: "Invokes local Qwen2.5-VL 3B model to analyze engineering diagrams, scanned inspection reports, and spectrogram charts.",
      sandbox: "Memory Isolated",
      icon: ScanEye,
      status: "Available Locally",
    },
    {
      id: "python_sandbox",
      name: "Python Code Sandbox",
      category: "Code Execution",
      desc: "Executes Python scripts, mathematical simulations, and data transformations within an isolated sandbox with timeout enforcement.",
      sandbox: "10s Strict Timeout",
      icon: Terminal,
      status: "Available Locally",
    },
    {
      id: "vector_retriever",
      name: "ChromaDB Vector Store",
      category: "Knowledge Retrieval",
      desc: "Queries local dense embeddings (BGE-M3, 1024-dim) for semantic cross-referencing against internal SOP manuals and standards.",
      sandbox: "Local DB Read",
      icon: Database,
      status: "Available Locally",
    },
    {
      id: "artifact_emitter",
      name: "Artifact & Document Writer",
      category: "Output Generation",
      desc: "Generates final Word documents, Excel spreadsheets, Markdown notes, and JSON payloads with SHA256 integrity hashing.",
      sandbox: "Managed Output Directory",
      icon: FileCode,
      status: "Available Locally",
    },
  ];

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-6xl mx-auto w-full font-sans">
      {/* Header */}
      <div className="pb-4 border-b border-[#202A22]">
        <h1 className="text-xl sm:text-2xl font-bold text-[#F1F5ED]">
          Tool Registry
        </h1>
        <p className="text-xs text-[#9BA79D] mt-1">
          Registered local tools invoked autonomously by SOAR during multi-step DAG execution.
        </p>
      </div>

      {/* Security note */}
      <div className="p-3.5 rounded-lg bg-[#0D120F] border border-[#202A22] text-xs font-mono text-[#9BA79D] flex items-center gap-3">
        <ShieldCheck className="w-4 h-4 text-[#B8F23D] shrink-0" />
        <span>
          Tools execute within strictly sandboxed OS processes with read-only protections on input archives and zero external internet access.
        </span>
      </div>

      {/* Tools Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
        {tools.map((tool) => {
          const Icon = tool.icon;
          return (
            <div
              key={tool.id}
              className="p-5 rounded-xl bg-[#0D120F] border border-[#202A22] hover:border-[#B8F23D]/30 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-lg bg-[#121812] border border-[#202A22] text-[#B8F23D]">
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="font-bold text-[#F1F5ED] text-sm">
                        {tool.name}
                      </div>
                      <div className="text-[10px] text-[#657066]">
                        <code>{tool.id}</code>
                      </div>
                    </div>
                  </div>

                  <span className="px-2 py-0.5 rounded bg-[#22C55E]/10 text-[#4ADE80] border border-[#22C55E]/30 text-[10px] uppercase font-bold flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#22C55E]" />
                    {tool.status}
                  </span>
                </div>

                <p className="text-xs text-[#9BA79D] leading-relaxed font-sans mt-3">
                  {tool.desc}
                </p>
              </div>

              <div className="pt-4 mt-4 border-t border-[#202A22] flex items-center justify-between text-[11px] text-[#657066]">
                <span>Category: <strong className="text-[#9BA79D]">{tool.category}</strong></span>
                <span className="flex items-center gap-1 text-[#D5FF78]">
                  <Lock className="w-3 h-3" />
                  {tool.sandbox}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
