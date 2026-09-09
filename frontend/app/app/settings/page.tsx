"use client";

import React, { useState } from "react";
import {
  ShieldCheck,
  HardDrive,
  Cpu,
  Lock,
  Info,
} from "lucide-react";
import { useWorkbench } from "@/context/WorkbenchContext";

export default function SettingsPage() {
  const { defaultModel } = useWorkbench();
  const [activeTab, setActiveTab] = useState<"security" | "storage" | "models" | "execution">("security");

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-5xl mx-auto w-full font-sans">
      {/* Header */}
      <div className="pb-4 border-b border-[#202A22]">
        <h1 className="text-xl sm:text-2xl font-bold text-[#F1F5ED]">
          System Settings & Policy
        </h1>
        <p className="text-xs text-[#9BA79D] mt-1">
          Host configuration parameters loaded from local <code>config/config.yaml</code>.
        </p>
      </div>

      {/* Notice */}
      <div className="p-3.5 rounded-lg bg-[#0D120F] border border-[#202A22] text-xs font-mono text-[#9BA79D] flex items-center gap-3">
        <Info className="w-4 h-4 text-[#B8F23D] shrink-0" />
        <span>
          Host settings are managed via <code>config.yaml</code> on the local filesystem. To preserve sovereign security boundaries, remote write configuration is disabled.
        </span>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-[#202A22] pb-3 font-mono text-xs">
        <button
          onClick={() => setActiveTab("security")}
          className={`px-3 py-1.5 rounded-lg transition ${
            activeTab === "security"
              ? "bg-[#171E18] text-[#D5FF78] border border-[#B8F23D]/40 font-semibold"
              : "text-[#9BA79D] hover:bg-[#121812] hover:text-[#F1F5ED]"
          }`}
        >
          Security & Air-Gap
        </button>
        <button
          onClick={() => setActiveTab("storage")}
          className={`px-3 py-1.5 rounded-lg transition ${
            activeTab === "storage"
              ? "bg-[#171E18] text-[#D5FF78] border border-[#B8F23D]/40 font-semibold"
              : "text-[#9BA79D] hover:bg-[#121812] hover:text-[#F1F5ED]"
          }`}
        >
          Storage Paths
        </button>
        <button
          onClick={() => setActiveTab("models")}
          className={`px-3 py-1.5 rounded-lg transition ${
            activeTab === "models"
              ? "bg-[#171E18] text-[#D5FF78] border border-[#B8F23D]/40 font-semibold"
              : "text-[#9BA79D] hover:bg-[#121812] hover:text-[#F1F5ED]"
          }`}
        >
          Model Policies
        </button>
        <button
          onClick={() => setActiveTab("execution")}
          className={`px-3 py-1.5 rounded-lg transition ${
            activeTab === "execution"
              ? "bg-[#171E18] text-[#D5FF78] border border-[#B8F23D]/40 font-semibold"
              : "text-[#9BA79D] hover:bg-[#121812] hover:text-[#F1F5ED]"
          }`}
        >
          Agent Execution
        </button>
      </div>

      {/* Tab Contents */}
      <div className="rounded-xl bg-[#0D120F] border border-[#202A22] p-6 space-y-6 font-mono text-xs">
        {activeTab === "security" && (
          <div className="space-y-4">
            <div className="flex items-center gap-2 pb-2 border-b border-[#202A22] text-[#F1F5ED] font-bold text-sm">
              <ShieldCheck className="w-4 h-4 text-[#B8F23D]" />
              <span>Network Isolation & Telemetry</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-3.5 rounded-lg bg-[#070A08] border border-[#202A22] space-y-1">
                <div className="text-[#657066] text-[10px] uppercase">External Network Policy</div>
                <div className="text-sm font-bold text-[#22C55E]">DISABLED</div>
                <div className="text-[10px] text-[#657066]">
                  <code>allow_external_network: false</code>
                </div>
              </div>

              <div className="p-3.5 rounded-lg bg-[#070A08] border border-[#202A22] space-y-1">
                <div className="text-[#657066] text-[10px] uppercase">Telemetry Egress</div>
                <div className="text-sm font-bold text-[#22C55E]">ZERO OUTBOUND</div>
                <div className="text-[10px] text-[#657066]">All packets bound to 127.0.0.1</div>
              </div>
            </div>

            <p className="text-xs text-[#9BA79D] font-sans leading-relaxed pt-2">
              SOAR operates strictly within your local security envelope. Outbound cloud API requests are disallowed by default configuration.
            </p>
          </div>
        )}

        {activeTab === "storage" && (
          <div className="space-y-4">
            <div className="flex items-center gap-2 pb-2 border-b border-[#202A22] text-[#F1F5ED] font-bold text-sm">
              <HardDrive className="w-4 h-4 text-[#B8F23D]" />
              <span>Managed Filesystem Directories</span>
            </div>

            <div className="space-y-2.5">
              <div className="p-3 rounded-lg bg-[#070A08] border border-[#202A22] flex justify-between items-center">
                <span className="text-[#657066]">Managed Upload Root:</span>
                <span className="text-[#F1F5ED]"><code>./data/files</code></span>
              </div>
              <div className="p-3 rounded-lg bg-[#070A08] border border-[#202A22] flex justify-between items-center">
                <span className="text-[#657066]">Vector Store Root:</span>
                <span className="text-[#F1F5ED]"><code>./data/chroma</code></span>
              </div>
              <div className="p-3 rounded-lg bg-[#070A08] border border-[#202A22] flex justify-between items-center">
                <span className="text-[#657066]">Metadata SQLite Database:</span>
                <span className="text-[#F1F5ED]"><code>./data/soar.db</code></span>
              </div>
              <div className="p-3 rounded-lg bg-[#070A08] border border-[#202A22] flex justify-between items-center">
                <span className="text-[#657066]">Maximum File Size:</span>
                <span className="text-[#D5FF78]">50 MB (52,428,800 bytes)</span>
              </div>
            </div>
          </div>
        )}

        {activeTab === "models" && (
          <div className="space-y-4">
            <div className="flex items-center gap-2 pb-2 border-b border-[#202A22] text-[#F1F5ED] font-bold text-sm">
              <Cpu className="w-4 h-4 text-[#B8F23D]" />
              <span>Inference Engine & Model Routing</span>
            </div>

            <div className="space-y-2.5">
              <div className="p-3 rounded-lg bg-[#070A08] border border-[#202A22] flex justify-between items-center">
                <span className="text-[#657066]">Inference Backend:</span>
                <span className="text-[#F1F5ED]">Ollama Server (<code>http://localhost:11434</code>)</span>
              </div>
              <div className="p-3 rounded-lg bg-[#070A08] border border-[#202A22] flex justify-between items-center">
                <span className="text-[#657066]">Default Model ID:</span>
                <span className="text-[#D5FF78] font-bold">{defaultModel || "qwen3:1.7b"}</span>
              </div>
              <div className="p-3 rounded-lg bg-[#070A08] border border-[#202A22] flex justify-between items-center">
                <span className="text-[#657066]">Hard Model Timeout:</span>
                <span className="text-[#F1F5ED]">15.0 seconds</span>
              </div>
              <div className="p-3 rounded-lg bg-[#070A08] border border-[#202A22] flex justify-between items-center">
                <span className="text-[#657066]">Dense Embedding Model:</span>
                <span className="text-[#F1F5ED]">BAAI/bge-m3 (1024-dim, normalized)</span>
              </div>
            </div>
          </div>
        )}

        {activeTab === "execution" && (
          <div className="space-y-4">
            <div className="flex items-center gap-2 pb-2 border-b border-[#202A22] text-[#F1F5ED] font-bold text-sm">
              <Lock className="w-4 h-4 text-[#B8F23D]" />
              <span>Sandbox & Agent Iteration Limits</span>
            </div>

            <div className="space-y-2.5">
              <div className="p-3 rounded-lg bg-[#070A08] border border-[#202A22] flex justify-between items-center">
                <span className="text-[#657066]">Max Agent Iterations:</span>
                <span className="text-[#D5FF78] font-bold">5 iterations</span>
              </div>
              <div className="p-3 rounded-lg bg-[#070A08] border border-[#202A22] flex justify-between items-center">
                <span className="text-[#657066]">Python Sandbox Timeout:</span>
                <span className="text-[#F1F5ED]">10 seconds</span>
              </div>
              <div className="p-3 rounded-lg bg-[#070A08] border border-[#202A22] flex justify-between items-center">
                <span className="text-[#657066]">Execution Progress Events:</span>
                <span className="text-[#22C55E] font-semibold">ENABLED</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
