"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArrowRight, Menu, X, ShieldCheck } from "lucide-react";
import { Logo } from "@/components/ui/Logo";
import { motion, AnimatePresence } from "framer-motion";

export function LandingNavbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-[#202A22]/80 bg-[#070A08]/85 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <Logo href="/" />

        {/* Desktop Nav Links */}
        <nav className="hidden md:flex items-center gap-8 text-xs font-medium text-[#9BA79D]">
          <Link
            href="#capabilities"
            className="hover:text-[#D5FF78] transition-colors"
          >
            Capabilities
          </Link>
          <Link
            href="#workflow"
            className="hover:text-[#D5FF78] transition-colors"
          >
            Workflow
          </Link>
          <Link
            href="#architecture"
            className="hover:text-[#D5FF78] transition-colors"
          >
            Architecture
          </Link>
          <Link
            href="#inspector"
            className="hover:text-[#D5FF78] transition-colors"
          >
            Inspector
          </Link>
        </nav>

        {/* Right Action Items */}
        <div className="hidden sm:flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-[#0D120F] border border-[#202A22] text-[11px] font-mono text-[#9BA79D]">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#B8F23D] opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#B8F23D]" />
            </span>
            <span className="text-[#F1F5ED] font-medium">LOCAL MODE</span>
            <span className="text-[#657066]">·</span>
            <span className="text-[10px] text-[#657066]">No external network</span>
          </div>

          <Link
            href="/app"
            className="group inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#B8F23D] text-[#070A08] font-semibold text-xs transition-all duration-200 hover:bg-[#D5FF78] shadow-[0_0_20px_-4px_rgba(184,242,61,0.4)]"
          >
            <span>Open Workbench</span>
            <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-0.5" />
          </Link>
        </div>

        {/* Mobile Hamburger */}
        <div className="flex sm:hidden items-center gap-2">
          <Link
            href="/app"
            className="inline-flex items-center px-3 py-1.5 rounded-lg bg-[#B8F23D] text-[#070A08] font-semibold text-xs"
          >
            Open
          </Link>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-1.5 rounded text-[#9BA79D] hover:text-[#F1F5ED] hover:bg-[#121812]"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="sm:hidden border-b border-[#202A22] bg-[#070A08]/95 px-6 py-4 flex flex-col gap-4 text-sm"
          >
            <Link
              href="#capabilities"
              onClick={() => setMobileMenuOpen(false)}
              className="text-[#9BA79D] hover:text-[#D5FF78]"
            >
              Capabilities
            </Link>
            <Link
              href="#workflow"
              onClick={() => setMobileMenuOpen(false)}
              className="text-[#9BA79D] hover:text-[#D5FF78]"
            >
              Workflow
            </Link>
            <Link
              href="#architecture"
              onClick={() => setMobileMenuOpen(false)}
              className="text-[#9BA79D] hover:text-[#D5FF78]"
            >
              Architecture
            </Link>
            <Link
              href="#inspector"
              onClick={() => setMobileMenuOpen(false)}
              className="text-[#9BA79D] hover:text-[#D5FF78]"
            >
              Inspector
            </Link>
            <div className="pt-2 border-t border-[#202A22] flex items-center justify-between text-xs font-mono text-[#9BA79D]">
              <span className="flex items-center gap-1.5 text-[#B8F23D]">
                <ShieldCheck className="w-3.5 h-3.5" />
                Local-First · Offline
              </span>
              <Link
                href="/app"
                onClick={() => setMobileMenuOpen(false)}
                className="font-bold text-[#B8F23D]"
              >
                Launch Workbench →
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
