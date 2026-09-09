"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArrowRight, Copy, Check } from "lucide-react";

export function FinalCTA() {
  const [copied, setCopied] = useState(false);

  const copyCommand = () => {
    navigator.clipboard.writeText("curl -fsSL https://soar.sh/install | bash");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section className="py-28 border-b border-[#202A22]/60 bg-[#040605] relative text-center overflow-hidden">
      {/* Ambient bottom glow */}
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-3/4 h-72 bg-[#B8F23D]/10 blur-[130px] pointer-events-none" />

      <div className="max-w-4xl mx-auto px-6 relative z-10">
        <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-[#0D120F] border border-[#B8F23D]/30 text-xs font-mono text-[#D5FF78] mb-6">
          <span>THE SOVEREIGN WORKBENCH</span>
        </div>

        <h2 className="text-4xl sm:text-6xl font-extrabold text-white tracking-tight mb-6 leading-tight">
          Give it something <br />
          <span className="text-[#D5FF78]">worth doing.</span>
        </h2>

        <p className="text-[#9BA79D] text-base sm:text-lg max-w-xl mx-auto mb-10 font-light leading-relaxed">
          Experience the power of local, sovereign AI. Run deep cognitive tasks,
          document synthesis, and sandboxed code on your own hardware.
        </p>

        {/* Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-10">
          <Link
            href="/app"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-8 py-3.5 rounded-lg bg-[#B8F23D] text-[#070A08] font-bold text-sm hover:bg-[#D5FF78] hover:shadow-[0_0_30px_rgba(184,242,61,0.45)] transition-all duration-300"
          >
            <span>Open Workbench</span>
            <ArrowRight className="w-4 h-4" />
          </Link>

          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-lg bg-[#0D120F] border border-[#202A22] text-[#F1F5ED] hover:text-white hover:border-[#B8F23D]/40 font-mono text-xs transition-all duration-300"
          >
            <svg className="w-4 h-4 text-[#9BA79D]" fill="currentColor" viewBox="0 0 24 24">
              <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
            </svg>
            <span>View on GitHub</span>
          </a>
        </div>

        {/* Shell install copy hint */}
        <div className="inline-flex items-center gap-3 px-4 py-2 rounded-lg bg-[#0D120F] border border-[#202A22] text-xs font-mono text-[#9BA79D]">
          <span className="text-[#B8F23D] font-bold">$</span>
          <span>curl -fsSL https://soar.sh/install | bash</span>
          <button
            onClick={copyCommand}
            className="text-[#657066] hover:text-[#F1F5ED] transition p-1"
            title="Copy command"
          >
            {copied ? (
              <Check className="w-3.5 h-3.5 text-[#22C55E]" />
            ) : (
              <Copy className="w-3.5 h-3.5" />
            )}
          </button>
        </div>
      </div>
    </section>
  );
}
