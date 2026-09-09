"use client";

import React from "react";
import {
  Cpu,
  AlertCircle,
  RotateCw,
  Info,
} from "lucide-react";
import { useWorkbench } from "@/context/WorkbenchContext";
import { useToast } from "@/components/ui/Toast";

export function ModelsPage() {
  const {
    models,
    defaultModel,
    selectedModel,
    setSelectedModel,
    isLoadingModels,
    refreshModels,
  } = useWorkbench();

  const { success } = useToast();

  const handleSelectModel = (modelId: string) => {
    setSelectedModel(modelId);
    success("Active Model Updated", `Default orchestrator will use ${modelId}`);
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-6xl mx-auto w-full font-sans">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#202A22]">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-[#F1F5ED]">
            Model Pool
          </h1>
          <p className="text-xs text-[#9BA79D] mt-1">
            Locally hosted open-weight LLMs managed via Ollama inference server. Dynamic routing routes tasks to the best suited model.
          </p>
        </div>

        <button
          onClick={refreshModels}
          disabled={isLoadingModels}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-[#121812] border border-[#202A22] hover:border-[#B8F23D]/40 text-xs font-mono text-[#F1F5ED] hover:text-[#D5FF78] transition shadow-sm self-start sm:self-auto"
        >
          <RotateCw
            className={`w-3.5 h-3.5 ${isLoadingModels ? "animate-spin text-[#B8F23D]" : ""}`}
          />
          <span>Refresh Pool</span>
        </button>
      </div>

      {/* Notice */}
      <div className="p-3.5 rounded-lg bg-[#0D120F] border border-[#202A22] text-xs font-mono text-[#9BA79D] flex items-center gap-3">
        <Info className="w-4 h-4 text-[#B8F23D] shrink-0" />
        <span>
          Models reflect live backend configuration from <code>config.yaml</code>. Model management actions (download/delete) are performed on the host machine.
        </span>
      </div>

      {/* Models Grid */}
      {isLoadingModels ? (
        <div className="p-12 text-center text-[#657066] font-mono text-xs space-y-2">
          <RotateCw className="w-6 h-6 mx-auto animate-spin text-[#B8F23D]" />
          <div>Querying local inference server at /api/models...</div>
        </div>
      ) : models.length === 0 ? (
        <div className="p-8 rounded-xl bg-[#0D120F] border border-[#202A22] text-center font-mono text-xs text-[#657066] space-y-2">
          <AlertCircle className="w-6 h-6 mx-auto text-[#EF4444]" />
          <div className="text-[#F1F5ED] font-semibold">No models detected</div>
          <p>Make sure your local Ollama daemon is running and models are registered in config.yaml.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {models.map((m) => {
            const isDefault = m.id === defaultModel;
            const isSelected = selectedModel === m.id;

            return (
              <div
                key={m.id}
                className={`p-5 rounded-xl border transition-all duration-200 flex flex-col justify-between ${
                  isSelected
                    ? "bg-[#121812] border-[#B8F23D]/50 shadow-[0_0_20px_-4px_rgba(184,242,61,0.2)]"
                    : "bg-[#0D120F] border-[#202A22] hover:border-[#2B382D]"
                }`}
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <div className="flex items-center gap-2">
                      <Cpu className="w-4 h-4 text-[#B8F23D]" />
                      <span className="font-mono text-sm font-bold text-[#F1F5ED]">
                        {m.id}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 font-mono text-[10px]">
                      {isDefault && (
                        <span className="px-2 py-0.5 rounded bg-[#B8F23D]/15 text-[#D5FF78] border border-[#B8F23D]/30 uppercase font-bold">
                          Default
                        </span>
                      )}
                      <span
                        className={`px-2 py-0.5 rounded border uppercase flex items-center gap-1 ${
                          m.available
                            ? "bg-[#22C55E]/10 text-[#4ADE80] border-[#22C55E]/30"
                            : "bg-[#657066]/10 text-[#9BA79D] border-[#202A22]"
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            m.available ? "bg-[#22C55E]" : "bg-[#657066]"
                          }`}
                        />
                        {m.available ? "Available" : "Offline"}
                      </span>
                    </div>
                  </div>

                  <div className="space-y-2 font-mono text-xs">
                    <div className="flex items-center gap-2 text-[#657066]">
                      <span>Provider:</span>
                      <span className="text-[#9BA79D] uppercase">{m.provider}</span>
                    </div>

                    <div className="flex items-center gap-2 text-[#657066]">
                      <span>Priority:</span>
                      <span className="text-[#9BA79D]">{m.priority}</span>
                      {m.timeout && (
                        <>
                          <span>·</span>
                          <span>Timeout: {m.timeout}s</span>
                        </>
                      )}
                    </div>

                    <div className="pt-2">
                      <div className="text-[10px] uppercase text-[#657066] mb-1">
                        Capabilities:
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {m.capabilities.map((cap) => (
                          <span
                            key={cap}
                            className="px-2 py-0.5 rounded bg-[#171E18] text-[#F1F5ED] text-[10px] border border-[#202A22]"
                          >
                            {cap}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="pt-4 mt-4 border-t border-[#202A22] flex items-center justify-between">
                  <span className="text-[11px] font-mono text-[#657066]">
                    {!m.available
                      ? "Model currently offline"
                      : isSelected
                      ? "Currently selected"
                      : "Click to select"}
                  </span>
                  <button
                    onClick={() => handleSelectModel(m.id)}
                    disabled={isSelected || !m.available}
                    className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition ${
                      !m.available
                        ? "bg-[#121812] text-[#657066] border border-[#202A22] cursor-not-allowed opacity-60"
                        : isSelected
                        ? "bg-[#B8F23D]/20 text-[#D5FF78] border border-[#B8F23D]/40 cursor-default"
                        : "bg-[#171E18] text-[#F1F5ED] hover:bg-[#B8F23D] hover:text-[#070A08] border border-[#202A22]"
                    }`}
                  >
                    {!m.available ? "Unavailable" : isSelected ? "Active" : "Use Model"}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default ModelsPage;
