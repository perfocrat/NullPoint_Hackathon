"""
app.py  --  CareerLens AI executive dashboard (Streamlit)
=========================================================
Run:  streamlit run app.py
"""
from __future__ import annotations

import io
import math
import os
import time
from typing import Any, Dict, List

import streamlit as st

from portfolio_analyzer import (DIMENSIONS, TOLERANCE, TRACK_BASELINES, TRACK_TARGETS,
                                PortfolioAnalyzer, compute_text_properties)

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "market_latent_space.pth")

st.set_page_config(page_title="CareerLens AI", page_icon="🎯", layout="wide")

SKILL_ROADMAP: Dict[str, str] = {
    "Python": "Publish 2 Python repos (a CLI tool and a small API). Set the repo language to Python and write a one-line description for each.",
    "PyTorch": "Build and push one PyTorch project (e.g. a small classifier or autoencoder). Put `pytorch` in the description and topics.",
    "C++": "Push one C++ project (data structures, a solver or a game loop) with a CMake/Makefile and a README.",
    "JavaScript": "Ship a JavaScript/TypeScript front-end or Node project and push it as a public repo.",
    "React": "Build a small React app, deploy it, and add `react` to the repo topics and the live URL to the homepage field.",
    "NodeJS": "Create a Node/Express REST API repo with a documented endpoint list; add `nodejs` to topics.",
    "Figma": "Link your Figma prototype in a repo README/homepage field and add `figma` / `ui-ux` topics to the repo that implements it.",
    "Docker": "Add a `Dockerfile` and `docker-compose.yml` to your best project, push it, and mention `docker` in the description.",
    "SQL": "Add a repo with a real schema (migrations or `.sql` files) using PostgreSQL/MySQL/SQLite; tag it `sql` / `database`.",
    "HTML": "Publish a hand-written HTML page or static site (GitHub Pages is free) and add `html` to topics.",
    "CSS": "Style a project with hand-written CSS/SCSS and push it; tag the repo `css`.",
    "Java": "Push one Java project (Spring Boot service or an OOP assignment cleaned up with tests).",
    "Git": "Make your work public on GitHub: commit regularly with meaningful messages and push at least two repos.",
    "AWS": "Deploy one project to AWS (EC2, S3 static site or Lambda) and record it in the description (`deployed on AWS`).",
    "FastAPI": "Wrap one of your models or scripts in a FastAPI service with `/docs`; add `fastapi` to topics.",
    "Django": "Build a small Django app (auth + CRUD) and push it; add `django` to topics.",
    "Tailwind": "Re-skin one front-end project with Tailwind CSS and add `tailwind` to the repo topics.",
    "Kubernetes": "Add Kubernetes manifests (Deployment + Service) or a Helm chart to a containerised project.",
    "CI_CD": "Add a `.github/workflows` pipeline (lint + tests + build) and mention `github actions` / `ci-cd` in the description.",
    "NoSQL": "Add a project using MongoDB, Redis or Firebase and tag it `mongodb` / `redis`.",
    "Linux": "Publish your dotfiles or a bash automation repo and tag it `linux` / `bash`.",
}

DIMENSION_TIPS: Dict[str, str] = {
    "consistency": "Push more finished repositories; aim for a steady cadence (one meaningful repo or major commit per month).",
    "tech_depth": "Use at least 4-6 different languages across projects (e.g. Python, JavaScript, SQL, Shell, CSS, C++).",
    "frameworks": "Build with recognised frameworks and name them in repo descriptions/topics (React, FastAPI, PyTorch, Django...).",
    "breadth": "Give every repo a clear name, a descriptive summary and topics so reviewers see the scope of your work.",
    "integrity": "Keep resume claims aligned with public project evidence; add a repository link for skills that are not currently visible.",
    "products": "Convert forks and tutorials into original projects; 8-10 original repos is a strong baseline.",
    "deployment": "Deploy your best 3-4 projects (Vercel, Render, Streamlit Cloud, AWS) and set the repo homepage to the live URL.",
    "collaboration": "Fork and contribute to open-source projects; open pull requests and keep forks that carry your changes.",
    "documentation": "Add a description to every repo and a README with setup, usage and screenshots.",
    "proximity": "Close the missing target-track skills above; proximity rises with each matching repository signal.",
    "gap": "Every missing baseline skill is one visible project signal away; start with the first item in this roadmap.",
    "ecosystem": "Make projects discoverable: good README, topics, a demo link; share them so others star or fork them.",
}


