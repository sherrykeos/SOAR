"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  PlusCircle,
  ListTodo,
  FolderOpen,
  Database,
  Cpu,
  Wrench,
  Settings,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import { useWorkbench } from "@/context/WorkbenchContext";
import { motion, AnimatePresence } from "framer-motion";

export function CommandPalette() {
  const router = useRouter();
  const {
    commandPaletteOpen,
    setCommandPaletteOpen,
    models,
    setSelectedModel,
  } = useWorkbench();

  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const baseCommands = [
    {
      id: "new-task",
      title: "New Task",
      category: "Actions",
      icon: PlusCircle,
      action: () => router.push("/app"),
    },
    {
      id: "tasks",
      title: "Task History",
      category: "Navigation",
      icon: ListTodo,
      action: () => router.push("/app/tasks"),
    },
    {
      id: "files",
      title: "Local Files",
      category: "Navigation",
      icon: FolderOpen,
      action: () => router.push("/app/files"),
    },
    {
      id: "knowledge",
      title: "Knowledge Base",
      category: "Navigation",
      icon: Database,
      action: () => router.push("/app/knowledge"),
    },
    {
      id: "models",
      title: "Model Manager",
      category: "Navigation",
      icon: Cpu,
      action: () => router.push("/app/models"),
    },
    {
      id: "tools",
      title: "Tool Registry",
      category: "Navigation",
      icon: Wrench,
      action: () => router.push("/app/tools"),
    },
    {
      id: "settings",
      title: "Settings & Air-Gap Policy",
      category: "Navigation",
      icon: Settings,
      action: () => router.push("/app/settings"),
    },
  ];

  // Dynamic model commands
  const modelCommands = models.map((m) => ({
    id: `model-${m.id}`,
    title: `Use Model: ${m.id}`,
    category: "Models",
    icon: Sparkles,
    action: () => {
      setSelectedModel(m.id);
      router.push("/app");
    },
  }));

  const allCommands = [...baseCommands, ...modelCommands];

  const filteredCommands = allCommands.filter((c) =>
    c.title.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    if (commandPaletteOpen) {
      const timer = setTimeout(() => {
        inputRef.current?.focus();
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [commandPaletteOpen]);

  const handleClose = useCallback(() => {
    setQuery("");
    setSelectedIndex(0);
    setCommandPaletteOpen(false);
  }, [setCommandPaletteOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!commandPaletteOpen) return;

      if (e.key === "Escape") {
        handleClose();
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev < filteredCommands.length - 1 ? prev + 1 : 0
        );
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev > 0 ? prev - 1 : filteredCommands.length - 1
        );
      } else if (e.key === "Enter") {
        e.preventDefault();
        const selected = filteredCommands[selectedIndex];
        if (selected) {
          selected.action();
          handleClose();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [commandPaletteOpen, filteredCommands, selectedIndex, handleClose]);

  return (
    <AnimatePresence>
      {commandPaletteOpen && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-[#040605]/80 backdrop-blur-sm"
            onClick={handleClose}
          />

          <motion.div
            initial={{ opacity: 0, scale: 0.97, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.97, y: -10 }}
            transition={{ duration: 0.15 }}
            className="relative z-10 w-full max-w-lg rounded-xl bg-[#0D120F] border border-[#202A22] shadow-2xl overflow-hidden font-mono text-xs"
          >
            {/* Search Input Bar */}
            <div className="flex items-center gap-3 px-4 py-3.5 border-b border-[#202A22] bg-[#121812]">
              <Search className="w-4 h-4 text-[#B8F23D] shrink-0" />
              <input
                ref={inputRef}
                type="text"
                placeholder="Type a command or search workbench..."
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setSelectedIndex(0);
                }}
                className="w-full bg-transparent text-[#F1F5ED] placeholder:text-[#657066] focus:outline-none"
              />
              <kbd className="px-1.5 py-0.5 rounded bg-[#171E18] text-[#9BA79D] text-[10px] border border-[#202A22]">
                ESC
              </kbd>
            </div>

            {/* Commands List */}
            <div className="max-h-72 overflow-y-auto p-2 divide-y divide-[#202A22]/40">
              {filteredCommands.length === 0 ? (
                <div className="p-6 text-center text-[#657066]">
                  No matching commands found.
                </div>
              ) : (
                filteredCommands.map((cmd, idx) => {
                  const Icon = cmd.icon;
                  const isSelected = idx === selectedIndex;
                  return (
                    <div
                      key={cmd.id}
                      onClick={() => {
                        cmd.action();
                        handleClose();
                      }}
                      onMouseEnter={() => setSelectedIndex(idx)}
                      className={`flex items-center justify-between px-3 py-2.5 rounded-lg cursor-pointer transition-colors ${
                        isSelected
                          ? "bg-[#171E18] text-[#D5FF78]"
                          : "text-[#9BA79D] hover:bg-[#121812] hover:text-[#F1F5ED]"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <Icon
                          className={`w-4 h-4 ${
                            isSelected ? "text-[#B8F23D]" : "text-[#657066]"
                          }`}
                        />
                        <span className="font-medium text-xs text-[#F1F5ED]">
                          {cmd.title}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-[#657066] uppercase">
                          {cmd.category}
                        </span>
                        {isSelected && (
                          <ArrowRight className="w-3.5 h-3.5 text-[#B8F23D]" />
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Footer */}
            <div className="px-4 py-2 bg-[#070A08] border-t border-[#202A22] text-[10px] text-[#657066] flex justify-between">
              <span>Navigate with ↑ ↓ · Select with Enter</span>
              <span>SOAR Command Engine</span>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
