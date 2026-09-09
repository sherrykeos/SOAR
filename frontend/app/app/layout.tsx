"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopBar } from "@/components/layout/TopBar";
import { MobileSidebar } from "@/components/layout/MobileSidebar";
import { CommandPalette } from "@/components/layout/CommandPalette";
import { WorkbenchProvider } from "@/context/WorkbenchContext";
import { ToastProvider } from "@/components/ui/Toast";

export default function WorkbenchLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const isChatPage = pathname === "/app";

  return (
    <WorkbenchProvider>
      <ToastProvider>
        <div className="h-screen w-screen overflow-hidden bg-[#070A08] text-[#F1F5ED] flex antialiased selection:bg-[#B8F23D] selection:text-[#070A08]">
          {/* Desktop Sidebar */}
          <div className="hidden md:block shrink-0 h-full">
            <Sidebar />
          </div>

          {/* Mobile Drawer */}
          <MobileSidebar />

          {/* Command Palette */}
          <CommandPalette />

          {/* Main Area */}
          <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
            <TopBar />
            <main
              className={`flex-1 flex flex-col min-w-0 min-h-0 bg-[#070A08] ${
                isChatPage ? "overflow-hidden" : "overflow-y-auto"
              }`}
            >
              {children}
            </main>
          </div>
        </div>
      </ToastProvider>
    </WorkbenchProvider>
  );
}
