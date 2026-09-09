"use client";

import React, { useState } from "react";
import {
  Check,
  Activity,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { motion } from "framer-motion";

export function RunInspectorShowcase() {
  const [expandedStep, setExpandedStep] = useState<number | null>(3);

  const stages = [
    {
      id: 0,
      name: "Task Classification",
      meta: "Engineering & Document Workflow",
      status: "completed",
      time: "10:24:01",
      details: "Deterministic classifier mapped intent to multi-step agent execution pipeline.",
    },
    {
      id: 1,
      name: "Model Selection",
      meta: "Qwen3 1.7B (Local Quant)",
      status: "completed",
      time: "10:24:02",
      details: "Capability match: General reasoning with low-latency tool calling over Ollama.",
    },
    {
      id: 2,
      name: "Planning & DAG Generation",
      meta: "Generated 4-step dependency graph",
      status: "completed",
      time: "10:24:03",
      details: "Step 1: Read PDF -> Step 2: Extract FFT vibration table -> Step 3: Check ISO limits -> Step 4: Generate memo.",
    },
    {
      id: 3,
      name: "Tool Execution",
      meta: "Active tool: pdf_reader",
      status: "running",
      time: "10:24:05",
      details: "Extracted 42 pages from ./inputs/inspection_rotor_04.pdf safely inside memory sandbox.",
    },
    {
      id: 4,
      name: "Reasoning & Variance Analysis",
      meta: "Pending tool output",
      status: "pending",
      time: "--:--:--",
      details: "Synthesizing harmonic vibration delta against ISO 10816-3 thresholds.",
    },
    {
      id: 5,
      name: "Output Generation",
      meta: "Word document & signed memo",
      status: "pending",
      time: "--:--:--",
      details: "Writing final defect clearance memo artifact.",
    },
  ];

  return (
    <section id="inspector" className="py-24 border-b border-[#202A22]/60 bg-[#040605] relative">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <span className="text-xs font-mono uppercase tracking-widest text-[#B8F23D] font-semibold">
            TELEMETRY & VISIBILITY
          </span>
          <h2 className="text-3xl sm:text-5xl font-extrabold text-white mt-3 mb-4 tracking-tight">
            Know what your AI is doing.
          </h2>
          <p className="text-[#9BA79D] text-sm sm:text-base leading-relaxed">
            No black-box opacity. SOAR displays deterministic checkpoints, tool invocations, and execution status — with zero private internal prompt leakage.
          </p>
        </div>

        {/* Large Inspector Container */}
        <div className="max-w-4xl mx-auto rounded-xl bg-[#0D120F] border border-[#202A22] shadow-2xl overflow-hidden font-mono">
          {/* Header */}
          <div className="p-4 bg-[#121812] border-b border-[#202A22] flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <Activity className="w-4 h-4 text-[#B8F23D]" />
              <span className="text-xs font-bold text-[#F1F5ED] tracking-wider">
                RUN INSPECTOR · RUN_9042A
              </span>
              <span className="px-2 py-0.5 rounded-full bg-[#B8F23D]/10 text-[#D5FF78] border border-[#B8F23D]/30 text-[10px] uppercase font-bold flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#B8F23D] animate-pulse" />
                RUNNING
              </span>
            </div>

            <div className="flex items-center gap-4 text-[11px] text-[#657066]">
              <span className="flex items-center gap-1 text-[#22C55E]">
                <ShieldCheck className="w-3.5 h-3.5" />
                Local Mode
              </span>
              <span>Stage 4 / 6</span>
            </div>
          </div>

          {/* Chronological Steps */}
          <div className="p-6 space-y-4">
            {stages.map((st) => {
              const isExpanded = expandedStep === st.id;
              const isCompleted = st.status === "completed";
              const isRunning = st.status === "running";

              return (
                <div
                  key={st.id}
                  className={`rounded-lg border transition-all duration-200 ${
                    isRunning
                      ? "bg-[#121812] border-[#B8F23D]/40"
                      : isCompleted
                      ? "bg-[#0A0E0C] border-[#202A22]"
                      : "bg-[#070A08]/50 border-[#202A22]/50 opacity-50"
                  }`}
                >
                  <div
                    onClick={() => setExpandedStep(isExpanded ? null : st.id)}
                    className="p-3.5 flex items-center justify-between cursor-pointer select-none"
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] shrink-0 ${
                          isCompleted
                            ? "bg-[#22C55E]/15 text-[#22C55E] border border-[#22C55E]/40"
                            : isRunning
                            ? "bg-[#B8F23D]/20 text-[#D5FF78] border border-[#B8F23D] animate-pulse"
                            : "bg-[#171E18] text-[#657066] border border-[#202A22]"
                        }`}
                      >
                        {isCompleted ? (
                          <Check className="w-3 h-3" />
                        ) : isRunning ? (
                          <span className="w-1.5 h-1.5 rounded-full bg-[#B8F23D]" />
                        ) : (
                          "○"
                        )}
                      </div>
                      <div>
                        <div
                          className={`text-xs font-semibold ${
                            isRunning ? "text-[#D5FF78]" : "text-[#F1F5ED]"
                          }`}
                        >
                          {st.name}
                        </div>
                        <div className="text-[11px] text-[#9BA79D]">{st.meta}</div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 text-xs text-[#657066]">
                      <span className="hidden sm:inline">{st.time}</span>
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      )}
                    </div>
                  </div>

                  {isExpanded && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      className="px-4 pb-3.5 pt-1 text-xs text-[#9BA79D] border-t border-[#202A22]/40 bg-[#070A08]/40"
                    >
                      <p className="leading-relaxed">{st.details}</p>
                    </motion.div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Footer Notice */}
          <div className="px-6 py-3 bg-[#070A08] border-t border-[#202A22] text-[10px] text-[#657066] flex justify-between items-center">
            <span>Privileged internal reasoning is hidden for security.</span>
            <span className="text-[#B8F23D] font-mono">Safe checkpoints verified</span>
          </div>
        </div>
      </div>
    </section>
  );
}
