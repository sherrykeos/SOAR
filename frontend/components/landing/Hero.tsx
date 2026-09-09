"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArrowRight, Play, Cpu } from "lucide-react";
import { motion } from "framer-motion";
import { HeroBackground } from "./HeroBackground";
import { HeroProductPreview } from "./HeroProductPreview";
import { Modal } from "@/components/ui/Modal";

export function Hero() {
  const [demoOpen, setDemoOpen] = useState(false);

  return (
    <section className="relative min-h-[92vh] flex flex-col items-center justify-between pt-16 overflow-hidden">
      <HeroBackground />

      <div className="relative z-10 max-w-4xl mx-auto px-6 text-center mt-6">
        {/* Technical Badge */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#0D120F]/90 border border-[#B8F23D]/30 text-xs font-mono tracking-widest uppercase mb-8 shadow-sm"
        >
          <span className="h-1.5 w-1.5 rounded-full bg-[#B8F23D] animate-pulse" />
          <span className="text-[#D5FF78] font-semibold">PRIVATE</span>
          <span className="text-[#657066]">•</span>
          <span className="text-[#F1F5ED]">LOCAL</span>
          <span className="text-[#657066]">•</span>
          <span className="text-[#9BA79D]">ON YOUR TERMS</span>
        </motion.div>

        {/* Main Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white leading-[1.08] mb-6"
        >
          Turn Complex Work <br className="hidden sm:inline" />
          into{" "}
          <span className="bg-gradient-to-r from-[#D5FF78] via-[#B8F23D] to-[#DFFF9A] bg-clip-text text-transparent drop-shadow-[0_0_25px_rgba(184,242,61,0.45)]">
            Real Results.
          </span>
        </motion.h1>

        {/* Supporting Pitch */}
        <motion.p
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="max-w-2xl mx-auto text-base sm:text-lg text-[#9BA79D] font-light leading-relaxed mb-10"
        >
          A sovereign AI workbench that understands your intent, plans the steps,
          uses the right tools and delivers actual results — on your machine.
        </motion.p>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-14"
        >
          <Link
            href="/app"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-8 py-3.5 rounded-lg bg-[#B8F23D] text-[#070A08] font-bold text-sm hover:bg-[#D5FF78] hover:shadow-[0_0_35px_rgba(184,242,61,0.45)] transition-all duration-300"
          >
            <span>Open Workbench</span>
            <ArrowRight className="w-4 h-4" />
          </Link>

          <button
            onClick={() => setDemoOpen(true)}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-lg bg-[#0D120F] border border-[#202A22] text-[#F1F5ED] hover:text-white hover:border-[#B8F23D]/40 font-medium text-sm transition-all duration-300"
          >
            <Play className="w-4 h-4 text-[#B8F23D] fill-current" />
            <span>Watch Demo</span>
            <span className="text-xs text-[#657066] font-mono">1:45</span>
          </button>
        </motion.div>

        {/* Local Security Claim */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="text-[11px] font-mono tracking-widest text-[#657066] uppercase mb-6"
        >
          SOVEREIGN LOCAL EXECUTION · ZERO EXTERNAL DATA EXPOSURE
        </motion.div>
      </div>

      {/* Product Preview */}
      <HeroProductPreview />

      {/* Demo Modal */}
      <Modal
        isOpen={demoOpen}
        onClose={() => setDemoOpen(false)}
        title="SOAR — Sovereign AI Overview"
        description="Experience the end-to-end local execution pipeline."
        maxWidth="lg"
      >
        <div className="space-y-4 text-xs text-[#9BA79D]">
          <div className="aspect-video bg-[#070A08] rounded-lg border border-[#202A22] flex flex-col items-center justify-center p-6 text-center">
            <Cpu className="w-10 h-10 text-[#B8F23D] mb-3 animate-pulse" />
            <h4 className="text-sm font-semibold text-[#F1F5ED] mb-1">
              Local-First Sovereign AI in Action
            </h4>
            <p className="max-w-md text-[#9BA79D] mb-4">
              Watch how SOAR reads scanned NDT reports, plans tool invocations, executes
              Python code sandboxes, and delivers verified Word & PDF memos on your metal.
            </p>
            <Link
              href="/app"
              onClick={() => setDemoOpen(false)}
              className="px-4 py-2 rounded bg-[#B8F23D] text-[#070A08] font-bold text-xs hover:bg-[#D5FF78] transition"
            >
              Launch Live Workbench →
            </Link>
          </div>
          <div className="flex items-center justify-between text-[11px] font-mono text-[#657066]">
            <span>Local daemon active</span>
            <span className="text-[#22C55E]">No external telemetry</span>
          </div>
        </div>
      </Modal>
    </section>
  );
}
