"use client";

import React from "react";
import {
  Sparkles,
  Workflow,
  Cpu,
  Terminal,
  RotateCcw,
  PackageCheck,
} from "lucide-react";
import { motion } from "framer-motion";

export function ExecutionFlow() {
  const steps = [
    {
      num: "01",
      title: "Understand",
      subtitle: "INTENT VECTOR",
      desc: "Parses user prompt, resolves file references, and classifies workload domain using low-latency on-premise classification.",
      icon: Sparkles,
    },
    {
      num: "02",
      title: "Plan",
      subtitle: "DEPENDENCY DAG",
      desc: "Deconstructs high-level objectives into an ordered Directed Acyclic Graph (DAG) specifying tool invocations and execution checkpoints.",
      icon: Workflow,
    },
    {
      num: "03",
      title: "Select Model",
      subtitle: "DYNAMIC ROUTING",
      desc: "Selects the optimal local model (Qwen 1.7B general, Qwen 4B reasoning, Coder 1.5B, or VL 3B vision) based on task capability.",
      icon: Cpu,
    },
    {
      num: "04",
      title: "Execute",
      subtitle: "LOCAL TOOL CALLS",
      desc: "Invokes document parsers, OCR readers, local vector searches, and sandboxed Python scripts within isolated OS processes.",
      icon: Terminal,
    },
    {
      num: "05",
      title: "Adapt",
      subtitle: "SELF-CORRECTING",
      desc: "Monitors tool outputs and errors. If a step fails, SOAR modifies parameters and initiates automated recovery attempts.",
      icon: RotateCcw,
    },
    {
      num: "06",
      title: "Deliver",
      subtitle: "VERIFIED ARTIFACTS",
      desc: "Compiles final deliverables (Word, Excel, Markdown, code, or structured JSON) with complete execution provenance.",
      icon: PackageCheck,
      isFinal: true,
    },
  ];

  return (
    <section id="workflow" className="py-24 border-b border-[#202A22]/60 bg-[#040605] relative">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-16">
          <div>
            <span className="text-xs font-mono uppercase tracking-widest text-[#B8F23D] font-semibold">
              EXECUTION PIPELINE
            </span>
            <h2 className="text-3xl sm:text-5xl font-extrabold text-white mt-2 tracking-tight">
              From intent to <span className="text-[#D5FF78]">impact.</span>
            </h2>
          </div>
          <p className="text-[#9BA79D] text-sm max-w-md mt-4 md:mt-0 leading-relaxed">
            A deterministic execution pipeline designed to eliminate hallucinations, enforce tool verification, and maintain complete machine sovereignty.
          </p>
        </div>

        {/* 6 Stage Timeline */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {steps.map((step, idx) => {
            const Icon = step.icon;
            return (
              <motion.div
                key={step.num}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: idx * 0.1 }}
                className={`p-5 rounded-xl bg-[#0D120F] border transition-all duration-300 relative group ${
                  step.isFinal
                    ? "border-[#B8F23D]/50 hover:border-[#B8F23D] hover:shadow-[0_0_24px_-4px_rgba(184,242,61,0.3)]"
                    : "border-[#202A22] hover:border-[#2B382D] hover:bg-[#121812]"
                }`}
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs font-mono font-bold ${
                        step.isFinal ? "text-[#D5FF78]" : "text-[#B8F23D]"
                      }`}
                    >
                      STAGE {step.num}
                    </span>
                    <span className="text-[#657066]">·</span>
                    <span className="text-[10px] font-mono uppercase text-[#657066]">
                      {step.subtitle}
                    </span>
                  </div>
                  <div className="p-1.5 rounded-lg bg-[#171E18] text-[#9BA79D] group-hover:text-[#B8F23D] transition-colors">
                    <Icon className="w-4 h-4" />
                  </div>
                </div>

                <h3 className="text-base font-bold text-[#F1F5ED] mb-2 group-hover:text-white transition-colors">
                  {step.title}
                </h3>
                <p className="text-xs text-[#9BA79D] leading-relaxed">
                  {step.desc}
                </p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