# --------------------------------------------------------------------------- #
# Cached resources
# --------------------------------------------------------------------------- #
@st.cache_resource(show_spinner=False)
def load_market_bundle(path: str):
    """Load the trained latent-space model once per server process (None if not trained yet)."""
    if not os.path.isfile(path):
        return None
    try:
        import torch
        from core_model import load_checkpoint
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model, tokenizer, extras = load_checkpoint(path, device)
        return model, tokenizer, extras, device
    except Exception as exc:  # corrupted / incompatible checkpoint must not crash the dashboard
        return {"error": str(exc)}


@st.cache_data(ttl=300, show_spinner=False)
def cached_live_analysis(resume_text: str, github_url: str, track: str, token: str, deep_scan: bool,
                         linkedin_text: str = "") -> Dict[str, Any]:
    """Runs portfolio_analyzer.py live; results are memoised in memory for 5 minutes so that
    re-renders do not burn the GitHub rate limit."""
    return PortfolioAnalyzer().post_analyze_candidate({
        "resume_text": resume_text, "github_url": github_url, "track": track,
        "github_token": token, "deep_scan": deep_scan, "linkedin_text": linkedin_text,
    })


def read_uploaded_resume(uploaded) -> str:
    raw = uploaded.getvalue()
    if uploaded.name.lower().endswith(".pdf"):
        try:
            from pypdf import PdfReader
            return "\n".join((page.extract_text() or "") for page in PdfReader(io.BytesIO(raw)).pages)
        except ImportError:
            st.warning("PDF support needs `pip install pypdf`. Paste the text instead.")
            return ""
    return raw.decode("utf-8", errors="ignore")


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #
def compute_readiness(metrics: Dict[str, Dict[str, Any]], track: str) -> Dict[str, Any]:
    """Balanced, normalised distance penalty over the 12 telemetry metrics.

    shortfall_i = max(0, target_i - value_i) / target_i      (0 = met, 1 = absent)
    distance    = 0.5 * RMS(shortfall) + 0.5 * mean(shortfall)
    readiness   = 100 * (1 - distance)
    Exceeding a target is never rewarded twice, and never penalised.
    """
    targets = TRACK_TARGETS[track]
    shortfalls: Dict[str, float] = {}
    for key, target in targets.items():
        shortfalls[key] = max(0.0, target - metrics[key]["value"]) / target
    values = list(shortfalls.values())
    rms = math.sqrt(sum(v * v for v in values) / len(values))
    mean = sum(values) / len(values)
    distance = 0.5 * rms + 0.5 * mean
    return {"score": max(0.0, min(100.0, 100.0 * (1.0 - distance))), "shortfalls": shortfalls}


def build_roadmap(result: Dict[str, Any], readiness: Dict[str, Any]) -> List[str]:
    steps: List[str] = []
    for skill in result["missing_track_skills"]:
        steps.append(f"**Prove {skill}** - {SKILL_ROADMAP.get(skill, 'Ship a public project that uses it.')}")
    for skill in result["unverified_claims"]:
        if skill in result["missing_track_skills"]:
            continue
        steps.append(f"**Back up or remove '{skill}' on your resume** - no GitHub evidence was found. "
                     f"{SKILL_ROADMAP.get(skill, '')}")
    targets = TRACK_TARGETS[result["track"]]
    weakest = sorted(
        (k for k, _ in DIMENSIONS if result["metrics"][k]["value"] < targets[k] - TOLERANCE
         and k not in ("gap", "proximity", "integrity")),
        key=lambda k: readiness["shortfalls"][k], reverse=True)
    for key in weakest[:3]:
        steps.append(f"**Lift {result['metrics'][key]['label']}** - {DIMENSION_TIPS[key]}")
    steps.append("**Re-run CareerLens AI** after pushing your changes. The analysis re-reads your live GitHub data "
                 "(cached for up to 5 minutes).")
    return steps


