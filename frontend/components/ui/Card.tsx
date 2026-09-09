import React from "react";
import { cn } from "@/lib/utils/cn";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "surface" | "elevated" | "subtle" | "ghost";
  borderGlow?: boolean;
}

export function Card({
  className,
  variant = "surface",
  borderGlow = false,
  children,
  ...props
}: CardProps) {
  const variants = {
    surface: "bg-[#0D120F] border border-[#202A22]",
    elevated: "bg-[#121812] border border-[#202A22] shadow-lg",
    subtle: "bg-[#171E18] border border-[#202A22]/80",
    ghost: "bg-transparent border border-[#202A22]",
  };

  return (
    <div
      className={cn(
        "rounded-xl transition-all duration-200",
        variants[variant],
        borderGlow && "hover:border-[#B8F23D]/40 hover:shadow-[0_0_20px_-4px_rgba(184,242,61,0.2)]",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
