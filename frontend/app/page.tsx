import Link from "next/link";
import {
  ArrowDown,
  ArrowRight,
  ArrowUpRight,
  BadgeCheck,
  Braces,
  ChartNoAxesCombined,
  CircleCheck,
  Compass,
  FileSearch,
  ScanLine,
  Sparkles,
  Target,
} from "lucide-react";
import { SiteFooter, SiteHeader } from "@/components/site-header";

const features = [
  {
    number: "01",
    icon: BadgeCheck,
    title: "Proof over keywords",
    description:
      "Connect the skills you claim to visible work, real projects, and profile evidence.",
    tone: "mint",
  },
  {
    number: "02",
    icon: ChartNoAxesCombined,
    title: "A score you can unpack",
    description:
      "See what is driving your readiness score instead of getting another mystery number.",
    tone: "lilac",
  },
  {
    number: "03",
    icon: Target,
    title: "Gaps that make sense",
    description:
      "Find the capabilities your target role expects and where your evidence is still thin.",
    tone: "lilac",
  },
  {
    number: "04",
    icon: Compass,
    title: "A way forward",
    description:
      "Turn the insights into small, actionable milestones you can start working on today.",
    tone: "mint",
  },
];

const steps = [
  ["01", "Bring your story", "Add a resume, GitHub, portfolio, and the role you want."],
  ["02", "Check the evidence", "See how your real work lines up with your stated strengths."],
  ["03", "Make your next move", "Leave with a clear view of your fit and a roadmap to grow."],
];

