"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import { CheckCircle2, AlertTriangle, AlertCircle, Info, X } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { motion, AnimatePresence } from "framer-motion";

export type ToastType = "success" | "warning" | "error" | "info";

export interface ToastItem {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
}

interface ToastContextType {
  toast: (title: string, options?: { type?: ToastType; message?: string }) => void;
  success: (title: string, message?: string) => void;
  error: (title: string, message?: string) => void;
  warning: (title: string, message?: string) => void;
  info: (title: string, message?: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback(
    (title: string, options?: { type?: ToastType; message?: string }) => {
      const id = Math.random().toString(36).substring(2, 9);
      const newToast: ToastItem = {
        id,
        type: options?.type || "info",
        title,
        message: options?.message,
      };

      setToasts((prev) => [...prev.slice(-4), newToast]);

      setTimeout(() => {
        removeToast(id);
      }, 4000);
    },
    [removeToast]
  );

  const success = useCallback(
    (title: string, message?: string) => addToast(title, { type: "success", message }),
    [addToast]
  );
  const error = useCallback(
    (title: string, message?: string) => addToast(title, { type: "error", message }),
    [addToast]
  );
  const warning = useCallback(
    (title: string, message?: string) => addToast(title, { type: "warning", message }),
    [addToast]
  );
  const info = useCallback(
    (title: string, message?: string) => addToast(title, { type: "info", message }),
    [addToast]
  );

  return (
    <ToastContext.Provider value={{ toast: addToast, success, error, warning, info }}>
      {children}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
        <AnimatePresence>
          {toasts.map((t) => (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, y: 15, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.95 }}
              transition={{ duration: 0.2 }}
              className={cn(
                "pointer-events-auto flex items-start gap-3 p-3.5 rounded-lg border shadow-xl backdrop-blur-md",
                t.type === "success" && "bg-[#0D120F]/95 border-[#22C55E]/40 text-[#F1F5ED]",
                t.type === "error" && "bg-[#0D120F]/95 border-[#EF4444]/40 text-[#F1F5ED]",
                t.type === "warning" && "bg-[#0D120F]/95 border-[#F59E0B]/40 text-[#F1F5ED]",
                t.type === "info" && "bg-[#0D120F]/95 border-[#202A22] text-[#F1F5ED]"
              )}
            >
              <div className="shrink-0 mt-0.5">
                {t.type === "success" && <CheckCircle2 className="w-4 h-4 text-[#22C55E]" />}
                {t.type === "error" && <AlertCircle className="w-4 h-4 text-[#EF4444]" />}
                {t.type === "warning" && <AlertTriangle className="w-4 h-4 text-[#F59E0B]" />}
                {t.type === "info" && <Info className="w-4 h-4 text-[#B8F23D]" />}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-semibold text-[#F1F5ED]">{t.title}</div>
                {t.message && (
                  <div className="text-[11px] text-[#9BA79D] mt-0.5 break-words">
                    {t.message}
                  </div>
                )}
              </div>
              <button
                onClick={() => removeToast(t.id)}
                className="shrink-0 text-[#657066] hover:text-[#F1F5ED] transition-colors p-0.5"
                aria-label="Close toast"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}
