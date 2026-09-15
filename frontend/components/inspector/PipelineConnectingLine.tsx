"use client";

import React from "react";
import { motion } from "framer-motion";

export interface PipelineConnectingLineProps {
  status: "completed" | "running" | "pending" | "failed";
  className?: string;
}

export function PipelineConnectingLine({
  status,
  className = "",
}: PipelineConnectingLineProps) {
  const isCompleted = status === "completed";
  const isRunning = status === "running";
  const isFailed = status === "failed";

  return (
    <div className={`relative flex justify-center w-5 h-6 sm:h-7 ${className}`}>
      {/* Background Track Rail */}
      <div className="absolute inset-y-0 w-[2px] bg-[#202A22] rounded-full" />

      {/* Completed Fill Line */}
      {isCompleted && (
        <motion.div
          initial={{ scaleY: 0 }}
          animate={{ scaleY: 1 }}
          transition={{ duration: 0.3, ease: "easeOut" }}
          style={{ originY: 0 }}
          className="absolute inset-y-0 w-[2px] bg-[#B8F23D] rounded-full shadow-[0_0_6px_rgba(184,242,61,0.4)]"
        />
      )}

      {/* Failed Line */}
      {isFailed && (
        <div className="absolute inset-y-0 w-[2px] bg-[#EF4444] rounded-full shadow-[0_0_6px_rgba(239,68,68,0.4)]" />
      )}

      {/* Active Running Line (Subtle Pulse) */}
      {isRunning && (
        <motion.div
          initial={{ scaleY: 0 }}
          animate={{ scaleY: [0.3, 0.8, 1, 0.5, 0.9] }}
          transition={{
            duration: 1.8,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          style={{ originY: 0 }}
          className="absolute inset-y-0 w-[2px] bg-gradient-to-b from-[#B8F23D] to-[#D5FF78] rounded-full shadow-[0_0_8px_rgba(184,242,61,0.35)]"
        />
      )}
    </div>
  );
}
