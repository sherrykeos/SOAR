"use client";

import React from "react";
import { motion } from "framer-motion";

export function HeroBackground() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none -z-10 select-none">
      {/* Subtle fine tech grid */}
      <div className="absolute inset-0 tech-grid opacity-25" />

      {/* Horizon Arc Effect */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1.2, ease: "easeOut" }}
        className="horizon-arc"
      />

      {/* Ambient Top Subtle Glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[350px] bg-[#B8F23D]/5 blur-[120px] rounded-full" />

      {/* Vertical Spatial Light Pillars */}
      <div className="light-pillar-left hidden lg:block">
        <div className="absolute -left-16 top-1/2 -translate-y-1/2 text-[9px] font-mono tracking-widest text-[#657066] uppercase -rotate-90">
          LOCAL · SECURE · SOVEREIGN
        </div>
      </div>

      <div className="light-pillar-right hidden lg:block">
        <div className="absolute -right-20 top-1/2 -translate-y-1/2 text-[9px] font-mono tracking-widest text-[#657066] uppercase rotate-90">
          INTELLIGENCE ON YOUR MACHINE
        </div>
      </div>
    </div>
  );
}
