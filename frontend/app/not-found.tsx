import React from "react";
import Link from "next/link";
import { ArrowLeft, Terminal } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#070A08] text-[#F1F5ED] flex flex-col items-center justify-center p-6 text-center font-mono">
      <div className="w-12 h-12 rounded-xl bg-[#121812] border border-[#202A22] flex items-center justify-center text-[#B8F23D] mb-4">
        <Terminal className="w-6 h-6" />
      </div>
      <span className="text-xs text-[#B8F23D] uppercase tracking-widest font-bold">
        HTTP 404
      </span>
      <h1 className="text-xl sm:text-2xl font-bold mt-2 mb-3">
        Endpoint or View Not Found
      </h1>
      <p className="text-xs text-[#9BA79D] max-w-sm mb-6 leading-relaxed">
        The requested resource does not exist within the local SOAR workbench navigation graph.
      </p>
      <Link
        href="/app"
        className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#B8F23D] text-[#070A08] font-bold text-xs hover:bg-[#D5FF78] transition"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        <span>Return to Workbench</span>
      </Link>
    </div>
  );
}
