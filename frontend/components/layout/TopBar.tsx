"use client";

import React from "react";
import { usePathname, useRouter } from "next/navigation";
import {
  Menu,
  Search,
  Cpu,
  Settings as SettingsIcon,
  PanelLeft,
  PanelRight,
  Plus,
} from "lucide-react";
import { useWorkbench } from "@/context/WorkbenchContext";

export function TopBar() {
  const pathname = usePathname();
  const router = useRouter();
  const {
    selectedModel,
    defaultModel,
    setCommandPaletteOpen,
    mobileSidebarOpen,
    setMobileSidebarOpen,
    sidebarCollapsed,
    setSidebarCollapsed,
    inspectorOpen,
    setInspectorOpen,
    setActiveRunId,
  } = useWorkbench();

  // Route labels
  const getSectionTitle = () => {
    if (pathname === "/app") return "Chat & Workspace";
    if (pathname.startsWith("/app/tasks")) return "Task History";
    if (pathname.startsWith("/app/files")) return "Managed Files";
    if (pathname.startsWith("/app/knowledge")) return "Knowledge Base";
    if (pathname.startsWith("/app/models")) return "Model Pool";
    if (pathname.startsWith("/app/tools")) return "Tool Registry";
    if (pathname.startsWith("/app/settings")) return "Settings";
    return "Workbench";
  };

  const handleNewChat = () => {
    setActiveRunId(null);
    if (pathname !== "/app") router.push("/app");
  };

  return (
    <header className="h-14 border-b border-[#202A22] bg-[#070A08]/90 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between select-none shrink-0 sticky top-0 z-30 font-sans">
      {/* Left: Toggles & Breadcrumb */}
      <div className="flex items-center gap-3">
        {/* Mobile Toggle */}
        <button
          onClick={() => setMobileSidebarOpen(!mobileSidebarOpen)}
          className="md:hidden p-1.5 rounded-lg text-[#9BA79D] hover:text-[#F1F5ED] hover:bg-[#121812]"
          aria-label="Toggle navigation"
        >
          <Menu className="w-4 h-4" />
        </button>

        {/* Desktop Sidebar Expand Toggle (visible when collapsed) */}
        {sidebarCollapsed && (
          <button
            onClick={() => setSidebarCollapsed(false)}
            className="hidden md:flex p-1.5 rounded-lg text-[#9BA79D] hover:text-[#D5FF78] hover:bg-[#121812] transition-colors"
            title="Expand left sidebar"
          >
            <PanelLeft className="w-4 h-4 text-[#B8F23D]" />
          </button>
        )}

        {/* Desktop Quick New Chat (visible when sidebar collapsed) */}
        {sidebarCollapsed && (
          <button
            onClick={handleNewChat}
            className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#121812] border border-[#B8F23D]/30 text-xs text-[#F1F5ED] hover:border-[#B8F23D] hover:text-[#D5FF78] transition-all"
            title="New Chat (⌘N)"
          >
            <Plus className="w-3.5 h-3.5 text-[#B8F23D]" />
            <span className="text-[11px] font-medium">New Chat</span>
          </button>
        )}

        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="text-[#657066]">soar</span>
          <span className="text-[#657066]">/</span>
          <span className="font-semibold text-[#F1F5ED]">{getSectionTitle()}</span>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-2.5 font-mono text-xs">
        {/* Air-gap indicator */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#0D120F] border border-[#202A22] text-[11px]">
          <span className="w-1.5 h-1.5 rounded-full bg-[#B8F23D] animate-pulse" />
          <span className="text-[#F1F5ED] font-medium">LOCAL MODE</span>
        </div>

        {/* Current Model */}
        <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#121812] border border-[#202A22] text-[11px] text-[#9BA79D]">
          <Cpu className="w-3.5 h-3.5 text-[#B8F23D]" />
          <span>Model:</span>
          <span
            suppressHydrationWarning
            className="text-[#D5FF78] font-semibold truncate max-w-[140px]"
          >
            {selectedModel === "auto" ? `Auto (${defaultModel})` : selectedModel}
          </span>
        </div>

        {/* Command Palette Trigger */}
        <button
          onClick={() => setCommandPaletteOpen(true)}
          className="flex items-center gap-2 px-3 py-1 rounded-lg bg-[#121812] border border-[#202A22] hover:border-[#B8F23D]/40 text-[#9BA79D] hover:text-[#F1F5ED] transition-colors cursor-pointer"
        >
          <Search className="w-3.5 h-3.5 text-[#657066]" />
          <span className="hidden md:inline text-[11px]">Search</span>
          <kbd className="text-[10px] bg-[#070A08] border border-[#202A22] px-1.5 py-0.5 rounded text-[#657066]">
            ⌘K
          </kbd>
        </button>

        {/* Collapsible Run Inspector Toggle */}
        <button
          onClick={() => setInspectorOpen((prev) => !prev)}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border transition-all cursor-pointer ${
            inspectorOpen
              ? "bg-[#171E18] text-[#D5FF78] border-[#B8F23D]/40"
              : "bg-[#0D120F] text-[#657066] border-[#202A22] hover:text-[#F1F5ED] hover:border-[#2B382D]"
          }`}
          title={inspectorOpen ? "Hide Run Inspector" : "Show Run Inspector"}
        >
          <PanelRight className={`w-3.5 h-3.5 ${inspectorOpen ? "text-[#B8F23D]" : "text-[#657066]"}`} />
          <span className="hidden xl:inline text-[11px] font-medium">Inspector</span>
        </button>

        {/* Quick Settings Action */}
        <button
          onClick={() => router.push("/app/settings")}
          className="p-1.5 rounded-lg text-[#657066] hover:text-[#F1F5ED] hover:bg-[#121812] transition-colors"
          title="Settings"
        >
          <SettingsIcon className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}
