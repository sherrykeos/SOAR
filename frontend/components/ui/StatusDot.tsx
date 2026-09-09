import React from "react";
import { cn } from "@/lib/utils/cn";

export interface StatusDotProps {
  status?: "active" | "online" | "warning" | "error" | "offline" | "idle";
  size?: "sm" | "md";
  pulse?: boolean;
  className?: string;
}

export function StatusDot({
  status = "online",
  size = "md",
  pulse = false,
  className,
}: StatusDotProps) {
  const colors = {
    active: "bg-[#B8F23D]",
    online: "bg-[#22C55E]",
    warning: "bg-[#F59E0B]",
    error: "bg-[#EF4444]",
    offline: "bg-[#657066]",
    idle: "bg-[#9BA79D]",
  };

  const dotSizes = {
    sm: "w-1.5 h-1.5",
    md: "w-2 h-2",
  };

  return (
    <span className={cn("relative inline-flex items-center justify-center shrink-0", dotSizes[size], className)}>
      {pulse && (
        <span
          className={cn(
            "animate-ping absolute inline-flex h-full w-full rounded-full opacity-75",
            colors[status]
          )}
        />
      )}
      <span
        className={cn("relative inline-flex rounded-full", dotSizes[size], colors[status])}
      />
    </span>
  );
}
