import React from "react";
import { LandingNavbar } from "@/components/landing/LandingNavbar";
import { Hero } from "@/components/landing/Hero";
import { IndustryStrip } from "@/components/landing/IndustryStrip";
import { WorkTypesSection } from "@/components/landing/WorkTypesSection";
import { ExecutionFlow } from "@/components/landing/ExecutionFlow";
import { DataSection } from "@/components/landing/DataSection";
import { RunInspectorShowcase } from "@/components/landing/RunInspectorShowcase";
import { BuildShowcase } from "@/components/landing/BuildShowcase";
import { FinalCTA } from "@/components/landing/FinalCTA";
import { Footer } from "@/components/landing/Footer";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#070A08] text-[#F1F5ED] flex flex-col selection:bg-[#B8F23D] selection:text-[#070A08]">
      <LandingNavbar />
      <main className="flex-1">
        <Hero />
        <IndustryStrip />
        <WorkTypesSection />
        <ExecutionFlow />
        <DataSection />
        <RunInspectorShowcase />
        <BuildShowcase />
        <FinalCTA />
      </main>
      <Footer />
    </div>
  );
}
