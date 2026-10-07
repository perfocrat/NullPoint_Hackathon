"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  ArrowUpRight,
  BadgeCheck,
  CircleHelp,
  FileCheck2,
  Lightbulb,
  Printer,
  Rocket,
  Target,
} from "lucide-react";
import { Brand, SiteFooter, SiteHeader } from "@/components/site-header";
import { getRoleLabel } from "@/lib/roles";
import type {
  CareerAnalysis,
  RoleFit,
  RoadmapStep,
  Skill,
  SkillGap,
} from "@/lib/types";

const breakdownRows: {
  key: "skillMatch" | "projectEvidence" | "projectQuality" | "activity" | "roleRequirements";
  label: string;
}[] = [
  { key: "skillMatch", label: "Skill match" },
  { key: "projectEvidence", label: "Project evidence" },
  { key: "projectQuality", label: "Project quality" },
  { key: "activity", label: "Activity" },
  { key: "roleRequirements", label: "Role requirements" },
];

export function ReportPage() {
  const [analysis, setAnalysis] = useState<CareerAnalysis | null>(null);
  const [ready, setReady] = useState(false);
  const [loadError, setLoadError] = useState("");

  useEffect(() => {
    const saved = window.sessionStorage.getItem("careerLensAnalysis");
    if (!saved) {
      setReady(true);
      return;
    }

    try {
      const parsed: unknown = JSON.parse(saved);
      if (!isCareerAnalysis(parsed)) {
        setLoadError("This saved report is incomplete. Please run a new analysis.");
      } else {
        const score = Math.min(parsed.score, 85);
        const explanation = parsed.explanation ?? "";
        setAnalysis({
          ...parsed,
          score,
          scoreStatus: parsed.scoreStatus ?? "Public evidence snapshot",
          explanation: explanation.includes("capped at 85")
            ? explanation
            : `${explanation} Public-evidence scores are capped at 85 because identity and code originality aren't confirmed.`.trim(),
          roles: parsed.roles.map((role) => ({ ...role, fit: Math.min(role.fit, 85) })),
        });
      }
    } catch {
      setLoadError("We couldn’t read this saved report. Please run a new analysis.");
    }
    setReady(true);
  }, []);

  if (!ready) {
    return (
      <main className="grid min-h-screen place-items-center px-5">
        <p className="font-mono text-xs text-muted">OPENING YOUR REPORT…</p>
      </main>
    );
  }

  return (
    <>
      <div className="report-chrome">
        <SiteHeader compact />
      </div>
      {analysis ? (
        <main className="mx-auto max-w-7xl px-5 pb-20 pt-10 sm:px-8 sm:pt-14">
          <div className="mb-9 flex flex-wrap items-center justify-between gap-4">
            <Brand />
            <div className="flex items-center gap-2">
              <button
                className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-line bg-white/[.03] px-3.5 text-xs font-semibold text-white transition hover:border-lilac/35 hover:bg-white/[.06]"
                onClick={() => window.print()}
                type="button"
              >
                <Printer size={15} />
                <span className="hidden sm:inline">Print / save PDF</span>
                <span className="sm:hidden">Save PDF</span>
              </button>
              <Link
                className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-line bg-white/[.03] px-3.5 text-xs font-semibold text-white transition hover:border-lilac/35 hover:bg-white/[.06]"
                href="/analyze"
              >
                New analysis
                <ArrowUpRight size={14} />
              </Link>
            </div>
          </div>

          <div className="flex flex-col justify-between gap-6 border-b border-line pb-8 sm:flex-row sm:items-end">
            <div>
              <Eyebrow>YOUR PUBLIC-EVIDENCE REPORT</Eyebrow>
              <h1 className="mt-4 font-display text-4xl font-semibold tracking-[-.065em] text-white sm:text-5xl">
                Your next move,
                <br className="hidden sm:block" /> in focus.
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-muted">
                Here&apos;s how your current profile lines up with the role
                you&apos;re working toward.
              </p>
            </div>
            <div className="rounded-2xl border border-lilac/20 bg-lilac/[.06] px-5 py-4 sm:min-w-52">
              <span className="font-mono text-[9px] tracking-[.12em] text-muted">TARGET ROLE</span>
              <span className="mt-1.5 block font-display text-sm font-semibold text-white">
                {getRoleLabel(analysis.targetRole)}
              </span>
            </div>
          </div>

          <section className="mt-8 grid gap-4 lg:grid-cols-2">
            <ScoreCard analysis={analysis} />
            <BreakdownCard analysis={analysis} />
          </section>

          {analysis.sources && (
            <aside className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 rounded-2xl border border-line bg-white/[.02] px-4 py-3 text-xs text-muted">
              <span className="font-mono text-[9px] tracking-[.12em] text-lilac">EVIDENCE REVIEWED</span>
              <a
                className="inline-flex items-center gap-1 text-white transition hover:text-mint"
                href={`https://github.com/${encodeURIComponent(analysis.sources.githubUser)}`}
                target="_blank"
                rel="noreferrer"
              >
                @{analysis.sources.githubUser}
                <ArrowUpRight size={12} />
              </a>
              <span>{analysis.sources.repositoriesReviewed} public repositories</span>
              <span>{analysis.sources.originalRepositories ?? 0} non-fork repositories</span>
              <span>{analysis.sources.deepScannedRepositories ?? 0} deeply scanned (limit {analysis.sources.deepScanLimit ?? 0})</span>
              {analysis.sources.githubAccountCreatedAt && <span>Account created {analysis.sources.githubAccountCreatedAt.slice(0, 10)}</span>}
              <span>{analysis.sources.accountAttributedRepositories ?? 0} repos have commits GitHub attributes to this account</span>
              <span>{analysis.sources.accountAttributedCommits ?? 0} total attributed commits across scanned projects</span>
              <span>{analysis.sources.signedCommitCount ?? 0} sampled commits with GitHub-verified signatures</span>
              {analysis.sources.publicActivity?.available && (
                <span>
                  Recent public activity: {analysis.sources.publicActivity.pushedCommits} pushed commits, {analysis.sources.publicActivity.pullRequestsMerged} merged PRs across {analysis.sources.publicActivity.eventsReviewed} events
                </span>
              )}
              {analysis.sources.linkedinSignals.provided && <span>LinkedIn text signals included</span>}
              {analysis.sources.deepScanErrors > 0 && <span>Some detailed repository data could not be fetched</span>}
              <p className="basis-full border-t border-white/[.07] pt-3 text-[11px] leading-5 text-muted">
                Contributor totals can lag, the event feed is only a recent sample, and line changes are sampled from at most two commits. Code copying is not checked against all GitHub repositories. The score is capped at 85 because this scan cannot confirm profile ownership or code originality.
              </p>
            </aside>
          )}

          {analysis.sources?.projects?.length ? (
            <details className="mt-3 rounded-2xl border border-line bg-white/[.02]">
              <summary className="cursor-pointer px-4 py-3 text-xs font-semibold text-white marker:text-lilac">
                Inspect project evidence ({analysis.sources.projects.length} repositories)
              </summary>
              <div className="grid gap-3 border-t border-line p-3 sm:grid-cols-2">
                {analysis.sources.projects.map((project) => (
                  <article className="rounded-xl border border-line bg-[#101520]/80 p-4" key={project.name}>
                    <a className="inline-flex items-center gap-1 text-sm font-semibold text-white hover:text-mint" href={project.url} target="_blank" rel="noreferrer">
                      {project.name}<ArrowUpRight size={13} />
                    </a>
                    <p className="mt-2 text-xs leading-5 text-muted">{project.description || "No repository description."}</p>
                    <div className="mt-3 flex flex-wrap gap-2 text-[10px] text-muted">
                      {project.languages.length > 0 && <span>{project.languages.join(", ")}</span>}
                      <span>{project.accountAttributedCommits} account-attributed commits in GitHub's contributor summary</span>
                      <span>{Math.round(project.accountContributionShare * 100)}% account share among linked contributor commits</span>
                      <span>{project.totalContributors} linked contributors</span>
                      <span>{project.sampledAccountAttributedCommits}{project.commitCountCapped ? "+" : ""} commits sampled</span>
                      {project.signedCommits > 0 && <span>{project.signedCommits} GitHub-verified signatures</span>}
                      {project.sampleCommitFilesChanged > 0 && <span>Latest sample: +{project.sampleCommitAdditions} / −{project.sampleCommitDeletions} lines across {project.sampleCommitFilesChanged} files</span>}
                    </div>
                    {project.sampleCommitUrls.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-x-3 gap-y-1">
                        {project.sampleCommitUrls.map((url) => (
                          <a className="text-[10px] text-lilac hover:text-mint" href={url} key={url} target="_blank" rel="noreferrer">View commit</a>
                        ))}
                      </div>
                    )}
                  </article>
                ))}
              </div>
            </details>
          ) : null}

          <section className="mt-14">
            <SectionTitle
              eyebrow="WHAT YOUR PROFILE SHOWS"
              title="Skills & evidence"
              note={`${analysis.skills.length} signals`}
              icon={<BadgeCheck size={18} />}
            />
            {analysis.skills.length ? (
              <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
                {analysis.skills.map((skill, index) => (
                  <SkillCard skill={skill} key={`${skill.name}-${index}`} />
                ))}
              </div>
            ) : (
              <EmptySection message="No skill evidence was returned for this analysis." />
            )}
          </section>

          <section className="mt-14">
            <SectionTitle
              eyebrow="ROOM TO GROW"
              title="Your next opportunities"
              note={`${analysis.gaps.length} focus ${
                analysis.gaps.length === 1 ? "area" : "areas"
              }`}
              icon={<Lightbulb size={18} />}
            />
            {analysis.gaps.length ? (
              <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {analysis.gaps.map((gap, index) => (
                  <GapCard gap={gap} key={`${gap.name}-${index}`} />
                ))}
              </div>
            ) : (
              <EmptySection message="No priority gaps were identified." />
            )}
          </section>

          <section className="mt-14">
            <SectionTitle
              eyebrow="WHERE YOU COULD GO"
              title="Role alignment"
              note="Based on your current evidence"
              icon={<Target size={18} />}
            />
            {analysis.roles.length ? (
              <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {analysis.roles.map((role, index) => (
                  <RoleCard role={role} key={`${role.name}-${index}`} />
                ))}
              </div>
            ) : (
              <EmptySection message="No role matches were returned." />
            )}
          </section>

          <section className="mt-14">
            <SectionTitle
              eyebrow="MAKE IT HAPPEN"
              title="A roadmap for what’s next"
              note={`${analysis.roadmap.length} ${
                analysis.roadmap.length === 1 ? "step" : "steps"
              }`}
              icon={<Rocket size={18} />}
            />
            {analysis.roadmap.length ? (
              <div className="mt-5 grid gap-3 md:grid-cols-2">
                {analysis.roadmap.map((step, index) => (
                  <RoadmapCard step={step} index={index} key={`${step.title}-${index}`} />
                ))}
              </div>
            ) : (
              <EmptySection message="No roadmap steps were returned." />
            )}
          </section>

          <section className="mt-14 flex flex-col gap-5 rounded-3xl border border-lilac/20 bg-gradient-to-br from-[#17172a] via-[#141827] to-[#111922] p-6 sm:flex-row sm:items-center sm:justify-between sm:p-8">
            <div>
              <Eyebrow>KEEP BUILDING</Eyebrow>
              <h2 className="mt-3 font-display text-2xl font-semibold tracking-[-.05em] text-white">
                Your score is a starting point.
              </h2>
              <p className="mt-2 max-w-xl text-sm leading-6 text-muted">
                Add new work, make your experience visible, and come back to
                see how far you&apos;ve moved.
              </p>
            </div>
            <Link
              className="inline-flex min-h-11 shrink-0 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-[#9a8dff] to-[#7362eb] px-4 text-sm font-bold text-white transition hover:-translate-y-0.5"
              href="/analyze"
            >
              Run another analysis
              <ArrowRight size={16} />
            </Link>
          </section>
        </main>
      ) : (
        <main className="mx-auto grid min-h-[70vh] max-w-2xl place-items-center px-5 py-16 text-center">
          <div>
            <span className="mx-auto grid size-14 place-items-center rounded-2xl border border-lilac/20 bg-lilac/[.08] text-lilac">
              <CircleHelp size={23} />
            </span>
            <Eyebrow>{loadError ? "REPORT NEEDS A REFRESH" : "YOUR STORY STARTS HERE"}</Eyebrow>
            <h1 className="mt-4 font-display text-3xl font-semibold tracking-[-.06em] text-white">
              {loadError ? "Let’s make a fresh snapshot." : "Your report is waiting."}
            </h1>
            <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-muted">
              {loadError || "Share your resume and a target role to see how your experience lines up."}
            </p>
            <Link
              className="mt-6 inline-flex min-h-11 items-center gap-2 rounded-xl bg-gradient-to-r from-[#9a8dff] to-[#7362eb] px-5 text-sm font-bold text-white"
              href="/analyze"
            >
              Start an analysis
              <ArrowRight size={16} />
            </Link>
          </div>
        </main>
      )}
      <div className="report-footer">
        <SiteFooter />
      </div>
    </>
  );
}

