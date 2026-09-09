import React from "react";
import Link from "next/link";
import { Logo } from "@/components/ui/Logo";

export function Footer() {
  return (
    <footer className="border-t border-[#202A22]/80 bg-[#070A08] py-14 text-xs font-sans text-[#9BA79D]">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 mb-12">
          {/* Brand Summary */}
          <div className="col-span-2 space-y-4">
            <Logo href="/" />
            <p className="text-xs text-[#657066] max-w-sm leading-relaxed">
              The sovereign AI workbench engineered for teams requiring full data privacy, zero external network dependency, and verified on-premise execution.
            </p>
            <div className="flex items-center gap-2 font-mono text-[11px] text-[#B8F23D]">
              <span className="h-1.5 w-1.5 rounded-full bg-[#B8F23D]" />
              <span>LOCAL MODE · Core daemon active</span>
            </div>
          </div>

          {/* Product Links */}
          <div>
            <h4 className="font-mono text-xs font-semibold text-[#F1F5ED] uppercase tracking-wider mb-3">
              Product
            </h4>
            <ul className="space-y-2">
              <li>
                <Link href="/app" className="hover:text-[#D5FF78] transition">
                  Workbench
                </Link>
              </li>
              <li>
                <Link href="/app/tasks" className="hover:text-[#D5FF78] transition">
                  Tasks
                </Link>
              </li>
              <li>
                <Link href="/app/models" className="hover:text-[#D5FF78] transition">
                  Models
                </Link>
              </li>
              <li>
                <Link href="/app/files" className="hover:text-[#D5FF78] transition">
                  Files
                </Link>
              </li>
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h4 className="font-mono text-xs font-semibold text-[#F1F5ED] uppercase tracking-wider mb-3">
              Resources
            </h4>
            <ul className="space-y-2">
              <li>
                <a href="#capabilities" className="hover:text-[#D5FF78] transition">
                  Use Cases
                </a>
              </li>
              <li>
                <a href="#workflow" className="hover:text-[#D5FF78] transition">
                  Architecture
                </a>
              </li>
              <li>
                <a href="#inspector" className="hover:text-[#D5FF78] transition">
                  Run Inspector
                </a>
              </li>
              <li>
                <Link href="/app/settings" className="hover:text-[#D5FF78] transition">
                  Settings
                </Link>
              </li>
            </ul>
          </div>

          {/* Security & Air-Gap */}
          <div>
            <h4 className="font-mono text-xs font-semibold text-[#F1F5ED] uppercase tracking-wider mb-3">
              Security
            </h4>
            <ul className="space-y-2">
              <li>
                <span className="text-[#657066]">Local Storage Only</span>
              </li>
              <li>
                <span className="text-[#657066]">Sandboxed Execution</span>
              </li>
              <li>
                <span className="text-[#657066]">No External Network</span>
              </li>
              <li>
                <span className="text-[#657066]">SHA256 File Hashes</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-[#202A22] flex flex-col sm:flex-row items-center justify-between text-[#657066] text-xs font-mono gap-4">
          <div>© 2026 SOAR AI Systems. Sovereign AI Workbench.</div>
          <div className="flex items-center gap-6">
            <span className="hover:text-[#9BA79D] cursor-pointer">Privacy</span>
            <span className="hover:text-[#9BA79D] cursor-pointer">Terms</span>
            <span className="hover:text-[#9BA79D] cursor-pointer">Air-Gap Policy</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