# --------------------------------------------------------------------------- #
# UI
# --------------------------------------------------------------------------- #
def main() -> None:
    st.title("🎯 CareerLens AI")
    st.caption("Role-fit signals from your resume and live public GitHub data across 12 measured dimensions.")
    st.info("GitHub commit attribution and signed-commit status are useful signals, but they do not prove who controls the profile or who originally wrote the code.")

    with st.sidebar:
        st.header("GitHub API")
        token = st.text_input("Personal access token (optional)", type="password",
                              value=os.environ.get("GITHUB_TOKEN", ""),
                              help="Raises the public limit from 60 to 5,000 requests/hour. "
                                   "It is only sent to api.github.com and is never stored.")
        deep_scan = st.checkbox("Detailed repository scan", value=True,
                                help="Reads language breakdowns and READMEs, and samples up to 100 commits attributed to the profile in each of 12 non-fork repositories.")
        st.markdown("---")
        st.caption("Model: " + ("trained ✅" if os.path.isfile(MODEL_PATH) else "not trained yet - run `python train_market_engine.py`"))

    c1, c2 = st.columns([3, 2])
    with c1:
        resume_text = st.text_area("Resume text block", height=240,
                                   placeholder="Paste the full text of the resume here...")
        uploaded = st.file_uploader("...or drop a .txt / .md / .pdf resume", type=["txt", "md", "pdf"])
        if uploaded is not None and not resume_text.strip():
            resume_text = read_uploaded_resume(uploaded)
            st.caption(f"Loaded {len(resume_text):,} characters from {uploaded.name}")
        raw_linkedin_text = st.text_area(
            "Paste Candidate LinkedIn Public Activity Stream Text / Post Logs Here:", value="", height=120,
            placeholder="Paste recent posts, featured text, or written recommendations from your LinkedIn profile layout...")
    with c2:
        github_url = st.text_input("Public GitHub profile link", placeholder="https://github.com/username")
        track = st.selectbox("Target global track role", list(TRACK_BASELINES.keys()))
        st.caption("Baseline skills: " + ", ".join(TRACK_BASELINES[track]))
        run = st.button("🔍 Analyze candidate", type="primary", use_container_width=True)

    if run:
        if not resume_text.strip() or not github_url.strip():
            st.warning("Provide both the resume text and a GitHub profile link.")
        else:
            with st.spinner("Reading the live GitHub API..."):
                st.session_state["result"] = cached_live_analysis(resume_text, github_url, track, token, deep_scan,
                                                                    raw_linkedin_text)
                st.session_state["resume_text"] = resume_text

    result = st.session_state.get("result")
    if not result:
        return
    if not result.get("ok"):
        st.error(result.get("error", "Analysis failed."))
        return
    if result["track"] != track:
        st.info(f"Showing the result for '{result['track']}'. Press Analyze to re-score for '{track}'.")

    readiness = compute_readiness(result["metrics"], result["track"])
    meta = result["meta"]
    st.divider()
    left, right = st.columns([1, 1.35], gap="large")

    # ------------------------------ left ---------------------------------- #
    with left:
        st.metric("Job Readiness Match Score", f"{readiness['score']:.1f}%",
                  help="100 minus the balanced normalised distance to the target-track constraints.")
        st.progress(int(round(readiness["score"])))
        age = time.time() - meta["fetched_at"]
        m1, m2 = st.columns(2)
        m1.metric("Live API processing speed", f"{meta['latency_sec']:.2f} s")
        m2.metric("GitHub calls / repos read", f"{meta['api_calls']} / {meta['repos']}")
        remaining = meta["rate_remaining"]
        st.caption(f"@{result['username']} | fetched {age:.0f}s ago | "
                   + (f"rate limit left: {remaining}" if remaining is not None else "rate limit unknown")
                   + (" | authenticated" if meta["authenticated"] else " | unauthenticated (60/h)")
                   + (" | deep scan" if meta["deep_scan"] else ""))

        li = result.get("linkedin", {})
        if li.get("provided"):
            found = [f"{t} x{c}" for t, c in {**li["milestones"], **li["attestations"]}.items()]
            st.caption("LinkedIn signals parsed: " + (", ".join(found) if found else "none detected")
                       + " | self-supplied text, so boosts are capped (ecosystem lift <= 60% of headroom, integrity <= +15%).")

        st.subheader("Verified tech skills")
        if result["verified_skills"]:
            st.success("Matching repository signals: " + "  ".join(f"`{s}`" for s in result["verified_skills"]))
        else:
            st.warning("No repository signals matched the skills claimed on the resume.")
        extra = [s for s in result["github_verified_skills"] if s not in result["resume_skills"]]
        if extra:
            st.caption("Also visible on GitHub but not on the resume: " + ", ".join(extra))

        st.subheader("Unverified capability gaps")
        if result["missing_track_skills"]:
            st.error("Missing from the scanned GitHub repositories for this track: **"
                     + ", ".join(result["missing_track_skills"]) + "**")
        else:
            st.success("A matching repository signal was found for every baseline skill.")
        if result["unverified_claims"]:
            st.error("Claimed on the resume but not found on GitHub: **"
                     + ", ".join(result["unverified_claims"]) + "**")

    # ------------------------------ right --------------------------------- #
    with right:
        st.subheader("12-dimension telemetry ledger")
        targets = TRACK_TARGETS[result["track"]]
        rows = ["| | Dimension | Live value | Score | Target window |", "|:-:|---|---|:-:|:-:|"]
        for key, label in DIMENSIONS:
            m = result["metrics"][key]
            low = max(0.0, targets[key] - TOLERANCE)
            mark = "✅" if m["value"] >= low else "❌"
            rows.append(f"| {mark} | **{label}** | {m['display']} | {m['value']:.2f} | ≥ {low:.2f} (target {targets[key]:.2f}) |")
        st.markdown("\n".join(rows))
        passed = sum(1 for k, _ in DIMENSIONS if result["metrics"][k]["value"] >= max(0.0, targets[k] - TOLERANCE))
        st.caption(f"{passed}/12 dimensions inside the tolerance window (±{TOLERANCE:.2f}).")

        st.subheader("Roadmap to close your gaps")
        for i, step in enumerate(build_roadmap(result, readiness), start=1):
            st.markdown(f"{i}. {step}")

    # ------------------------- latent space readout ----------------------- #
    bundle = load_market_bundle(MODEL_PATH)
    with st.expander("Market latent-space alignment (trained VAE)"):
        if bundle is None:
            st.info("Train the model first (`python train_market_engine.py`) to enable this readout.")
        elif isinstance(bundle, dict):
            st.warning(f"Could not load '{MODEL_PATH}': {bundle['error']}")
        else:
            from core_model import latent_alignment
            model, tokenizer, extras, device = bundle
            text = st.session_state.get("resume_text", "")
            info = latent_alignment(model, tokenizer, text, compute_text_properties(text), extras, device)
            a, b = st.columns(2)
            a.metric("Market typicality", f"{info['typicality_pct']:.0f}%")
            b.metric("Latent distance to market centroid", f"{info['distance']:.2f}",
                     help=f"Median distance in the training corpus: {info['median_distance']:.2f}")
            st.caption(f"Learned from {extras.get('n_resumes', '?')} resumes. This is an informational "
                       "signal about how typical the resume text is of the training corpus - it is not part "
                       "of the readiness score.")


if __name__ == "__main__":
    main()
