import React from "react";
import {
  FlaskConical,
  Wrench,
  Factory,
  Shield,
  Landmark,
  Zap,
} from "lucide-react";

export function IndustryStrip() {
  const industries = [
    { name: "Research", icon: FlaskConical, desc: "Laboratories & Science" },
    { name: "Engineering", icon: Wrench, desc: "Industrial & Structural" },
    { name: "Manufacturing", icon: Factory, desc: "Quality & Diagnostics" },
    { name: "Defence", icon: Shield, desc: "Sovereign Infrastructure" },
    { name: "Government", icon: Landmark, desc: "Confidential Operations" },
    { name: "Energy", icon: Zap, desc: "Refineries & Utilities" },
  ];

  return (
    <section className="relative z-10 w-full max-w-6xl mx-auto px-6 py-12 border-t border-b border-[#202A22]/60">
      <div className="text-center text-[11px] font-mono uppercase tracking-widest text-[#657066] mb-8 font-semibold">
        BUILT FOR WORK THAT MATTERS.
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-4">
        {industries.map((ind) => {
          const Icon = ind.icon;
          return (
            <div
              key={ind.name}
              className="flex flex-col items-center justify-center p-4 rounded-lg bg-[#0D120F]/40 border border-[#202A22]/50 hover:border-[#B8F23D]/30 hover:bg-[#121812] transition-all duration-200 group text-center"
            >
              <Icon className="w-5 h-5 text-[#9BA79D] group-hover:text-[#B8F23D] transition-colors mb-2" />
              <span className="text-xs font-semibold text-[#F1F5ED] group-hover:text-white transition-colors">
                {ind.name}
              </span>
              <span className="text-[10px] text-[#657066] mt-0.5">
                {ind.desc}
              </span>
            </div>
          );
        })}
      </div>
    </section>
  );
}
