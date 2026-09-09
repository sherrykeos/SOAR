"use client";

import React, { useState } from "react";
import {
  Check,
  Terminal,
  Activity,
  FileText,
  AlertTriangle,
  Sparkles,
  ArrowRight,
} from "lucide-react";
import Link from "next/link";

export function HeroProductPreview() {
  const [activeTab, setActiveTab] = useState<"dag" | "fft">("dag");

  return (
    <div className="relative z-20 max-w-6xl mx-auto px-4 sm:px-6 -mt-8 mb-24">
      {/* Ambient glow behind preview */}
      <div className="absolute -inset-1 bg-gradient-to-b from-[#B8F23D]/20 to-transparent rounded-2xl blur-xl -z-10 opacity-70" />

      <div className="rounded-xl border border-[#202A22] bg-[#0D120F] shadow-2xl overflow-hidden font-sans">
        {/* Titlebar */}
        <div className="px-4 py-3 bg-[#070A08] border-b border-[#202A22] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#EF4444]/80 inline-block" />
              <span className="w-2.5 h-2.5 rounded-full bg-[#F59E0B]/80 inline-block" />
              <span className="w-2.5 h-2.5 rounded-full bg-[#22C55E]/80 inline-block" />
            </div>
            <div className="h-4 w-px bg-[#202A22]" />
            <div className="flex items-center gap-2 text-xs font-mono text-[#9BA79D]">
              <span className="text-[#B8F23D] font-bold">SOAR</span>
              <span className="text-[#657066]">/</span>
              <span className="text-[#F1F5ED] truncate max-w-[200px] sm:max-w-none">
                Turbine_Rotor_Batch_04.session
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 font-mono text-[11px]">
            <span className="hidden sm:inline-flex px-2 py-0.5 rounded bg-[#171E18] text-[#9BA79D] border border-[#202A22]">
              Model: Qwen3 1.7B
            </span>
            <span className="px-2 py-0.5 rounded bg-[#B8F23D]/10 text-[#D5FF78] border border-[#B8F23D]/30 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#B8F23D] animate-pulse" />
              LIVE DAG
            </span>
          </div>
        </div>

        {/* Workbench Mockup Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 min-h-[460px]">
          {/* Main Area */}
          <div className="lg:col-span-7 p-5 flex flex-col justify-between border-b lg:border-b-0 lg:border-r border-[#202A22] bg-[#0A0E0C]">
            <div className="space-y-4">
              {/* Task Header */}
              <div className="pb-3 border-b border-[#202A22] flex items-center justify-between">
                <div>
                  <div className="text-xs font-mono uppercase tracking-wider text-[#B8F23D] flex items-center gap-1.5 font-semibold">
                    <Sparkles className="w-3.5 h-3.5" />
                    Autonomous Task Execution
                  </div>
                  <h3 className="text-sm sm:text-base font-semibold text-[#F1F5ED] mt-1">
                    Analyze inspection report & generate defect clearance memo
                  </h3>
                </div>
                <div className="flex gap-1.5">
                  <button
                    onClick={() => setActiveTab("dag")}
                    className={`px-2 py-1 rounded text-xs font-mono transition-colors ${
                      activeTab === "dag"
                        ? "bg-[#171E18] text-[#D5FF78] border border-[#B8F23D]/30"
                        : "text-[#657066] hover:text-[#9BA79D]"
                    }`}
                  >
                    Console
                  </button>
                  <button
                    onClick={() => setActiveTab("fft")}
                    className={`px-2 py-1 rounded text-xs font-mono transition-colors ${
                      activeTab === "fft"
                        ? "bg-[#171E18] text-[#D5FF78] border border-[#B8F23D]/30"
                        : "text-[#657066] hover:text-[#9BA79D]"
                    }`}
                  >
                    Analysis
                  </button>
                </div>
              </div>

              {activeTab === "dag" ? (
                <div className="space-y-3 font-mono text-xs">
                  {/* User Request */}
                  <div className="p-3 rounded-lg bg-[#121812] border border-[#202A22] text-[#F1F5ED]">
                    <div className="text-[10px] text-[#B8F23D] uppercase font-bold mb-1">
                      USER INTENT
                    </div>
                    &quot;Parse <span className="text-[#D5FF78]">./raw_scans/B2-rotor-crack-ultrasonic.pdf</span>, cross-reference ISO 10816-3 vibration limits, and produce a signed engineer approval note.&quot;
                  </div>

                  {/* Execution Log */}
                  <div className="p-3 rounded-lg bg-[#070A08] border border-[#202A22] text-[#9BA79D] space-y-1.5 text-[11px]">
                    <div className="flex items-center gap-2 text-[#657066]">
                      <span>[10:24:01]</span>
                      <span className="text-[#F1F5ED]">Classification: Multimodal Doc & Engineering workflow</span>
                    </div>
                    <div className="flex items-center gap-2 text-[#657066]">
                      <span>[10:24:02]</span>
                      <span className="text-[#F1F5ED]">Selected Model: <span className="text-[#D5FF78]">Qwen3 1.7B</span> via local Ollama</span>
                    </div>
                    <div className="flex items-center gap-2 text-[#657066]">
                      <span>[10:24:03]</span>
                      <span className="text-[#F1F5ED]">Running sandboxed tool: <span className="text-[#A78BFA]">pdf_reader</span></span>
                    </div>
                    <div className="flex items-center gap-2 text-[#F59E0B]">
                      <span>[10:24:05]</span>
                      <span>Variance flagged: Peak 7.82 mm/s RMS exceeds 4.50 mm/s limit</span>
                    </div>
                  </div>

                  {/* Generated Artifact */}
                  <div className="p-3 rounded-lg bg-[#121812] border border-[#22C55E]/40 flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="p-1.5 rounded bg-[#22C55E]/15 text-[#22C55E]">
                        <FileText className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="text-xs font-semibold text-[#F1F5ED]">
                          clearance_memo_04.docx
                        </div>
                        <div className="text-[10px] text-[#657066]">
                          DOCX · 42 KB · Verified Hash SHA256: e3b0c44...
                        </div>
                      </div>
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#22C55E]/15 text-[#4ADE80] border border-[#22C55E]/30">
                      OUTPUT READY
                    </span>
                  </div>
                </div>
              ) : (
                /* FFT Spectrogram Tab */
                <div className="space-y-3 font-mono text-xs">
                  <div className="p-3 rounded-lg bg-[#121812] border border-[#202A22]">
                    <div className="flex justify-between items-center text-[10px] text-[#9BA79D] mb-2">
                      <span>HARMONIC FREQUENCY SPECTRUM</span>
                      <span className="text-[#EF4444] font-bold">PEAK: 284.8 HZ (EXCEEDED)</span>
                    </div>
                    {/* SVG mini chart */}
                    <div className="h-24 w-full">
                      <svg className="w-full h-full" viewBox="0 0 300 70" preserveAspectRatio="none">
                        <line x1="0" y1="30" x2="300" y2="30" stroke="#657066" strokeDasharray="3,3" strokeWidth="1" />
                        <text x="5" y="24" fill="#657066" fontSize="8" fontFamily="monospace">ISO Threshold 4.5 mm/s</text>
                        <rect x="25" y="45" width="12" height="25" fill="#2B382D" rx="1" />
                        <rect x="60" y="38" width="12" height="32" fill="#B8F23D" opacity="0.8" rx="1" />
                        <rect x="95" y="50" width="12" height="20" fill="#2B382D" rx="1" />
                        <rect x="130" y="8" width="14" height="62" fill="#EF4444" rx="1" />
                        <rect x="170" y="35" width="12" height="35" fill="#B8F23D" opacity="0.6" rx="1" />
                        <rect x="205" y="48" width="12" height="22" fill="#2B382D" rx="1" />
                        <rect x="240" y="54" width="12" height="16" fill="#2B382D" rx="1" />
                      </svg>
                    </div>
                    <div className="flex justify-between text-[9px] text-[#657066] border-t border-[#202A22] pt-1">
                      <span>0 Hz</span>
                      <span>Stage 2 Resonance (2X)</span>
                      <span>600 Hz</span>
                    </div>
                  </div>
                  <div className="p-2.5 rounded bg-[#EF4444]/10 border border-[#EF4444]/30 text-[#EF4444] text-[11px] flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 shrink-0" />
                    <span>Immediate borescope tear-down recommended for stage #2 bearing housing.</span>
                  </div>
                </div>
              )}
            </div>

            {/* Prompt Composer Dock */}
            <div className="mt-4 pt-3 border-t border-[#202A22]">
              <div className="flex items-center gap-2 bg-[#070A08] border border-[#202A22] rounded-lg px-3 py-2">
                <Terminal className="w-3.5 h-3.5 text-[#B8F23D] shrink-0" />
                <input
                  type="text"
                  readOnly
                  value="Run vibration tolerance checks and generate mitigation checklist"
                  className="bg-transparent text-xs text-[#F1F5ED] w-full focus:outline-none font-mono"
                />
                <Link
                  href="/app"
                  className="shrink-0 px-2.5 py-1 rounded bg-[#B8F23D] hover:bg-[#D5FF78] text-[#070A08] text-[11px] font-bold font-mono transition flex items-center gap-1"
                >
                  <span>Execute</span>
                  <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
            </div>
          </div>

          {/* Right Area: Run Inspector Showcase */}
          <div className="lg:col-span-5 p-5 bg-[#0D120F] flex flex-col justify-between font-mono text-xs">
            <div>
              <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#202A22]">
                <div className="flex items-center gap-2">
                  <Activity className="w-3.5 h-3.5 text-[#B8F23D]" />
                  <span className="font-bold text-[#F1F5ED] tracking-wider">RUN INSPECTOR</span>
                </div>
                <span className="px-2 py-0.5 rounded-full bg-[#B8F23D]/10 text-[#D5FF78] border border-[#B8F23D]/30 text-[10px]">
                  Stage 4 / 6
                </span>
              </div>

              {/* Execution Steps */}
              <div className="space-y-3.5 pl-2 relative before:absolute before:left-3.5 before:top-2 before:bottom-2 before:w-px before:bg-[#202A22]">
                {/* Step 1 */}
                <div className="flex items-start gap-3 relative">
                  <div className="w-4 h-4 rounded-full bg-[#22C55E]/20 border border-[#22C55E] flex items-center justify-center text-[#22C55E] text-[9px] shrink-0 z-10 bg-[#0D120F]">
                    <Check className="w-2.5 h-2.5" />
                  </div>
                  <div>
                    <div className="text-xs text-[#F1F5ED] font-semibold">1. Task Classification</div>
                    <div className="text-[11px] text-[#657066]">Parsed engineering schema & PDF scan</div>
                  </div>
                </div>

                {/* Step 2 */}
                <div className="flex items-start gap-3 relative">
                  <div className="w-4 h-4 rounded-full bg-[#22C55E]/20 border border-[#22C55E] flex items-center justify-center text-[#22C55E] text-[9px] shrink-0 z-10 bg-[#0D120F]">
                    <Check className="w-2.5 h-2.5" />
                  </div>
                  <div>
                    <div className="text-xs text-[#F1F5ED] font-semibold">2. Model Selection</div>
                    <div className="text-[11px] text-[#657066]">Qwen3 1.7B (Dynamic local routing)</div>
                  </div>
                </div>

                {/* Step 3 */}
                <div className="flex items-start gap-3 relative">
                  <div className="w-4 h-4 rounded-full bg-[#22C55E]/20 border border-[#22C55E] flex items-center justify-center text-[#22C55E] text-[9px] shrink-0 z-10 bg-[#0D120F]">
                    <Check className="w-2.5 h-2.5" />
                  </div>
                  <div>
                    <div className="text-xs text-[#F1F5ED] font-semibold">3. DAG Planning</div>
                    <div className="text-[11px] text-[#657066]">Generated 4-step execution graph</div>
                  </div>
                </div>

                {/* Step 4 (Active) */}
                <div className="flex items-start gap-3 relative bg-[#121812] p-2 rounded border border-[#B8F23D]/30">
                  <div className="w-4 h-4 rounded-full bg-[#B8F23D]/20 border border-[#B8F23D] flex items-center justify-center text-[#B8F23D] text-[9px] shrink-0 z-10 bg-[#0D120F] animate-pulse">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#B8F23D]" />
                  </div>
                  <div>
                    <div className="text-xs text-[#D5FF78] font-bold">4. Tool Execution</div>
                    <div className="text-[11px] text-[#9BA79D]">
                      Active: <code className="text-[#D5FF78]">pdf_reader</code> & <code className="text-[#A78BFA]">calc</code>
                    </div>
                  </div>
                </div>

                {/* Step 5 */}
                <div className="flex items-start gap-3 relative opacity-50">
                  <div className="w-4 h-4 rounded-full bg-[#171E18] border border-[#202A22] flex items-center justify-center text-[#657066] text-[9px] shrink-0 z-10 bg-[#0D120F]">
                    ○
                  </div>
                  <div>
                    <div className="text-xs text-[#657066]">5. Reasoning & Verification</div>
                    <div className="text-[11px] text-[#657066]">Queued</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Illustrative Footer Strip */}
            <div className="mt-4 pt-3 border-t border-[#202A22] flex justify-between items-center text-[10px] text-[#657066]">
              <span>Illustrative preview</span>
              <span className="text-[#B8F23D]">Zero cloud leaks</span>
              <span>100% Local</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
