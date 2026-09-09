"use client";

import React, { useEffect } from "react";
import { AlertCircle, RotateCw } from "lucide-react";

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log error internally if needed
  }, [error]);

  return (
    <div className="min-h-screen bg-[#070A08] text-[#F1F5ED] flex flex-col items-center justify-center p-6 text-center font-mono">
      <div className="w-12 h-12 rounded-xl bg-[#EF4444]/15 border border-[#EF4444]/30 flex items-center justify-center text-[#EF4444] mb-4">
        <AlertCircle className="w-6 h-6" />
      </div>
      <span className="text-xs text-[#EF4444] uppercase tracking-widest font-bold">
        APPLICATION ERROR
      </span>
      <h1 className="text-xl sm:text-2xl font-bold mt-2 mb-3">
        Workbench Caught an Exception
      </h1>
      <p className="text-xs text-[#9BA79D] max-w-sm mb-6 leading-relaxed">
        {error.message || "An unexpected error occurred in the workbench layout."}
      </p>
      <button
        onClick={() => reset()}
        className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#121812] border border-[#202A22] hover:border-[#B8F23D]/50 text-[#F1F5ED] hover:text-[#D5FF78] font-bold text-xs transition cursor-pointer"
      >
        <RotateCw className="w-3.5 h-3.5" />
        <span>Reload Workbench View</span>
      </button>
    </div>
  );
}
