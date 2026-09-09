import React from "react";
import { cn } from "@/lib/utils/cn";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "lime" | "emerald" | "amber" | "rose" | "violet" | "outline";
  size?: "sm" | "md";
}

export function Badge({
  className,
  variant = "default",
  size = "md",
  children,
  ...props
}: BadgeProps) {
  const baseStyles =
    "inline-flex items-center font-mono uppercase tracking-wider rounded border transition-colors select-none";

  const variants = {
    default: "bg-[#171E18] text-[#9BA79D] border-[#202A22]",
    lime: "bg-[#B8F23D]/10 text-[#D5FF78] border-[#B8F23D]/30",
    emerald: "bg-[#22C55E]/10 text-[#4ADE80] border-[#22C55E]/30",
    amber: "bg-[#F59E0B]/10 text-[#FCD34D] border-[#F59E0B]/30",
    rose: "bg-[#EF4444]/10 text-[#FCA5A5] border-[#EF4444]/30",
    violet: "bg-[#A78BFA]/10 text-[#C4B5FD] border-[#A78BFA]/30",
    outline: "bg-transparent text-[#9BA79D] border-[#202A22]",
  };

  const sizes = {
    sm: "text-[10px] px-1.5 py-0.5 leading-none",
    md: "text-xs px-2 py-0.5 leading-tight font-medium",
  };

  return (
    <span
      className={cn(baseStyles, variants[variant], sizes[size], className)}
      {...props}
    >
      {children}
    </span>
  );
}
