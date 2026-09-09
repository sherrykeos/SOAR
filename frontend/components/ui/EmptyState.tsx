import React from "react";
import { cn } from "@/lib/utils/cn";

export interface EmptyStateProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center p-8 text-center rounded-xl bg-[#0D120F]/60 border border-[#202A22] border-dashed",
        className
      )}
    >
      <div className="w-12 h-12 rounded-lg bg-[#121812] border border-[#202A22] flex items-center justify-center text-[#9BA79D] mb-4">
        {icon}
      </div>
      <h3 className="text-sm font-semibold text-[#F1F5ED] mb-1">{title}</h3>
      <p className="text-xs text-[#9BA79D] max-w-sm mb-4 leading-relaxed">
        {description}
      </p>
      {action && <div>{action}</div>}
    </div>
  );
}
