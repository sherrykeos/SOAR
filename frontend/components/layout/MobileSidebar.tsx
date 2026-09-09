"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { X, ShieldCheck } from "lucide-react";
import { Logo } from "@/components/ui/Logo";
import { useWorkbench } from "@/context/WorkbenchContext";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  ListTodo,
  FolderOpen,
  Database,
  Cpu,
  Wrench,
  Settings,
} from "lucide-react";

const emptySubscribe = () => () => {};

export function MobileSidebar() {
  const isClient = React.useSyncExternalStore(
    emptySubscribe,
    () => true,
    () => false
  );
  const pathname = usePathname();
  const { mobileSidebarOpen, setMobileSidebarOpen, sessionTasks, models } =
    useWorkbench();

  useEffect(() => {
    setMobileSidebarOpen(false);
  }, [pathname, setMobileSidebarOpen]);

  const navItems = [
    { name: "Home", href: "/app", icon: LayoutDashboard },
    {
      name: "Tasks",
      href: "/app/tasks",
      icon: ListTodo,
      badge: isClient && sessionTasks.length > 0 ? `${sessionTasks.length}` : undefined,
    },
    { name: "Files", href: "/app/files", icon: FolderOpen },
    { name: "Knowledge", href: "/app/knowledge", icon: Database },
    {
      name: "Models",
      href: "/app/models",
      icon: Cpu,
      badge: isClient && models.length > 0 ? `${models.length}` : undefined,
    },
    { name: "Tools", href: "/app/tools", icon: Wrench },
    { name: "Settings", href: "/app/settings", icon: Settings },
  ];

  return (
    <AnimatePresence>
      {mobileSidebarOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-[#040605]/80 backdrop-blur-sm"
            onClick={() => setMobileSidebarOpen(false)}
          />

          <motion.div
            initial={{ x: -280 }}
            animate={{ x: 0 }}
            exit={{ x: -280 }}
            transition={{ duration: 0.2 }}
            className="relative z-10 w-72 bg-[#070A08] border-r border-[#202A22] h-full flex flex-col justify-between p-4"
          >
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-[#202A22]">
                <Logo href="/" />
                <button
                  onClick={() => setMobileSidebarOpen(false)}
                  className="p-1 rounded text-[#9BA79D] hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <nav className="mt-4 flex flex-col gap-1">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = pathname === item.href;
                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      className={`flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-colors ${
                        isActive
                          ? "bg-[#121812] text-[#F1F5ED] font-semibold"
                          : "text-[#9BA79D] hover:bg-[#0D120F] hover:text-[#F1F5ED]"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <Icon
                          className={`w-4 h-4 ${
                            isActive ? "text-[#B8F23D]" : "text-[#657066]"
                          }`}
                        />
                        <span>{item.name}</span>
                      </div>
                      {item.badge && (
                        <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-[#171E18] text-[#9BA79D]">
                          {item.badge}
                        </span>
                      )}
                    </Link>
                  );
                })}
              </nav>
            </div>

            <div className="p-3 rounded-lg bg-[#0D120F] border border-[#202A22] font-mono text-xs">
              <div className="flex items-center gap-1.5 text-[11px] text-[#D5FF78] font-semibold">
                <ShieldCheck className="w-4 h-4 text-[#B8F23D]" />
                LOCAL MODE
              </div>
              <div className="text-[10px] text-[#657066] mt-1">
                Runs locally · No external network
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
