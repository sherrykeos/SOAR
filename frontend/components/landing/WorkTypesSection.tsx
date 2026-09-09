"use client";

import React from "react";
import {
  Search,
  ScanSearch,
  FilePlus2,
  Code2,
  Workflow,
  ArrowRight,
} from "lucide-react";
import { motion } from "framer-motion";
import Link from "next/link";

export function WorkTypesSection() {
  const workTypes = [
    {
      title: "Research",
      desc: "Explore topics, synthesize multi-source data, and create structured insights without external search engine leaks.",
      icon: Search,
      badge: "Semantic Search",
      details: ["Local vector indexing", "Source attribution & citations"],
    },
    {
      title: "Analyze",
      desc: "Work with complex engineering PDFs, spreadsheets, scans, and technical data to identify patterns and variances.",
      icon: ScanSearch,
      badge: "Multimodal & OCR",
      details: ["Tabular data extraction", "Threshold & tolerance validation"],
    },
    {
      title: "Create",
      desc: "Generate production-grade reports, approval notes, Word documents, and presentations formatted to strict internal guidelines.",
      icon: FilePlus2,
      badge: "Artifact Generation",
      details: ["Deterministic document synthesis", "Verifiable audit trail"],
    },
    {
      title: "Build",
      desc: "Write, test, and safely execute Python code in an isolated local sandbox to automate complex calculations.",
      icon: Code2,
      badge: "Sandboxed Execution",
      details: ["Process isolation", "Data transformation pipelines"],
    },
    {
      title: "Plan",
      desc: "Break complex, ambiguous objectives into ordered Directed Acyclic Graphs (DAGs) with automated tool selection and fallback.",
      icon: Workflow,
      badge: "Agent Orchestration",
      details: ["Autonomous DAG decomposition", "Self-correcting recovery routines"],
    },
  ];

  return (
    <section id="capabilities" className="py-24 border-b border-[#202A22]/60 bg-[#070A08] relative">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <span className="text-xs font-mono uppercase tracking-widest text-[#B8F23D] font-semibold">
            ONE WORKSPACE. MANY POSSIBILITIES.
          </span>
          <h2 className="text-3xl sm:text-5xl font-extrabold text-white mt-3 mb-4 tracking-tight">
            Do More. <span className="text-[#D5FF78]">Locally.</span>
          </h2>
          <p className="text-[#9BA79D] text-sm sm:text-base leading-relaxed">
            Replace fragmented external SaaS tools with a unified sovereign environment engineered for deep, mission-critical cognitive tasks.
          </p>
        </div>

        {/* 5 Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {workTypes.map((item, idx) => {
            const Icon = item.icon;
            const isWide = idx === 4; // 5th item spans 2 cols on lg screens
            return (
              <motion.div
                key={item.title}
                whileHover={{ y: -3 }}
                transition={{ duration: 0.2 }}
                className={`p-6 rounded-xl bg-[#0D120F] border border-[#202A22] hover:border-[#B8F23D]/40 hover:shadow-[0_0_24px_-4px_rgba(184,242,61,0.2)] transition-all duration-300 group flex flex-col justify-between ${
                  isWide ? "md:col-span-2 lg:col-span-2" : ""
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-5">
                    <div className="w-10 h-10 rounded-lg bg-[#121812] border border-[#202A22] flex items-center justify-center text-[#9BA79D] group-hover:text-[#B8F23D] group-hover:border-[#B8F23D]/30 transition-colors">
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className="px-2 py-0.5 rounded bg-[#171E18] text-[#9BA79D] border border-[#202A22] text-[10px] font-mono">
                      {item.badge}
                    </span>
                  </div>

                  <h3 className="text-lg font-bold text-[#F1F5ED] mb-2 group-hover:text-white transition-colors">
                    {item.title}
                  </h3>
                  <p className="text-xs text-[#9BA79D] leading-relaxed mb-6">
                    {item.desc}
                  </p>
                </div>

                <div className="border-t border-[#202A22] pt-4">
                  <div className="flex flex-wrap gap-3 mb-4">
                    {item.details.map((detail) => (
                      <span
                        key={detail}
                        className="text-[11px] font-mono text-[#657066] flex items-center gap-1.5"
                      >
                        <span className="text-[#B8F23D]">▹</span>
                        {detail}
                      </span>
                    ))}
                  </div>

                  <Link
                    href="/app"
                    className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#9BA79D] group-hover:text-[#D5FF78] transition-colors"
                  >
                    <span>Give SOAR a job</span>
                    <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-1" />
                  </Link>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
