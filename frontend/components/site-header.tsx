import Link from "next/link";
import { ArrowUpRight, ChevronDown, Menu, ScanLine } from "lucide-react";

export function Brand() {
  return (
    <Link
      className="inline-flex items-center gap-2.5 font-display text-[21px] font-bold tracking-[-1.1px]"
      href="/"
      aria-label="CareerLens home"
    >
      <span className="grid size-8 place-items-center rounded-[11px] border border-lilac/40 bg-lilac/15 text-lilac shadow-[0_0_24px_rgba(139,124,255,.16)]">
        <ScanLine size={17} strokeWidth={2.2} />
      </span>
      CareerLens
    </Link>
  );
}

export function SiteHeader({
  compact = false,
}: {
  compact?: boolean;
}) {
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-[#090b12]/80 backdrop-blur-xl">
      <div className="mx-auto flex min-h-[72px] max-w-7xl items-center justify-between gap-4 px-5 sm:px-8">
        <Brand />
        {!compact && (
          <>
            <nav className="hidden items-center gap-8 text-sm text-muted md:flex">
              <Link className="transition hover:text-white" href="/#features">
                Features
              </Link>
              <Link className="transition hover:text-white" href="/#how-it-works">
                How it works
              </Link>
            </nav>
            <details className="group relative md:hidden">
              <summary
                aria-label="Open site navigation"
                className="grid size-10 cursor-pointer list-none place-items-center rounded-xl border border-line bg-white/[.025] text-white [&::-webkit-details-marker]:hidden"
              >
                <Menu className="group-open:hidden" size={18} />
                <ChevronDown className="hidden group-open:block" size={17} />
              </summary>
              <nav className="absolute right-0 top-12 z-40 grid w-48 animate-[menu-in_.16s_ease-out_both] gap-1 rounded-2xl border border-line bg-[#101522]/95 p-2 text-sm text-muted shadow-2xl backdrop-blur-xl">
                <Link className="rounded-xl px-3 py-2.5 transition hover:bg-white/[.05] hover:text-white" href="/#features">
                  Features
                </Link>
                <Link className="rounded-xl px-3 py-2.5 transition hover:bg-white/[.05] hover:text-white" href="/#how-it-works">
                  How it works
                </Link>
              </nav>
            </details>
          </>
        )}
        <Link
          className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-lilac/30 bg-lilac/10 px-3 text-xs font-semibold text-white transition hover:-translate-y-0.5 hover:border-lilac/60 hover:bg-lilac/20 sm:px-4 sm:text-sm"
          href="/analyze"
        >
          <span className="min-[380px]:hidden">Analyze</span>
          <span className="hidden min-[380px]:inline">Analyze profile</span>
          <ArrowUpRight className="hidden min-[380px]:block" size={15} />
        </Link>
      </div>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="border-t border-line">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-5 py-8 text-sm text-muted sm:flex-row sm:items-center sm:justify-between sm:px-8">
        <Brand />
        <p>Make your next move with evidence.</p>
        <p>CareerLens · Career readiness, in focus.</p>
      </div>
    </footer>
  );
}
