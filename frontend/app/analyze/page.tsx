import type { Metadata } from "next";
import { AnalyzeForm } from "@/components/analyze-form";
import { SiteFooter, SiteHeader } from "@/components/site-header";

export const metadata: Metadata = {
  title: "Analyze your profile",
};

export default function AnalyzePage() {
  return (
    <>
      <SiteHeader compact />
      <main className="mx-auto max-w-4xl px-5 pb-24 pt-14 sm:px-8 sm:pt-20">
        <div className="mb-10 max-w-2xl">
          <p className="inline-flex items-center gap-2 rounded-full border border-lilac/20 bg-lilac/[.07] px-3 py-1.5 font-mono text-[10px] tracking-[.12em] text-lilac">
            <span className="size-1.5 rounded-full bg-mint" />
            YOUR STARTING POINT
          </p>
          <h1 className="mt-5 font-display text-4xl font-semibold tracking-[-.065em] text-white sm:text-5xl">
            Let&apos;s map out your next move.
          </h1>
          <p className="mt-4 max-w-xl text-sm leading-7 text-muted sm:text-base">
            Share your resume, a few links, and a role you&apos;re aiming for.
            We&apos;ll look for the evidence behind your experience.
          </p>
        </div>
        <AnalyzeForm />
      </main>
      <SiteFooter />
    </>
  );
}