export default function HomePage() {
  return (
    <>
      <SiteHeader />
      <main>
        <section className="hero-atmosphere relative mx-auto grid min-h-[680px] max-w-7xl items-center gap-16 overflow-hidden px-5 py-20 sm:px-8 lg:grid-cols-[1.05fr_.95fr] lg:py-28">
          <div className="relative z-10 max-w-2xl animate-[rise_.7s_ease-out_both]">
            <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-lilac/20 bg-lilac/[.07] px-3.5 py-2 font-mono text-[10px] tracking-[.12em] text-lilac">
              <span className="size-1.5 rounded-full bg-mint shadow-[0_0_12px_#75edcf]" />
              YOUR CAREER, WITH CLARITY
            </div>
            <h1 className="font-display text-[clamp(3.5rem,8vw,6.4rem)] font-semibold leading-[.98] tracking-[-.075em] text-white">
              Make your
              <br />
              next move
              <br />
              <span className="bg-gradient-to-r from-[#c7bbff] via-lilac to-mint bg-clip-text text-transparent">
                make sense.
              </span>
            </h1>
            <p className="mt-7 max-w-xl text-base leading-8 text-muted sm:text-lg">
              A clearer picture of how your experience matches the roles you
              want — grounded in your work, not just the words on your resume.
            </p>
            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <Link
                className="group inline-flex min-h-12 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-[#9a8dff] to-[#7362eb] px-6 text-sm font-bold text-white shadow-[0_12px_34px_rgba(111,95,229,.28)] transition hover:-translate-y-0.5 hover:shadow-[0_16px_38px_rgba(111,95,229,.4)]"
                href="/analyze"
              >
                See where you stand
                <ArrowRight
                  className="transition group-hover:translate-x-1"
                  size={17}
                />
              </Link>
              <a
                className="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl border border-line bg-white/[.025] px-6 text-sm font-semibold text-white transition hover:border-lilac/40 hover:bg-white/[.05]"
                href="#how-it-works"
              >
                How it works
                <ArrowDown size={15} />
              </a>
            </div>
            <div className="mt-10 flex flex-wrap gap-x-6 gap-y-3 text-xs text-muted">
              <span className="inline-flex items-center gap-2">
                <CircleCheck size={15} className="text-mint" />
                Evidence-led insights
              </span>
              <span className="inline-flex items-center gap-2">
                <CircleCheck size={15} className="text-mint" />
                A plan you can act on
              </span>
            </div>
          </div>

          <div className="relative mx-auto w-full max-w-[490px] animate-[rise_.8s_.12s_ease-out_both]">
            <div className="absolute -inset-12 rounded-full bg-lilac/[.09] blur-3xl" />
            <div className="absolute -right-3 -top-7 z-10 flex items-center gap-2 rounded-full border border-mint/20 bg-[#101923] px-3.5 py-2 text-[11px] font-semibold text-mint shadow-xl sm:right-0">
              <span className="size-1.5 rounded-full bg-mint" />
              YOUR PROFILE, DECODED
            </div>
            <div className="relative overflow-hidden rounded-[26px] border border-white/10 bg-gradient-to-br from-[#171e31] to-[#0c111d] p-6 shadow-[0_35px_100px_rgba(0,0,0,.4)] sm:p-8">
              <div className="absolute left-[12%] top-0 h-px w-1/2 bg-gradient-to-r from-transparent via-lilac/80 to-transparent" />
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-xs font-medium text-muted">
                  <ScanLine size={15} className="text-lilac" />
                  PUBLIC EVIDENCE SNAPSHOT
                </div>
                <span className="rounded-full border border-mint/15 bg-mint/[.08] px-2.5 py-1 text-[10px] font-semibold text-mint">
                  SAMPLE REPORT
                </span>
              </div>
              <div className="mt-8 flex items-center gap-6">
                <div className="relative grid size-32 shrink-0 place-items-center rounded-full sm:size-36">
                  <svg className="absolute inset-0 size-full -rotate-90" viewBox="0 0 144 144" aria-hidden="true">
                    <circle cx="72" cy="72" r="62" fill="none" stroke="rgba(255,255,255,.08)" strokeWidth="7" />
                    <circle
                      cx="72"
                      cy="72"
                      r="62"
                      fill="none"
                      stroke="url(#readiness-gradient)"
                      strokeWidth="7"
                      strokeLinecap="round"
                      strokeDasharray="390"
                      strokeDashoffset="86"
                    />
                    <defs>
                      <linearGradient id="readiness-gradient" x1="0" y1="0" x2="144" y2="144">
                        <stop stopColor="#a899ff" />
                        <stop offset="1" stopColor="#75edcf" />
                      </linearGradient>
                    </defs>
                  </svg>
                  <div className="text-center">
                    <div className="font-display text-4xl font-semibold tracking-[-.07em] text-white">78</div>
                    <div className="font-mono text-[10px] text-muted">OUT OF 100</div>
                  </div>
                </div>
                <div>
                  <p className="font-display text-lg font-semibold text-white">A solid foundation.</p>
                  <p className="mt-2 text-sm leading-6 text-muted">
                    Your strengths are showing. Here&apos;s what to build next.
                  </p>
                  <div className="mt-4 inline-flex items-center gap-1.5 text-xs font-semibold text-lilac">
                    Backend Developer
                    <ArrowUpRight size={13} />
                  </div>
                </div>
              </div>
              <div className="my-7 h-px bg-white/[.08]" />
              <div className="flex items-center justify-between text-xs">
                <span className="font-mono text-[10px] tracking-[.1em] text-muted">SKILL SIGNALS</span>
                <span className="text-muted">3 examples</span>
              </div>
              <div className="mt-3 space-y-2">
                <SkillSignal name="Python" status="Signal found" value={92} />
                <SkillSignal name="SQL" status="Signal found" value={72} />
                <SkillSignal name="Docker" status="Opportunity" value={38} />
              </div>
            </div>
            <div className="absolute -bottom-5 -left-4 flex items-center gap-3 rounded-2xl border border-white/10 bg-[#121826]/95 px-4 py-3 shadow-2xl backdrop-blur-xl sm:-left-8">
              <span className="grid size-9 place-items-center rounded-xl bg-lilac/10 text-lilac">
                <Sparkles size={17} />
              </span>
              <div>
                <div className="text-xs font-semibold text-white">Your next step</div>
                <div className="mt-0.5 text-[11px] text-muted">Build on what you know</div>
              </div>
            </div>
          </div>
        </section>

        <section className="border-y border-line bg-[#0d111b]/65">
          <div className="mx-auto grid max-w-7xl gap-5 px-5 py-5 text-sm sm:grid-cols-3 sm:px-8">
            <TrustSignal icon={<FileSearch size={17} />} label="Evidence, not guesswork" />
            <TrustSignal icon={<Braces size={17} />} label="Your actual projects" />
            <TrustSignal icon={<Target size={17} />} label="Your target role" />
          </div>
        </section>

        <section className="mx-auto max-w-7xl px-5 py-24 sm:px-8 sm:py-32" id="features">
          <div className="max-w-2xl">
            <Eyebrow>THE CAREERLENS DIFFERENCE</Eyebrow>
            <h2 className="mt-5 font-display text-4xl font-semibold tracking-[-.06em] text-white sm:text-5xl">
              More signal.
              <br />
              Less guesswork.
            </h2>
            <p className="mt-5 max-w-xl text-base leading-7 text-muted">
              Your next opportunity deserves more than a keyword scan. Get a
              practical read on the evidence you already have.
            </p>
          </div>
          <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {features.map(({ number, icon: Icon, title, description, tone }) => (
              <article
                className="group relative overflow-hidden rounded-2xl border border-line bg-gradient-to-br from-[#141a29]/90 to-[#0e121d]/80 p-6 transition duration-300 hover:-translate-y-1 hover:border-lilac/30"
                key={number}
              >
                <div className="flex items-center justify-between">
                  <span
                    className={`grid size-10 place-items-center rounded-xl border ${
                      tone === "mint"
                        ? "border-mint/20 bg-mint/[.08] text-mint"
                        : "border-lilac/20 bg-lilac/[.08] text-lilac"
                    }`}
                  >
                    <Icon size={18} />
                  </span>
                  <span className="font-mono text-[10px] text-muted">{number}</span>
                </div>
                <h3 className="mt-9 font-display text-lg font-semibold tracking-[-.03em] text-white">
                  {title}
                </h3>
                <p className="mt-3 text-sm leading-6 text-muted">{description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="border-y border-line bg-gradient-to-r from-[#101421]/90 via-[#111626]/70 to-[#101421]/90" id="how-it-works">
          <div className="mx-auto grid max-w-7xl gap-12 px-5 py-24 sm:px-8 lg:grid-cols-[.8fr_1.2fr] lg:py-28">
            <div>
              <Eyebrow>THREE STEPS. ONE CLEARER PICTURE.</Eyebrow>
              <h2 className="mt-5 max-w-md font-display text-4xl font-semibold leading-tight tracking-[-.06em] text-white sm:text-5xl">
                From your experience to your next move.
              </h2>
            </div>
            <div className="divide-y divide-white/[.08]">
              {steps.map(([number, title, description]) => (
                <div className="grid grid-cols-[48px_1fr] gap-4 py-6 first:pt-0 last:pb-0 sm:grid-cols-[60px_1fr]" key={number}>
                  <span className="font-mono text-xs text-mint">{number}</span>
                  <div>
                    <h3 className="font-display text-lg font-semibold text-white">{title}</h3>
                    <p className="mt-2 text-sm leading-6 text-muted">{description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-7xl px-5 py-24 sm:px-8 sm:py-28">
          <div className="relative overflow-hidden rounded-[28px] border border-lilac/20 bg-gradient-to-br from-[#17172a] via-[#141827] to-[#111922] px-6 py-12 text-center sm:px-12 sm:py-16">
            <div className="absolute -right-10 -top-28 size-80 rounded-full bg-lilac/[.12] blur-3xl" />
            <div className="absolute -bottom-36 -left-10 size-72 rounded-full bg-mint/[.07] blur-3xl" />
            <div className="relative mx-auto max-w-2xl">
              <Eyebrow>YOUR NEXT CHAPTER STARTS HERE</Eyebrow>
              <h2 className="mt-5 font-display text-4xl font-semibold tracking-[-.06em] text-white sm:text-5xl">
                Get to know the strength of your story.
              </h2>
              <p className="mx-auto mt-4 max-w-xl text-sm leading-7 text-muted sm:text-base">
                Bring your resume and the work you&apos;re proud of. We&apos;ll
                help you see what&apos;s next.
              </p>
              <Link
                className="mt-8 inline-flex min-h-12 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-[#9a8dff] to-[#7362eb] px-6 text-sm font-bold text-white transition hover:-translate-y-0.5"
                href="/analyze"
              >
                Start your analysis
                <ArrowRight size={17} />
              </Link>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}

function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <p className="inline-flex items-center gap-2 font-mono text-[10px] tracking-[.13em] text-lilac">
      <span className="size-1 rounded-full bg-mint" />
      {children}
    </p>
  );
}

function TrustSignal({
  icon,
  label,
}: {
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <div className="flex items-center justify-center gap-2.5 text-muted sm:justify-start">
      <span className="text-mint">{icon}</span>
      {label}
    </div>
  );
}

function SkillSignal({
  name,
  status,
  value,
}: {
  name: string;
  status: string;
  value: number;
}) {
  return (
    <div className="grid grid-cols-[1fr_auto] items-center gap-x-4 rounded-xl bg-white/[.025] px-3.5 py-2.5">
      <div className="flex items-center justify-between gap-3 text-xs">
        <span className="font-medium text-white">{name}</span>
        <span
          className={
            status === "Signal found"
              ? "text-mint"
              : status === "Observed"
                ? "text-[#f6c86a]"
                : "text-muted"
          }
        >
          {status}
        </span>
      </div>
      <div className="col-span-2 mt-2 h-1 overflow-hidden rounded-full bg-white/[.07]">
        <div
          className="h-full rounded-full bg-gradient-to-r from-lilac to-mint"
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}
