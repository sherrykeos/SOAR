"use client";

import React from "react";
import { cn } from "@/lib/utils/cn";
import { Loader2 } from "lucide-react";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "primary",
      size = "md",
      isLoading = false,
      leftIcon,
      rightIcon,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      "inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-[#B8F23D]/40 active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none disabled:active:scale-100 select-none cursor-pointer";

    const variants = {
      primary:
        "bg-[#B8F23D] text-[#070A08] font-semibold hover:bg-[#D5FF78] shadow-[0_0_20px_-4px_rgba(184,242,61,0.4)] hover:shadow-[0_0_28px_-2px_rgba(184,242,61,0.55)]",
      secondary:
        "bg-[#121812] text-[#F1F5ED] border border-[#202A22] hover:bg-[#171E18] hover:border-[#2B382D] hover:text-white",
      outline:
        "bg-transparent text-[#F1F5ED] border border-[#202A22] hover:border-[#B8F23D]/60 hover:text-[#B8F23D] hover:bg-[#B8F23D]/5",
      ghost:
        "bg-transparent text-[#9BA79D] hover:text-[#F1F5ED] hover:bg-[#121812]",
      danger:
        "bg-[#EF4444]/15 text-[#EF4444] border border-[#EF4444]/30 hover:bg-[#EF4444]/25 hover:border-[#EF4444]/50",
    };

    const sizes = {
      sm: "text-xs px-2.5 py-1.5 gap-1.5",
      md: "text-sm px-4 py-2 gap-2",
      lg: "text-base px-6 py-3 gap-2.5 font-semibold",
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        {...props}
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 animate-spin text-current" />
        ) : (
          leftIcon
        )}
        {children}
        {!isLoading && rightIcon}
      </button>
    );
  }
);

Button.displayName = "Button";
