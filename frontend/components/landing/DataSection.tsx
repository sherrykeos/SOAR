import React from "react";
import {
  FolderOpen,
  Database,
  Cpu,
  Wrench,
  ShieldCheck,
  FileCheck2,
  Lock,
} from "lucide-react";

export function DataSection() {
  const pillars = [
    {
      title: "Local Files",
      desc: "Upload PDFs, Word docs, spreadsheets, engineering CAD drawings, and sensor logs stored securely on your local SSD.",
      icon: FolderOpen,
      metric: "50 MB Max / File",
    },
    {
      title: "Local Knowledge",
      desc: "ChromaDB vector store with BAAI/bge-m3 dense embeddings for semantic search over organizational SOPs and past records.",
      icon: Database,
      metric: "Local Vector Store",
    },
    {
      title: "Local Models",
      desc: "Connects to Ollama / open-weight models (Qwen, DeepSeek, Llama) with dynamic routing based on general, reasoning, coding, or vision needs.",
      icon: Cpu,
      metric: "Dynamic Quant Pool",
    },
    {
      title: "Local Tools",
      desc: "Native sandboxed tool executions including PDF parsing, OCR vision, code sandbox, and calculations with deterministic parameterization.",
      icon: Wrench,
      metric: "Process Isolated",
    },
  ];

  return (
    <section id="architecture" className="py-24 border-b border-[#202A22]/60 bg-[#070A08] relative">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Narrative Column */}
          <div className="lg:col-span-5 space-y-6">
            <span className="text-xs font-mono uppercase tracking-widest text-[#B8F23D] font-semibold">
              DATA SOVEREIGNTY ARCHITECTURE
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight leading-tight">
              Your machine. <br />
              Your data. <br />
              <span className="text-[#D5FF78]">Your context.</span>
            </h2>
            <p className="text-sm text-[#9BA79D] leading-relaxed">
              Traditional cloud AI requires sending sensitive industrial data, confidential reports, and proprietary drawings to external servers.
            </p>
            <p className="text-sm text-[#9BA79D] leading-relaxed">
              SOAR runs on your own infrastructure with strict network policies, local weights, and sandboxed tool execution. Nothing leaves your perimeter.
            </p>

            <div className="space-y-3 pt-2 font-mono text-xs">
              <div className="flex items-center gap-2.5 text-[#F1F5ED]">
                <ShieldCheck className="w-4 h-4 text-[#22C55E]" />
                <span>Zero outbound analytics or external cloud pings</span>
              </div>
              <div className="flex items-center gap-2.5 text-[#F1F5ED]">
                <FileCheck2 className="w-4 h-4 text-[#B8F23D]" />
                <span>Local filesystem storage with SHA256 integrity checks</span>
              </div>
              <div className="flex items-center gap-2.5 text-[#F1F5ED]">
                <Lock className="w-4 h-4 text-[#A78BFA]" />
                <span>Isolated sandbox process execution limits</span>
              </div>
            </div>
          </div>

          {/* Architecture Cards Column */}
          <div className="lg:col-span-7">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {pillars.map((p) => {
                const Icon = p.icon;
                return (
                  <div
                    key={p.title}
                    className="p-5 rounded-xl bg-[#0D120F] border border-[#202A22] hover:border-[#B8F23D]/30 transition-all duration-200"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="w-9 h-9 rounded-lg bg-[#121812] border border-[#202A22] flex items-center justify-center text-[#B8F23D]">
                        <Icon className="w-4 h-4" />
                      </div>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#171E18] text-[#9BA79D] border border-[#202A22]">
                        {p.metric}
                      </span>
                    </div>

                    <h3 className="text-sm font-bold text-[#F1F5ED] mb-1.5">
                      {p.title}
                    </h3>
                    <p className="text-xs text-[#9BA79D] leading-relaxed">
                      {p.desc}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
