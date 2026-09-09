import React from "react";
import Link from "next/link";
import { cn } from "@/lib/utils/cn";

export interface LogoProps {
  className?: string;
  showSubtitle?: boolean;
  href?: string;
}

export function Logo({
  className,
  showSubtitle = true,
  href = "/",
}: LogoProps) {
  const content = (
    <div className={cn("flex items-center gap-3 select-none group", className)}>
      <div className="relative flex items-center justify-center">
        <div className="absolute -inset-1 bg-[#B8F23D]/20 blur-md rounded-full group-hover:bg-[#B8F23D]/35 transition-all duration-300" />
        <svg
          className="h-7 w-auto relative z-10"
          fill="none"
          viewBox="0 0 36 36"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M18 2L32 32H24L18 18L12 32H4L18 2Z"
            fill="url(#soarLimeGrad)"
          />
          <path d="M18 10L25 26H11L18 10Z" fill="#070A08" />
          <circle cx="18" cy="18" fill="#B8F23D" r="2.5" />
          <defs>
            <linearGradient
              id="soarLimeGrad"
              x1="4"
              y1="2"
              x2="32"
              y2="32"
              gradientUnits="userSpaceOnUse"
            >
              <stop offset="0%" stopColor="#D5FF78" />
              <stop offset="100%" stopColor="#B8F23D" />
            </linearGradient>
          </defs>
        </svg>
      </div>
      <div className="flex flex-col">
        <span className="font-sans font-extrabold text-base tracking-[0.18em] text-[#F1F5ED] leading-none">
          SOAR
        </span>
        {showSubtitle && (
          <span className="font-mono text-[9px] text-[#657066] uppercase tracking-wider mt-0.5 leading-none">
            Sovereign AI
          </span>
        )}
      </div>
    </div>
  );

  if (href) {
    return <Link href={href}>{content}</Link>;
  }

  return content;
}
