import React from "react";
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
  return (
    <WorkbenchProvider>
      <ToastProvider>
        <div className="min-h-screen bg-[#070A08] text-[#F1F5ED] flex flex-col md:flex-row antialiased selection:bg-[#B8F23D] selection:text-[#070A08]">
          {/* Desktop Sidebar */}
          <div className="hidden md:block shrink-0">
            <Sidebar />
          </div>

          {/* Mobile Drawer */}
          <MobileSidebar />

          {/* Command Palette */}
          <CommandPalette />

          {/* Main Area */}
          <div className="flex-1 flex flex-col min-w-0 min-h-screen">
            <TopBar />
            <main className="flex-1 flex flex-col min-w-0 bg-[#070A08]">
              {children}
            </main>
          </div>
        </div>
      </ToastProvider>
    </WorkbenchProvider>
  );
}
