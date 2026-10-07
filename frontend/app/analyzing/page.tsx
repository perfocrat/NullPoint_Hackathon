"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Activity, BadgeCheck, FileSearch, Route, Sparkles } from "lucide-react";
import { Brand } from "@/components/site-header";

const stages = [
  { label: "Reading your experience", icon: FileSearch },
  { label: "Looking for skill evidence", icon: BadgeCheck },
  { label: "Matching your target role", icon: Activity },
  { label: "Preparing your next steps", icon: Route },
];

export default function AnalyzingPage() {
  const router = useRouter();
  const [stage, setStage] = useState(0);

  useEffect(() => {
    if (!window.sessionStorage.getItem("careerLensAnalysis")) {
      router.replace("/analyze");
      return;
    }

    const stageTimer = window.setInterval(() => {
      setStage((current) => Math.min(current + 1, stages.length - 1));
    }, 520);
    const redirectTimer = window.setTimeout(() => router.replace("/report"), 2300);

    return () => {
      window.clearInterval(stageTimer);
      window.clearTimeout(redirectTimer);
    };
  }, [router]);

  const activeStage = stages[stage];

  return (
    <main className="grid min-h-screen place-items-center px-5 py-12">
      <section className="w-full max-w-xl rounded-[28px] border border-white/10 bg-gradient-to-br from-[#141a29]/95 to-[#0d111c]/95 px-6 py-10 shadow-[0_35px_100px_rgba(0,0,0,.35)] sm:px-10">
        <div className="flex justify-center">
          <Brand />
        </div>
        <div className="relative mx-auto mt-12 grid size-24 place-items-center">
          <div className="absolute inset-0 rounded-full border border-lilac/20" />
          <div className="absolute inset-2 animate-spin rounded-full border border-dashed border-mint/40 [animation-duration:8s]" />
          <div className="grid size-14 place-items-center rounded-full bg-gradient-to-br from-lilac to-[#5548ba] text-white shadow-[0_0_38px_rgba(139,124,255,.4)]">
            <Sparkles size={22} />
          </div>
        </div>
        <div className="mt-8 text-center">
          <p className="font-mono text-[10px] tracking-[.14em] text-lilac">
            CAREERLENS ANALYSIS
          </p>
          <h1 className="mt-3 font-display text-3xl font-semibold tracking-[-.055em] text-white">
            Connecting the dots.
          </h1>
          <p aria-live="polite" className="mt-2 text-sm text-muted">
            {activeStage.label}
          </p>
        </div>
        <div className="mt-8 h-1.5 overflow-hidden rounded-full bg-white/[.07]" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={(stage + 1) * 25} aria-label="Profile analysis progress">
          <div
            className="h-full rounded-full bg-gradient-to-r from-lilac to-mint transition-[width] duration-500"
            style={{ width: `${(stage + 1) * 25}%` }}
          />
        </div>
        <div className="mt-7 space-y-2">
          {stages.map(({ label, icon: Icon }, index) => {
            const complete = index < stage;
            const current = index === stage;
            return (
              <div
                className={`flex items-center gap-3 rounded-xl px-3.5 py-3 text-sm transition ${
                  current
                    ? "border border-lilac/15 bg-lilac/[.06] text-white"
                    : complete
                      ? "text-mint"
                      : "text-muted/70"
                }`}
                key={label}
              >
                <Icon size={16} />
                <span>{label}</span>
                {current && (
                  <span className="ml-auto size-1.5 animate-pulse rounded-full bg-mint" />
                )}
              </div>
            );
          })}
        </div>
      </section>
    </main>
  );
}