function ScoreCard({ analysis }: { analysis: CareerAnalysis }) {
  const score = percentage(analysis.score);
  const circumference = 2 * Math.PI * 76;
  const offset = circumference * (1 - score / 100);
  const scoreDescription =
    analysis.explanation ??
    "Your profile has been measured against the evidence and requirements for this role.";

  return (
    <article className="rounded-3xl border border-line bg-[radial-gradient(ellipse_at_50%_0%,rgba(139,124,255,.1),transparent_55%),linear-gradient(145deg,#141a29,#0e131f)] p-6 sm:p-8">
      <div className="flex items-start justify-between gap-4">
        <div>
          <Eyebrow>ROLE FIT FROM PUBLIC SIGNALS</Eyebrow>
          <h2 className="mt-2 font-display text-lg font-semibold text-white">Evidence score</h2>
        </div>
        <span className="rounded-full border border-mint/15 bg-mint/[.07] px-3 py-1 text-xs font-semibold text-mint">
          {analysis.scoreStatus ?? "Your snapshot"}
        </span>
      </div>
      <div className="my-8 flex justify-center">
        <div
          className="relative grid size-44 place-items-center"
          role="img"
          aria-label={`Public evidence score: ${score} out of 100`}
        >
          <svg className="absolute inset-0 size-full -rotate-90" viewBox="0 0 180 180" aria-hidden="true">
            <circle cx="90" cy="90" r="76" fill="none" stroke="rgba(255,255,255,.08)" strokeWidth="8" />
            <circle
              cx="90"
              cy="90"
              r="76"
              fill="none"
              stroke="#a899ff"
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              className="transition-[stroke-dashoffset] duration-1000"
            />
          </svg>
          <div className="text-center">
            <div className="font-display text-5xl font-semibold tracking-[-.075em] text-white">{score}</div>
            <div className="font-mono text-[10px] text-muted">OUT OF 100</div>
          </div>
        </div>
      </div>
      <div className="border-t border-white/[.08] pt-5">
        <p className="font-display text-sm font-semibold text-white">
          {score >= 80
            ? "Strong momentum."
            : score >= 60
              ? "A solid foundation."
              : "A starting point to build from."}
        </p>
        <p className="mt-2 text-xs leading-6 text-muted">{scoreDescription}</p>
      </div>
    </article>
  );
}

