"use client";

import { useRef, useState, type DragEvent, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  BriefcaseBusiness,
  CodeXml,
  FileText,
  LoaderCircle,
  LockKeyhole,
  Upload,
  X,
} from "lucide-react";
import type { AnalysisResponse } from "@/lib/types";
import { roles } from "@/lib/roles";

const MAX_FILE_SIZE = 10 * 1024 * 1024;

type LinkFields = {
  github: string;
};

export function AnalyzeForm() {
  const router = useRouter();
  const fileInput = useRef<HTMLInputElement>(null);
  const [resume, setResume] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [targetRole, setTargetRole] = useState("");
  const [links, setLinks] = useState<LinkFields>({
    github: "",
  });
  const [linkedinText, setLinkedinText] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function chooseFile(file?: File) {
    setError("");
    if (!file) return;

    if (!/\.(pdf|docx)$/i.test(file.name)) {
      setResume(null);
      setError("Please choose a PDF or DOCX resume.");
      if (fileInput.current) fileInput.current.value = "";
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setResume(null);
      setError("Your resume must be smaller than 10 MB.");
      if (fileInput.current) fileInput.current.value = "";
      return;
    }

    setResume(file);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    chooseFile(event.dataTransfer.files[0]);
  }

  function updateLink(field: keyof LinkFields, value: string) {
    setLinks((current) => ({ ...current, [field]: value }));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (!resume) {
      setError("Add your resume to get started.");
      fileInput.current?.focus();
      return;
    }

    if (!targetRole) {
      setError("Choose the role you’re working toward.");
      document.getElementById("targetRole")?.focus();
      return;
    }

    if (!links.github.trim()) {
      setError("Add your GitHub profile so we can check real project evidence.");
      document.getElementById("github")?.focus();
      return;
    }

    for (const [label, value] of Object.entries(links)) {
      if (!value.trim()) continue;
      try {
        const url = new URL(value);
        if (url.protocol !== "http:" && url.protocol !== "https:") {
          throw new Error("Invalid protocol");
        }
      } catch {
        setError(`Add a valid https:// address for your ${label} link.`);
        document.getElementById(label)?.focus();
        return;
      }
    }

    if (links.github.trim()) {
      try {
        const githubUrl = new URL(links.github);
        if (!["github.com", "www.github.com"].includes(githubUrl.hostname)) {
          setError("Your GitHub link should be on github.com.");
          document.getElementById("github")?.focus();
          return;
        }
      } catch {
        setError("Add a valid https:// address for your GitHub link.");
        document.getElementById("github")?.focus();
        return;
      }
    }

    setSubmitting(true);
    try {
      const formData = new FormData();
      formData.append("resume", resume);
      formData.append("github", links.github.trim());
      formData.append("linkedinText", linkedinText.trim());
      formData.append("targetRole", targetRole);

      const response = await fetch("/api/analyze", {
        method: "POST",
        body: formData,
      });
      const result = (await response.json()) as AnalysisResponse;

      if (!response.ok || !result.success || !result.analysis) {
        throw new Error(
          result.error || "We couldn’t analyze that profile. Please try again.",
        );
      }

      window.sessionStorage.setItem(
        "careerLensAnalysis",
        JSON.stringify(result.analysis),
      );
      router.push("/analyzing");
    } catch (submissionError) {
      setSubmitting(false);
      setError(
        submissionError instanceof Error
          ? submissionError.message
          : "Couldn’t reach CareerLens. Check your connection and try again.",
      );
    }
  }

  return (
    <form
      className="overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-[#141a29]/95 to-[#0e121d]/95 shadow-[0_30px_90px_rgba(0,0,0,.23)]"
      onSubmit={submit}
      noValidate
    >
      <div className="divide-y divide-white/[.08] px-5 sm:px-9">
        <section className="py-7 sm:py-9">
          <SectionHeading number="01" title="Your resume" description="Start with the story you already have." />
          <div
            className={`mt-6 flex min-h-32 items-center gap-4 rounded-2xl border border-dashed px-5 py-5 transition sm:px-6 ${
              dragging
                ? "border-mint/70 bg-mint/[.06]"
                : resume
                  ? "border-mint/35 bg-mint/[.035]"
                  : "border-lilac/25 bg-lilac/[.025] hover:border-lilac/50 hover:bg-lilac/[.05]"
            }`}
            onDragOver={(event) => {
              event.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
          >
            <label
              className="flex min-w-0 flex-1 cursor-pointer items-center gap-4"
              htmlFor="resume"
            >
              <span className="grid size-12 shrink-0 place-items-center rounded-2xl border border-lilac/20 bg-lilac/[.08] text-lilac">
                {resume ? <FileText size={21} /> : <Upload size={21} />}
              </span>
              <span className="min-w-0 flex-1">
                <span className="block truncate text-sm font-semibold text-white">
                  {resume?.name ?? "Drop your resume here"}
                </span>
                <span className="mt-1 block text-xs text-muted">
                  {resume
                    ? `${formatFileSize(resume.size)} · Ready to analyze`
                    : "PDF or DOCX · Up to 10 MB"}
                </span>
              </span>
              {!resume && (
                <span className="shrink-0 rounded-lg border border-line px-3 py-2 text-xs font-semibold text-white">
                  Browse files
                </span>
              )}
              <input
                ref={fileInput}
                className="sr-only"
                id="resume"
                name="resume"
                type="file"
                accept=".pdf,.docx"
                aria-describedby={error ? "form-error" : "resume-hint"}
                onChange={(event) => chooseFile(event.currentTarget.files?.[0])}
              />
            </label>
            {resume && (
              <button
                aria-label="Remove resume"
                className="grid size-9 shrink-0 place-items-center rounded-xl text-muted transition hover:bg-white/[.07] hover:text-white"
                onClick={() => {
                  setResume(null);
                  if (fileInput.current) fileInput.current.value = "";
                }}
                type="button"
              >
                <X size={17} />
              </button>
            )}
          </div>
          <p className="mt-3 text-xs text-muted" id="resume-hint">
            A recent resume gives us the best starting point.
          </p>
        </section>

        <section className="py-7 sm:py-9">
          <SectionHeading number="02" title="Show us your work" description="GitHub is required to compare resume claims with public project signals." />
          <div className="mt-6 grid gap-4">
            <ProfileLinkField
              id="github"
              label="GitHub"
              hint="We inspect the profile, original repositories, README files, languages, and GitHub-attributed commits."
              placeholder="https://github.com/you"
              value={links.github}
              onChange={(value) => updateLink("github", value)}
              icon={<CodeXml size={16} />}
              required
            />
          </div>
          <label className="mt-5 block" htmlFor="linkedinText">
            <span className="mb-2 flex items-center gap-2 text-xs font-semibold text-white">
              <BriefcaseBusiness className="text-lilac" size={16} />
              LinkedIn activity <span className="ml-auto font-normal text-muted">Optional</span>
            </span>
            <textarea
              className="min-h-28 w-full resize-y rounded-xl border border-line bg-[#0a0e18]/90 px-3.5 py-3 text-sm leading-6 text-white outline-none transition placeholder:text-[#667087] focus:border-lilac/50 focus:ring-4 focus:ring-lilac/10"
              id="linkedinText"
              name="linkedinText"
              maxLength={10000}
              placeholder="Paste a few public milestones or recommendations. Don't include private contact details."
              value={linkedinText}
              onChange={(event) => setLinkedinText(event.target.value)}
            />
            <span className="mt-1.5 block text-[11px] text-muted">
              We only use this text to look for work milestones and peer endorsements.
            </span>
          </label>
        </section>

        <section className="py-7 sm:py-9">
          <SectionHeading number="03" title="Choose your direction" description="Pick the role you’re building toward." />
          <label className="mt-6 block" htmlFor="targetRole">
            <span className="mb-2 block text-xs font-semibold text-white">Target role</span>
            <select
              className="min-h-12 w-full appearance-none rounded-xl border border-line bg-[#0a0e18] px-4 text-sm text-white outline-none transition focus:border-lilac/50 focus:ring-4 focus:ring-lilac/10"
              id="targetRole"
              name="targetRole"
              value={targetRole}
              onChange={(event) => setTargetRole(event.target.value)}
              required
            >
              <option value="" disabled>
                Select a role
              </option>
              {roles.map((role) => (
                <option key={role.value} value={role.value}>
                  {role.label}
                </option>
              ))}
            </select>
          </label>
        </section>
      </div>

      <div className="border-t border-white/[.08] bg-white/[.02] px-5 py-5 sm:px-9">
        {error && (
          <p
            className="mb-4 rounded-xl border border-rose-400/20 bg-rose-400/[.07] px-4 py-3 text-sm text-rose-200"
            id="form-error"
            role="alert"
          >
            {error}
          </p>
        )}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <p className="flex items-center gap-2 text-xs leading-5 text-muted">
            <LockKeyhole className="shrink-0 text-mint" size={14} />
            Your resume is only used for this analysis.
          </p>
          <button
            className="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-[#9a8dff] to-[#7362eb] px-5 text-sm font-bold text-white shadow-[0_10px_28px_rgba(111,95,229,.24)] transition hover:-translate-y-0.5 hover:shadow-[0_14px_34px_rgba(111,95,229,.36)] disabled:cursor-wait disabled:opacity-70"
            disabled={submitting}
            type="submit"
          >
            {submitting ? (
              <>
                <LoaderCircle className="animate-spin" size={17} />
                Reading your profile…
              </>
            ) : (
              <>
                Build my career snapshot
                <ArrowRight size={17} />
              </>
            )}
          </button>
        </div>
      </div>
    </form>
  );
}

function SectionHeading({
  number,
  title,
  description,
}: {
  number: string;
  title: string;
  description: string;
}) {
  return (
    <div className="flex items-start gap-4">
      <span className="grid size-9 shrink-0 place-items-center rounded-xl border border-mint/15 bg-mint/[.055] font-mono text-[10px] text-mint">
        {number}
      </span>
      <div>
        <h2 className="font-display text-lg font-semibold tracking-[-.03em] text-white">
          {title}
        </h2>
        <p className="mt-1 text-sm text-muted">{description}</p>
      </div>
    </div>
  );
}

function ProfileLinkField({
  id,
  label,
  hint,
  placeholder,
  value,
  onChange,
  icon,
  required = false,
}: {
  id: keyof LinkFields;
  label: string;
  hint: string;
  placeholder: string;
  value: string;
  onChange: (value: string) => void;
  icon: React.ReactNode;
  required?: boolean;
}) {
  return (
    <label className="block" htmlFor={id}>
      <span className="mb-2 flex items-center gap-2 text-xs font-semibold text-white">
        <span className="text-lilac">{icon}</span>
        {label}
        <span className="ml-auto font-normal text-muted">{required ? "Required" : "Optional"}</span>
      </span>
      <input
        className="min-h-11 w-full rounded-xl border border-line bg-[#0a0e18]/90 px-3.5 text-sm text-white outline-none transition placeholder:text-[#667087] focus:border-lilac/50 focus:ring-4 focus:ring-lilac/10"
        id={id}
        name={id}
        type="url"
        placeholder={placeholder}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        autoComplete="url"
        required={required}
      />
      <span className="mt-1.5 block text-[11px] text-muted">{hint}</span>
    </label>
  );
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
