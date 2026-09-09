import React from "react";
import { CheckCircle2, FileCode2 } from "lucide-react";

export function BuildShowcase() {
  return (
    <section className="py-24 border-b border-[#202A22]/60 bg-[#070A08] relative">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <span className="text-xs font-mono uppercase tracking-widest text-[#B8F23D] font-semibold">
            DEVELOPMENT & CODING ENGINE
          </span>
          <h2 className="text-3xl sm:text-5xl font-extrabold text-white mt-3 mb-4 tracking-tight">
            Build something.
          </h2>
          <p className="text-[#9BA79D] text-sm sm:text-base leading-relaxed">
            Give SOAR real software tasks. From writing endpoints and data pipelines to running automated unit tests inside an isolated local sandbox.
          </p>
        </div>

        {/* Code Editor Style Showcase */}
        <div className="max-w-4xl mx-auto rounded-xl bg-[#0D120F] border border-[#202A22] shadow-2xl overflow-hidden font-mono text-xs">
          {/* Header Bar */}
          <div className="px-4 py-3 bg-[#070A08] border-b border-[#202A22] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileCode2 className="w-4 h-4 text-[#B8F23D]" />
              <span className="text-[#F1F5ED] font-semibold">process_inspection.py</span>
              <span className="text-[#657066]">·</span>
              <span className="text-[10px] text-[#22C55E]">Test Suite Passed (3/3)</span>
            </div>
            <span className="px-2 py-0.5 rounded bg-[#171E18] text-[#9BA79D] text-[10px] border border-[#202A22]">
              Qwen2.5-Coder 1.5B
            </span>
          </div>

          {/* Workflow Stepper Bar */}
          <div className="px-4 py-2 bg-[#121812] border-b border-[#202A22] flex flex-wrap items-center gap-3 text-[11px] text-[#657066]">
            <span className="text-[#22C55E] flex items-center gap-1">
              ✓ Understand
            </span>
            <span>→</span>
            <span className="text-[#22C55E] flex items-center gap-1">
              ✓ Inspect
            </span>
            <span>→</span>
            <span className="text-[#22C55E] flex items-center gap-1">
              ✓ Plan
            </span>
            <span>→</span>
            <span className="text-[#22C55E] flex items-center gap-1">
              ✓ Write
            </span>
            <span>→</span>
            <span className="text-[#B8F23D] font-bold flex items-center gap-1">
              ◉ Test
            </span>
            <span>→</span>
            <span>Deliver</span>
          </div>

          {/* Code Window */}
          <div className="p-6 bg-[#040605] text-[#F1F5ED] leading-relaxed overflow-x-auto">
            <pre className="text-xs">
              <code>
                <span className="text-[#657066]"># Request: &quot;Build a REST endpoint that processes uploaded inspection reports&quot;</span>{"\n"}
                <span className="text-[#A78BFA]">from</span> fastapi <span className="text-[#A78BFA]">import</span> APIRouter, UploadFile, HTTPException{"\n"}
                <span className="text-[#A78BFA]">from</span> pydantic <span className="text-[#A78BFA]">import</span> BaseModel{"\n"}
                {"\n"}
                router = APIRouter(prefix=<span className="text-[#D5FF78]">&quot;/inspections&quot;</span>){"\n"}
                {"\n"}
                <span className="text-[#B8F23D]">@router.post</span>(<span className="text-[#D5FF78]">&quot;/process&quot;</span>){"\n"}
                <span className="text-[#A78BFA]">async def</span> <span className="text-[#60A5FA]">process_report</span>(file: UploadFile):{"\n"}
                {"    "}data = <span className="text-[#A78BFA]">await</span> file.read(){"\n"}
                {"    "}spec = parse_spectrogram(data){"\n"}
                {"    "}<span className="text-[#A78BFA]">if</span> spec.peak_rms &gt; <span className="text-[#F59E0B]">4.50</span>:{"\n"}
                {"        "}<span className="text-[#A78BFA]">return</span> {"{"}<span className="text-[#D5FF78]">&quot;status&quot;</span>: <span className="text-[#EF4444]">&quot;exceeded&quot;</span>, <span className="text-[#D5FF78]">&quot;delta&quot;</span>: spec.peak_rms - 4.50{"}"}{"\n"}
                {"    "}<span className="text-[#A78BFA]">return</span> {"{"}<span className="text-[#D5FF78]">&quot;status&quot;</span>: <span className="text-[#22C55E]">&quot;nominal&quot;</span>{"}"}
              </code>
            </pre>
          </div>

          {/* Sandbox Test Execution Bar */}
          <div className="p-3 bg-[#070A08] border-t border-[#202A22] flex items-center justify-between text-[11px]">
            <div className="flex items-center gap-2 text-[#22C55E]">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Sandbox pytest: 3 tests passed in 0.42s (0 failures, isolated memory)</span>
            </div>
            <span className="text-[#657066]">Sandbox Exit Code: 0</span>
          </div>
        </div>
      </div>
    </section>
  );
}
