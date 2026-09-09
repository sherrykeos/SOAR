"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  ListTodo,
  FolderOpen,
  Database,
  Cpu,
  Wrench,
  Settings,
  Plus,
  ShieldCheck,
  RefreshCw,
} from "lucide-react";
import { Logo } from "@/components/ui/Logo";
import { useWorkbench } from "@/context/WorkbenchContext";

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const {
    sessionTasks,
    models,
    isBackendOnline,
    health,
    checkHealth,
    setActiveRunId,
  } = useWorkbench();

  const navItems = [
    { name: "Home", href: "/app", icon: LayoutDashboard, exact: true },
    {
      name: "Tasks",
      href: "/app/tasks",
      icon: ListTodo,
      badge: sessionTasks.length > 0 ? `${sessionTasks.length}` : undefined,
    },
    { name: "Files", href: "/app/files", icon: FolderOpen },
    { name: "Knowledge", href: "/app/knowledge", icon: Database },
    {
      name: "Models",
      href: "/app/models",
      icon: Cpu,
      badge: models.length > 0 ? `${models.length}` : undefined,
    },
    { name: "Tools", href: "/app/tools", icon: Wrench },
    { name: "Settings", href: "/app/settings", icon: Settings },
  ];

  const handleNewTask = () => {
    setActiveRunId(null);
    router.push("/app");
  };

  return (
    <aside className="w-64 bg-[#070A08] border-r border-[#202A22] flex flex-col justify-between p-3 select-none shrink-0 h-screen sticky top-0 font-sans">
      <div className="flex flex-col gap-4">
        {/* Logo */}
        <div className="px-2 pt-1 pb-2 border-b border-[#202A22]/50">
          <Logo href="/" />
        </div>

        {/* New Task Button */}
        <button
          onClick={handleNewTask}
          className="w-full flex items-center justify-between px-3 py-2 bg-[#121812] border border-[#B8F23D]/30 text-[#F1F5ED] rounded-lg hover:border-[#B8F23D] hover:bg-[#171E18] transition-all group cursor-pointer shadow-sm"
        >
          <div className="flex items-center gap-2">
            <Plus className="w-4 h-4 text-[#B8F23D] group-hover:rotate-90 transition-transform" />
            <span className="text-xs font-semibold">New Task</span>
          </div>
          <kbd className="font-mono text-[10px] bg-[#0D120F] border border-[#202A22] px-1.5 py-0.5 rounded text-[#9BA79D] group-hover:text-white">
            ⌘N
          </kbd>
        </button>

        {/* Navigation Items */}
        <nav className="flex flex-col gap-0.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = item.exact
              ? pathname === item.href
              : pathname.startsWith(item.href);

            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all relative ${
                  isActive
                    ? "bg-[#121812] text-[#F1F5ED] font-semibold"
                    : "text-[#9BA79D] hover:bg-[#0D120F] hover:text-[#F1F5ED]"
                }`}
              >
                {isActive && (
                  <span className="absolute left-0 top-1.5 bottom-1.5 w-0.5 bg-[#B8F23D] rounded-r" />
                )}
                <div className="flex items-center gap-2.5">
                  <Icon
                    className={`w-4 h-4 ${
                      isActive ? "text-[#B8F23D]" : "text-[#657066]"
                    }`}
                  />
                  <span>{item.name}</span>
                </div>
                {item.badge && (
                  <span
                    className={`font-mono text-[10px] px-1.5 py-0.5 rounded ${
                      isActive
                        ? "bg-[#B8F23D]/15 text-[#D5FF78] border border-[#B8F23D]/30"
                        : "bg-[#121812] text-[#657066] border border-[#202A22]"
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Bottom Telemetry & Health Panel */}
      <div className="flex flex-col gap-2 pt-3 border-t border-[#202A22]/60">
        {/* Local Mode Badge */}
        <div className="p-2.5 rounded-lg bg-[#0D120F] border border-[#202A22] flex flex-col gap-1 font-mono">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-[11px] text-[#D5FF78] font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-[#B8F23D] animate-pulse" />
              LOCAL MODE
            </div>
            <ShieldCheck className="w-3.5 h-3.5 text-[#B8F23D]" />
          </div>
          <div className="text-[10px] text-[#657066] leading-tight">
            Runs locally · No external network
          </div>
        </div>

        {/* Real Backend Status */}
        <div className="px-2.5 py-1.5 rounded-lg bg-[#0A0E0C] border border-[#202A22]/70 flex items-center justify-between text-[11px] font-mono">
          <div className="flex items-center gap-2">
            <span
              className={`w-2 h-2 rounded-full ${
                isBackendOnline ? "bg-[#22C55E]" : "bg-[#EF4444]"
              }`}
            />
            <span
              className={isBackendOnline ? "text-[#F1F5ED]" : "text-[#EF4444] font-medium"}
            >
              {isBackendOnline ? `Daemon v${health?.version || "0.1"}` : "Daemon offline"}
            </span>
          </div>

          {!isBackendOnline && (
            <button
              onClick={checkHealth}
              title="Retry connection"
              className="text-[#657066] hover:text-[#B8F23D] p-1 transition"
            >
              <RefreshCw className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>
    </aside>
  );
}
