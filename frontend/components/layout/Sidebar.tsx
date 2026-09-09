"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  ListTodo,
  FolderOpen,
  Database,
  Cpu,
  Wrench,
  Settings,
  Plus,
  ShieldCheck,
  RefreshCw,
  PanelLeftClose,
  PanelLeft,
  MessageSquare,
  Trash2,
} from "lucide-react";
import { Logo } from "@/components/ui/Logo";
import { useWorkbench } from "@/context/WorkbenchContext";

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const {
    isHydrated,
    sessions,
    activeSessionId,
    setActiveSessionId,
    createNewSession,
    deleteSession,
    models,
    isBackendOnline,
    health,
    checkHealth,
    sidebarCollapsed,
    setSidebarCollapsed,
  } = useWorkbench();

  const navItems = [
    {
      name: "Chats",
      href: "/app",
      icon: MessageSquare,
      exact: true,
      badge: isHydrated && sessions.length > 0 ? `${sessions.length}` : undefined,
    },
    {
      name: "Tasks",
      href: "/app/tasks",
      icon: ListTodo,
    },
    { name: "Files", href: "/app/files", icon: FolderOpen },
    { name: "Knowledge", href: "/app/knowledge", icon: Database },
    {
      name: "Models",
      href: "/app/models",
      icon: Cpu,
      badge: isHydrated && models.length > 0 ? `${models.length}` : undefined,
    },
    { name: "Tools", href: "/app/tools", icon: Wrench },
    { name: "Settings", href: "/app/settings", icon: Settings },
  ];

  const handleNewChat = React.useCallback(() => {
    const active = sessions.find((s) => s.id === activeSessionId) || sessions[0];
    if (active && active.messages.length === 0) {
      setActiveSessionId(active.id);
      if (pathname !== "/app") {
        router.push("/app");
      }
      return;
    }
    const newId = createNewSession();
    setActiveSessionId(newId);
    if (pathname !== "/app") {
      router.push("/app");
    }
  }, [sessions, activeSessionId, createNewSession, setActiveSessionId, pathname, router]);

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        (e.metaKey && e.key.toLowerCase() === "n") ||
        (e.altKey && e.key.toLowerCase() === "n") ||
        (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === "n")
      ) {
        e.preventDefault();
        handleNewChat();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleNewChat]);

  const handleSelectSession = (id: string) => {
    setActiveSessionId(id);
    if (pathname !== "/app") {
      router.push("/app");
    }
  };

  const handleDeleteSession = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    deleteSession(id);
  };

  return (
    <aside
      className={`bg-[#070A08] border-r border-[#202A22] flex flex-col justify-between p-3 select-none shrink-0 h-full font-sans transition-all duration-200 z-20 ${
        sidebarCollapsed ? "w-[68px]" : "w-64"
      }`}
    >
      <div className="flex flex-col gap-3 min-h-0 overflow-hidden flex-1">
        {/* Top Header: Logo + Collapse Toggle */}
        <div className="flex items-center justify-between px-1 pt-1 pb-2 border-b border-[#202A22]/50 shrink-0">
          {!sidebarCollapsed ? (
            <>
              <Logo href="/" />
              <button
                onClick={() => setSidebarCollapsed(true)}
                className="p-1.5 rounded-lg text-[#657066] hover:text-[#F1F5ED] hover:bg-[#121812] transition-colors cursor-pointer"
                title="Collapse sidebar"
              >
                <PanelLeftClose className="w-4 h-4" />
              </button>
            </>
          ) : (
            <div className="w-full flex flex-col items-center gap-2">
              <button
                onClick={() => setSidebarCollapsed(false)}
                className="p-2 rounded-lg text-[#9BA79D] hover:text-[#D5FF78] hover:bg-[#121812] transition-colors cursor-pointer"
                title="Expand sidebar"
              >
                <PanelLeft className="w-5 h-5 text-[#B8F23D]" />
              </button>
            </div>
          )}
        </div>

        {/* New Chat Button */}
        {!sidebarCollapsed ? (
          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-between px-3 py-2 bg-[#121812] border border-[#B8F23D]/30 text-[#F1F5ED] rounded-lg hover:border-[#B8F23D] hover:bg-[#171E18] transition-all group cursor-pointer shadow-sm shrink-0"
          >
            <div className="flex items-center gap-2">
              <Plus className="w-4 h-4 text-[#B8F23D] group-hover:rotate-90 transition-transform" />
              <span className="text-xs font-semibold">New Chat</span>
            </div>
            <kbd className="font-mono text-[10px] bg-[#0D120F] border border-[#202A22] px-1.5 py-0.5 rounded text-[#9BA79D] group-hover:text-white">
              ⌘N
            </kbd>
          </button>
        ) : (
          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-center p-2.5 bg-[#121812] border border-[#B8F23D]/30 text-[#B8F23D] rounded-lg hover:border-[#B8F23D] hover:bg-[#171E18] transition-all cursor-pointer shadow-sm shrink-0"
            title="New Chat (⌘N)"
          >
            <Plus className="w-4 h-4" />
          </button>
        )}

        {/* Navigation Items */}
        <nav className="flex flex-col gap-0.5 shrink-0">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = item.exact
              ? pathname === item.href
              : pathname.startsWith(item.href);

            if (sidebarCollapsed) {
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  title={item.name}
                  className={`flex items-center justify-center p-2.5 rounded-lg text-xs transition-all relative ${
                    isActive
                      ? "bg-[#121812] text-[#B8F23D]"
                      : "text-[#9BA79D] hover:bg-[#0D120F] hover:text-[#F1F5ED]"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {item.badge && (
                    <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-[#B8F23D]" />
                  )}
                </Link>
              );
            }

            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center justify-between px-3 py-1.5 rounded-lg text-xs font-medium transition-all relative ${
                  isActive
                    ? "bg-[#121812] text-[#F1F5ED] font-semibold"
                    : "text-[#9BA79D] hover:bg-[#0D120F] hover:text-[#F1F5ED]"
                }`}
              >
                {isActive && (
                  <span className="absolute left-0 top-1.5 bottom-1.5 w-0.5 bg-[#B8F23D] rounded-r" />
                )}
                <div className="flex items-center gap-2.5 min-w-0">
                  <Icon
                    className={`w-4 h-4 shrink-0 ${
                      isActive ? "text-[#B8F23D]" : "text-[#657066]"
                    }`}
                  />
                  <span className="truncate">{item.name}</span>
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

        {/* Chat Sessions History (ChatGPT / Claude style) */}
        {!sidebarCollapsed && (
          <div className="flex-1 flex flex-col min-h-0 pt-2 border-t border-[#202A22]/50 overflow-hidden">
            <div className="px-2 pb-1 text-[10px] uppercase font-bold tracking-wider text-[#657066] font-mono flex items-center justify-between">
              <span>CONVERSATIONS</span>
              <span className="text-[9px] text-[#657066]" suppressHydrationWarning>
                {isHydrated ? sessions.length : 0}
              </span>
            </div>

            <div className="flex-1 overflow-y-auto space-y-0.5 pr-1 text-xs">
              {!isHydrated || sessions.length === 0 ? (
                <div className="px-2 py-4 text-center text-[11px] text-[#657066] font-mono">
                  No active chats yet.
                  <br />
                  Click + New Chat above.
                </div>
              ) : (
                sessions.map((s) => {
                  const isCurrent =
                    activeSessionId === s.id ||
                    (!activeSessionId && sessions[0]?.id === s.id);

                  return (
                    <div
                      key={s.id}
                      onClick={() => handleSelectSession(s.id)}
                      className={`group w-full px-2.5 py-1.5 rounded-lg transition-all flex items-center justify-between gap-2 cursor-pointer ${
                        isCurrent
                          ? "bg-[#121812] text-[#F1F5ED] border border-[#B8F23D]/30 font-medium"
                          : "text-[#9BA79D] hover:bg-[#0D120F] hover:text-[#F1F5ED] border border-transparent"
                      }`}
                      title={s.title}
                    >
                      <div className="flex items-center gap-2 min-w-0 flex-1">
                        <MessageSquare
                          className={`w-3.5 h-3.5 shrink-0 ${
                            isCurrent ? "text-[#B8F23D]" : "text-[#657066]"
                          }`}
                        />
                        <span className="truncate text-xs">{s.title || "Untitled Chat"}</span>
                      </div>

                      {/* Delete button on hover */}
                      <button
                        onClick={(e) => handleDeleteSession(e, s.id)}
                        className="opacity-0 group-hover:opacity-100 p-1 rounded text-[#657066] hover:text-[#EF4444] hover:bg-[#171E18] transition-opacity shrink-0"
                        title="Delete chat"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}
      </div>

      {/* Bottom Telemetry & Health Panel */}
      <div className="flex flex-col gap-2 pt-3 border-t border-[#202A22]/60 shrink-0">
        {!sidebarCollapsed ? (
          <>
            {/* Local Mode Badge */}
            <div className="p-2.5 rounded-lg bg-[#0D120F] border border-[#202A22] flex flex-col gap-1 font-mono">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-[11px] text-[#D5FF78] font-semibold">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#B8F23D] animate-pulse" />
                  LOCAL MODE
                </div>
                <div title="LOCAL MODE — Runs locally · No external network">
                  <ShieldCheck className="w-3.5 h-3.5 text-[#B8F23D]" />
                </div>
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
                  className={
                    isBackendOnline ? "text-[#F1F5ED]" : "text-[#EF4444] font-medium"
                  }
                >
                  {isBackendOnline
                    ? `Daemon v${health?.version || "0.1"}`
                    : "Daemon offline"}
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
          </>
        ) : (
          <div className="flex flex-col items-center gap-2 py-1">
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                isBackendOnline ? "bg-[#22C55E]" : "bg-[#EF4444]"
              }`}
              title={isBackendOnline ? "Daemon Online" : "Daemon Offline"}
            />
            <div title="LOCAL MODE — Runs locally · No external network">
              <ShieldCheck className="w-4 h-4 text-[#B8F23D]" />
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
