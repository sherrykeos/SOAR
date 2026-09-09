"use client";

import React, { useState } from "react";
import {
  Database,
  Search,
  Info,
} from "lucide-react";

export default function KnowledgePage() {
  const [searchQuery, setSearchQuery] = useState("");

  const collections = [
    {
      name: "soar_knowledge",
      description: "Default primary organizational knowledge base and standard operating procedures.",
      backend: "ChromaDB (Local)",
      embeddingModel: "BAAI/bge-m3 (1024-dim)",
      path: "./data/chroma",
      status: "Configured Locally",
      topK: 5,
    },
    {
      name: "iso_industrial_standards",
      description: "Vibration tolerances, structural fatigue criteria (ISO 10816-3, Class II).",
      backend: "ChromaDB (Local)",
      embeddingModel: "BAAI/bge-m3 (1024-dim)",
      path: "./data/chroma",
      status: "Reference Vault",
      topK: 5,
    },
  ];

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-6xl mx-auto w-full font-sans">
      {/* Header */}
      <div className="pb-4 border-b border-[#202A22]">
        <h1 className="text-xl sm:text-2xl font-bold text-[#F1F5ED]">
          Knowledge Base
        </h1>
        <p className="text-xs text-[#9BA79D] mt-1">
          Local vector embeddings and semantic search over organizational manuals and procedures.
        </p>
      </div>

      {/* Backend API Contract Notice */}
      <div className="p-3.5 rounded-lg bg-[#0D120F] border border-[#202A22] text-xs font-mono text-[#9BA79D] flex items-start gap-3">
        <Info className="w-4 h-4 text-[#B8F23D] shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="text-[#F1F5ED] font-semibold">
            Local-First Retrieval Architecture (Read-Only Mode)
          </div>
          <p className="leading-relaxed">
            Dynamic collection management REST APIs are scheduled for a future backend release. Currently, documents are embedded via offline backend batch ingestion into ChromaDB using BGE-M3.
          </p>
        </div>
      </div>

      {/* Search Input Simulation */}
      <div className="p-4 rounded-xl bg-[#0D120F] border border-[#202A22] space-y-3 font-mono text-xs">
        <div className="text-[10px] uppercase font-bold text-[#657066]">
          SEMANTIC SIMILARITY SEARCH
        </div>
        <div className="relative">
          <Search className="w-4 h-4 text-[#657066] absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search your local knowledge base (e.g. 'ISO 10816-3 vibration limits')..."
            className="w-full bg-[#070A08] border border-[#202A22] rounded-lg pl-10 pr-4 py-2.5 text-xs text-[#F1F5ED] placeholder:text-[#657066] focus:outline-none focus:border-[#B8F23D]/50"
          />
        </div>
        <div className="flex items-center justify-between text-[11px] text-[#657066]">
          <span>Vector Similarity: Cosine metric</span>
          <span className="text-[#D5FF78]">Active collection: soar_knowledge</span>
        </div>
      </div>

      {/* Collections Grid */}
      <div className="space-y-3">
        <div className="text-[11px] font-mono uppercase tracking-wider text-[#657066] font-semibold">
          Active Local Collections
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
          {collections.map((col) => (
            <div
              key={col.name}
              className="p-5 rounded-xl bg-[#0D120F] border border-[#202A22] flex flex-col justify-between space-y-4"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <Database className="w-4 h-4 text-[#B8F23D]" />
                    <span className="font-bold text-sm text-[#F1F5ED]">
                      {col.name}
                    </span>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-[#22C55E]/10 text-[#4ADE80] border border-[#22C55E]/30 text-[10px] uppercase font-bold">
                    {col.status}
                  </span>
                </div>

                <p className="text-xs text-[#9BA79D] font-sans leading-relaxed">
                  {col.description}
                </p>
              </div>

              <div className="pt-3 border-t border-[#202A22] space-y-1.5 text-[11px] text-[#657066]">
                <div className="flex justify-between">
                  <span>Engine:</span>
                  <span className="text-[#9BA79D]">{col.backend}</span>
                </div>
                <div className="flex justify-between">
                  <span>Embeddings:</span>
                  <span className="text-[#9BA79D]">{col.embeddingModel}</span>
                </div>
                <div className="flex justify-between">
                  <span>Storage Path:</span>
                  <span className="text-[#9BA79D]">{col.path}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