function BreakdownCard({ analysis }: { analysis: CareerAnalysis }) {
  return (
    <article className="rounded-3xl border border-line bg-gradient-to-br from-[#141a29]/95 to-[#0e131f]/95 p-6 sm:p-8">
      <Eyebrow>WHAT SHAPES YOUR SCORE</Eyebrow>
      <h2 className="mt-2 font-display text-lg font-semibold text-white">The details behind it</h2>
      <div className="mt-8 space-y-5">
        {breakdownRows.map(({ key, label }) => {
          const value = percentage(analysis.breakdown?.[key] ?? 0);
          return (
            <div key={key}>
              <div className="mb-2 flex justify-between gap-4 text-xs">
                <span className="text-muted">{label}</span>
                <span className="font-semibold text-white">{value}%</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-white/[.07]">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-[#7968e9] via-lilac to-mint transition-[width] duration-700"
                  style={{ width: `${value}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </article>
  );
}

function SkillCard({ skill }: { skill: Skill }) {
  const status = skill.status.toLowerCase();
  const signalFound = status === "signal";
  const observed = status === "observed";
  return (
    <article className="rounded-2xl border border-line bg-[#111724]/90 p-4 transition hover:-translate-y-0.5 hover:border-lilac/30">
      <div className="flex items-center justify-between gap-3">
        <h3 className="font-display text-sm font-semibold text-white">{skill.name}</h3>
        <span
          className={`size-2 rounded-full ${
          signalFound ? "bg-mint" : observed ? "bg-[#f6c86a]" : "bg-rose-400"
          }`}
        />
      </div>
      <p
        className={`mt-3 font-mono text-[9px] tracking-[.1em] ${
          signalFound ? "text-mint" : observed ? "text-[#f6c86a]" : "text-rose-300"
        }`}
      >
        {signalFound ? "RESUME + REPO SIGNAL" : observed ? "REPO SIGNAL" : "NEEDS EVIDENCE"}
      </p>
      <p className="mt-2 text-xs leading-5 text-muted">{skill.evidence}</p>
    </article>
  );
}

function GapCard({ gap }: { gap: SkillGap }) {
  return (
    <article className="rounded-2xl border border-line bg-gradient-to-br from-[#141a29]/90 to-[#101520]/90 p-5">
      <span className="inline-flex items-center gap-1.5 rounded-full border border-[#f6c86a]/15 bg-[#f6c86a]/[.06] px-2.5 py-1 font-mono text-[9px] tracking-wide text-[#f6c86a]">
        <Lightbulb size={12} />
        {gap.priority}
      </span>
      <h3 className="mt-4 font-display text-lg font-semibold text-white">{gap.name}</h3>
      <p className="mt-2 text-sm leading-6 text-muted">{gap.description}</p>
      <div className="mt-5 flex items-start gap-2 border-t border-white/[.07] pt-4 text-xs leading-5 text-lilac">
        <ArrowRight className="mt-0.5 shrink-0" size={14} />
        {gap.action}
      </div>
    </article>
  );
}

function RoleCard({ role }: { role: RoleFit }) {
  const fit = percentage(role.fit);
  return (
    <article
      className={`rounded-2xl border bg-gradient-to-br p-5 ${
        role.primary
          ? "border-lilac/30 from-lilac/[.09] to-[#111724]"
          : "border-line from-[#141a29]/90 to-[#101520]/90"
      }`}
    >
      <div className="flex items-center justify-between gap-3">
        <h3 className="font-display text-base font-semibold text-white">{role.name}</h3>
        <span className="font-display text-lg font-semibold text-lilac">{fit}%</span>
      </div>
      <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-white/[.08]">
        <div
          className="h-full rounded-full bg-gradient-to-r from-lilac to-mint"
          style={{ width: `${fit}%` }}
        />
      </div>
      <p className="mt-3 text-xs leading-5 text-muted">{role.description}</p>
      {role.primary && (
        <span className="mt-4 inline-flex items-center gap-1.5 text-[10px] font-semibold text-mint">
          <BadgeCheck size={13} />
          Closest match
        </span>
      )}
    </article>
  );
}

function RoadmapCard({ step, index }: { step: RoadmapStep; index: number }) {
  return (
    <article className="flex gap-4 rounded-2xl border border-line bg-gradient-to-br from-[#141a29]/90 to-[#101520]/90 p-5">
      <span className="grid size-9 shrink-0 place-items-center rounded-xl border border-mint/20 bg-mint/[.06] font-display text-sm font-semibold text-mint">
        {String(index + 1).padStart(2, "0")}
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1 font-mono text-[9px] tracking-wide text-lilac">
          <span>{step.phase}</span>
          <span className="text-muted">·</span>
          <span className="text-muted">{step.duration}</span>
        </div>
        <h3 className="mt-2 font-display text-base font-semibold text-white">{step.title}</h3>
        <p className="mt-1.5 text-xs leading-5 text-muted">{step.description}</p>
        <div className="mt-3 inline-flex items-start gap-2 rounded-lg bg-white/[.035] px-3 py-2 text-xs text-white">
          <FileCheck2 className="mt-0.5 shrink-0 text-mint" size={13} />
          {step.task}
        </div>
      </div>
    </article>
  );
}

function SectionTitle({
  eyebrow,
  title,
  note,
  icon,
}: {
  eyebrow: string;
  title: string;
  note: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div className="flex items-center gap-3">
        <span className="grid size-10 place-items-center rounded-xl border border-lilac/20 bg-lilac/[.07] text-lilac">
          {icon}
        </span>
        <div>
          <Eyebrow>{eyebrow}</Eyebrow>
          <h2 className="mt-1 font-display text-xl font-semibold tracking-[-.04em] text-white sm:text-2xl">
            {title}
          </h2>
        </div>
      </div>
      <span className="text-xs text-muted">{note}</span>
    </div>
  );
}

function EmptySection({ message }: { message: string }) {
  return (
    <p className="mt-5 rounded-2xl border border-dashed border-line px-5 py-6 text-sm text-muted">
      {message}
    </p>
  );
}

function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <p className="font-mono text-[9px] tracking-[.13em] text-lilac">
      {children}
    </p>
  );
}

function percentage(value: number) {
  if (!Number.isFinite(value)) return 0;
  return Math.round(Math.max(0, Math.min(100, value)));
}

function isCareerAnalysis(value: unknown): value is CareerAnalysis {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Partial<CareerAnalysis>;
  return (
    typeof candidate.score === "number" &&
    typeof candidate.targetRole === "string" &&
    Array.isArray(candidate.skills) &&
    Array.isArray(candidate.gaps) &&
    Array.isArray(candidate.roles) &&
    Array.isArray(candidate.roadmap)
  );
}
