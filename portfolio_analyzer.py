"""
portfolio_analyzer.py  --  CareerLens AI live data-stream extraction engine
==========================================================================
Pure standard library (urllib + json + re + math). No random numbers, no
simulated data: every metric is computed from

  * the resume text block the user pasted, and
  * the JSON returned by the live GitHub REST API
    (https://api.github.com/users/{username}/repos).

This module is shared by the whole project:
  * app.py                 -> PortfolioAnalyzer.post_analyze_candidate()
  * train_market_engine.py -> compute_text_properties() so that the 12 training
                              conditions and the inference conditions are
                              produced by the SAME function.
"""
from __future__ import annotations

import json
import math
import ssl
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
GITHUB_API = "https://api.github.com"
USER_AGENT = "CareerLensAI/1.0 (DataQuest-3.0)"
MAX_PAGES = 3            # 3 x 100 = up to 300 repos per candidate
DEEP_SCAN_LIMIT = 12     # max extra /languages calls when deep scan is enabled
TOLERANCE = 0.15         # width of the tolerance window used by the dashboard

# Master skill list (order is the order used everywhere in the project)
SKILLS: List[str] = [
    "Python", "PyTorch", "C++", "JavaScript", "React", "NodeJS", "Figma",
    "Docker", "SQL", "HTML", "CSS", "Java", "Git", "AWS", "FastAPI", "Django",
    "Tailwind", "Kubernetes", "CI_CD", "NoSQL", "Linux",
]

# Master regex list for self-claimed competencies in a resume
SKILL_PATTERNS: Dict[str, str] = {
    "Python": r"\bpython[23]?\b",
    "PyTorch": r"\bpy\s?torch\b|\btorch\b",
    "C++": r"(?<![\w+])c\+\+(?![\w+])|\bcpp\b",
    "JavaScript": r"\bjavascript\b|\btypescript\b|\becmascript\b|\bjs\b",
    "React": r"\breact(?:\.?js)?\b|\bnext\.?js\b",
    "NodeJS": r"\bnode(?:\.?js)?\b|\bexpress(?:\.?js)?\b",
    "Figma": r"\bfigma\b",
    "Docker": r"\bdocker(?:file|-compose)?\b|\bcontaineri[sz](?:ed|ation)\b",
    "SQL": r"\b(?:sql|mysql|postgres(?:ql)?|sqlite|mssql|pl/sql|t-sql)\b",
    "HTML": r"\bhtml5?\b",
    "CSS": r"\bcss3?\b|\bscss\b|\bsass\b",
    "Java": r"\bjava\b",
    "Git": r"\bgit(?:hub|lab)?\b",
    "AWS": r"\baws\b|\bamazon web services\b|\bec2\b|\bs3\b|\bsagemaker\b",
    "FastAPI": r"\bfast\s?api\b",
    "Django": r"\bdjango\b",
    "Tailwind": r"\btailwind(?:\s?css)?\b",
    "Kubernetes": r"\bkubernetes\b|\bk8s\b",
    "CI_CD": r"\bci\s?/\s?cd\b|\bci-cd\b|\bcicd\b|\bcontinuous (?:integration|delivery|deployment)\b"
             r"|\bjenkins\b|\bgithub actions\b|\bgitlab ci\b",
    "NoSQL": r"\bnosql\b|\bmongo(?:db)?\b|\bcassandra\b|\bredis\b|\bdynamodb\b|\bcouchdb\b|\bfirebase\b",
    "Linux": r"\blinux\b|\bubuntu\b|\bunix\b|\bbash\b|\bshell scripting\b",
}
SKILL_REGEX: Dict[str, "re.Pattern[str]"] = {
    name: re.compile(pattern, re.IGNORECASE) for name, pattern in SKILL_PATTERNS.items()
}

# Target career tracks -> exact baseline criteria arrays
TRACK_BASELINES: Dict[str, List[str]] = {
    "Core Software Engineer": ["Python", "JavaScript", "Git", "SQL", "Docker"],
    "Data Scientist / AI Engineer": ["Python", "PyTorch", "Git", "Linux", "AWS"],
    "UI/UX Product Architect": ["Figma", "HTML", "CSS", "Tailwind", "JavaScript"],
}

# The 12 dimensions (key, human label). Order is fixed across the project.
DIMENSIONS: List[Tuple[str, str]] = [
    ("consistency", "Consistency Index"),
    ("tech_depth", "Tech Depth (language diversity)"),
    ("frameworks", "Framework Complexity"),
    ("breadth", "Structural Breadth"),
    ("integrity", "Claims Integrity"),
    ("products", "Shipped Products"),
    ("deployment", "Deployment Footprint"),
    ("collaboration", "Collaboration Density"),
    ("documentation", "Documentation Quality"),
    ("proximity", "Domain Proximity"),
    ("gap", "Gap Accessibility"),
    ("ecosystem", "Network Ecosystem Dispersion"),
]
DIMENSION_KEYS: List[str] = [k for k, _ in DIMENSIONS]

# Target value per dimension and track (0..1). A metric "passes" when
# value >= target - TOLERANCE.
TRACK_TARGETS: Dict[str, Dict[str, float]] = {
    "Core Software Engineer": {
        "consistency": 0.60, "tech_depth": 0.50, "frameworks": 0.40, "breadth": 0.50,
        "integrity": 0.80, "products": 0.50, "deployment": 0.40, "collaboration": 0.20,
        "documentation": 0.50, "proximity": 0.70, "gap": 0.80, "ecosystem": 0.20,
    },
    "Data Scientist / AI Engineer": {
        "consistency": 0.50, "tech_depth": 0.50, "frameworks": 0.55, "breadth": 0.50,
        "integrity": 0.80, "products": 0.50, "deployment": 0.30, "collaboration": 0.20,
        "documentation": 0.60, "proximity": 0.70, "gap": 0.80, "ecosystem": 0.20,
    },
    "UI/UX Product Architect": {
        "consistency": 0.50, "tech_depth": 0.40, "frameworks": 0.45, "breadth": 0.50,
        "integrity": 0.80, "products": 0.50, "deployment": 0.50, "collaboration": 0.30,
        "documentation": 0.50, "proximity": 0.70, "gap": 0.80, "ecosystem": 0.30,
    },
}

# Skills whose claims are expensive to fake -> a failed cross-check hurts more
STRICT_CLAIM_SKILLS = {"Docker", "SQL", "Kubernetes", "AWS", "NoSQL", "CI_CD"}
STRICT_WEIGHT = 2.0

FRAMEWORK_KEYWORDS: List[str] = [
    "react", "next.js", "nextjs", "vue", "angular", "svelte", "django", "flask", "fastapi",
    "express", "spring", "streamlit", "pytorch", "tensorflow", "keras", "scikit learn",
    "sklearn", "pandas", "numpy", "opencv", "huggingface", "transformers", "langchain",
    "tailwind", "bootstrap", "node", "kubernetes", "electron", "flutter", "react native",
]

# What counts as GitHub evidence for a skill: primary/secondary language names
# (lower-case) and keywords searched in repo name + description + topics.
GITHUB_EVIDENCE: Dict[str, Dict[str, List[str]]] = {
    "Python": {"lang": ["python", "jupyter notebook"],
               "kw": ["python", "pandas", "numpy", "flask", "sklearn", "scikit learn"]},
    "PyTorch": {"lang": [], "kw": ["pytorch", "torch", "deep learning", "neural network", "lstm",
                                   "autoencoder", "vae", "transformer", "cnn"]},
    "C++": {"lang": ["c++"], "kw": ["c++", "cpp"]},
    "JavaScript": {"lang": ["javascript", "typescript"],
                   "kw": ["javascript", "typescript", "node", "react", "vue", "express", "next.js", "nextjs"]},
    "React": {"lang": [], "kw": ["react", "next.js", "nextjs", "redux"]},
    "NodeJS": {"lang": [], "kw": ["node", "nodejs", "node.js", "express", "npm", "nestjs"]},
    "Figma": {"lang": [], "kw": ["figma", "ui ux", "ux", "wireframe", "prototype", "design system"]},
    "Docker": {"lang": ["dockerfile"], "kw": ["docker", "dockerfile", "container", "compose"]},
    "SQL": {"lang": ["sql", "plpgsql", "tsql", "plsql"],
            "kw": ["sql", "mysql", "postgres", "postgresql", "sqlite", "database", "sqlalchemy", "orm"]},
    "HTML": {"lang": ["html"], "kw": ["html"]},
    "CSS": {"lang": ["css", "scss", "sass", "less"], "kw": ["css", "bootstrap", "sass", "scss", "tailwind"]},
    "Java": {"lang": ["java"], "kw": ["java", "spring", "maven", "gradle"]},
    "Git": {"lang": [], "kw": []},  # a public repository is itself Git evidence (handled below)
    "AWS": {"lang": [], "kw": ["aws", "lambda", "ec2", "s3", "cloudformation", "sagemaker", "amazon"]},
    "FastAPI": {"lang": [], "kw": ["fastapi"]},
    "Django": {"lang": [], "kw": ["django"]},
    "Tailwind": {"lang": [], "kw": ["tailwind", "tailwindcss"]},
    "Kubernetes": {"lang": [], "kw": ["kubernetes", "k8s", "helm"]},
    "CI_CD": {"lang": [], "kw": ["ci cd", "cicd", "github actions", "jenkins", "gitlab ci", "continuous integration"]},
    "NoSQL": {"lang": [], "kw": ["nosql", "mongo", "mongodb", "redis", "firebase", "dynamodb", "cassandra"]},
    "Linux": {"lang": ["shell"], "kw": ["linux", "ubuntu", "bash", "shell", "dotfiles"]},
}

DEPLOY_ANCHORS: List[str] = [
    "vercel", "render", "aws", "docker", "deploy", "deployed", "deployment", "netlify", "heroku",
    "azure", "gcp", "railway", "github pages", "streamlit app", "huggingface spaces", "cloud run",
]


def _norm(text: str) -> str:
    """Lower-case and collapse separators so 'deep-learning' == 'deep learning'."""
    return re.sub(r"[-_/]+", " ", (text or "").lower())


def _kw_regex(keywords: List[str]) -> Optional["re.Pattern[str]"]:
    if not keywords:
        return None
    parts = [re.escape(_norm(k)) for k in keywords]
    return re.compile(r"(?<![a-z0-9])(?:" + "|".join(parts) + r")(?![a-z0-9])")


_EVIDENCE_REGEX = {skill: _kw_regex(rule["kw"]) for skill, rule in GITHUB_EVIDENCE.items()}
_EVIDENCE_LANGS = {skill: set(rule["lang"]) for skill, rule in GITHUB_EVIDENCE.items()}
_FRAMEWORK_REGEX = _kw_regex(FRAMEWORK_KEYWORDS)
_DEPLOY_REGEX = _kw_regex(DEPLOY_ANCHORS)


def _clip(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(x)))


def _sat(x: float, k: float) -> float:
    """Smooth saturation: 0 -> 0, large x -> 1."""
    return 1.0 - math.exp(-max(0.0, x) / k)


# --------------------------------------------------------------------------- #
# Text -> 12 objective properties (used for training AND inference)
# --------------------------------------------------------------------------- #
_WORD_RE = re.compile(r"c\+\+|c#|[a-z][a-z0-9]*(?:[.+#][a-z0-9]+)*")
_SHIP_RE = re.compile(r"\b(built|developed|deployed|launched|shipped|implemented|designed|released|"
                      r"delivered|engineered|created|published)\b")
_CLOUD_RE = re.compile(r"\b(aws|azure|gcp|cloud|vercel|heroku|netlify|deploy\w*|ec2|production|docker|kubernetes)\b")
_TEAM_RE = re.compile(r"\b(team|collaborat\w*|led|mentor\w*|agile|scrum|stakeholder\w*|cross-functional|"
                      r"code review|pair programming)\b")
_DOC_RE = re.compile(r"\b(document\w*|readme|wiki|report\w*|technical writing|specification|manual)\b")

SKILL_CATEGORIES: Dict[str, List[str]] = {
    "languages": ["Python", "C++", "JavaScript", "Java", "SQL"],
    "ml_backend": ["PyTorch", "FastAPI", "Django", "NoSQL"],
    "frontend_design": ["React", "NodeJS", "HTML", "CSS", "Tailwind", "Figma"],
    "infra": ["Docker", "Kubernetes", "AWS", "CI_CD", "Linux", "Git"],
}


def compute_text_properties(text: str) -> List[float]:
    """
    12 continuous, deterministic properties in [0, 1] derived from length,
    Shannon entropy and skill statistics of a resume. Same order as DIMENSIONS.
    """
    text = text or ""
    low = text.lower()
    words = _WORD_RE.findall(low)
    n = len(words)
    if n == 0:
        return [0.0] * 12

    counts = Counter(words)
    entropy = -sum((c / n) * math.log2(c / n) for c in counts.values())  # bits

    skill_hits = {s: len(SKILL_REGEX[s].findall(text)) for s in SKILLS}
    found = [s for s, c in skill_hits.items() if c > 0]
    found_set = set(found)

    fw_found = {m.group(0) for m in (_FRAMEWORK_REGEX.finditer(_norm(text)) if _FRAMEWORK_REGEX else [])}
    sentences = [s for s in re.split(r"[.!?\n]+", text) if s.strip()]
    avg_sentence = (sum(len(_WORD_RE.findall(s.lower())) for s in sentences) / len(sentences)) if sentences else 0.0

    track_overlaps = [
        len(found_set & set(base)) / len(base) for base in TRACK_BASELINES.values()
    ]

    cat_counts = [sum(skill_hits[s] for s in members) for members in SKILL_CATEGORIES.values()]
    cat_total = sum(cat_counts)
    if cat_total > 0:
        cat_entropy = -sum((c / cat_total) * math.log2(c / cat_total) for c in cat_counts if c > 0)
        dispersion = cat_entropy / math.log2(len(cat_counts))
    else:
        dispersion = 0.0

    reinforced = sum(1 for s in found if skill_hits[s] >= 2)

    props = [
        _sat(n, 600.0),                                              # 1 consistency (length)
        len(found) / len(SKILLS),                                    # 2 tech depth
        _clip(len(fw_found) / 6.0),                                  # 3 framework complexity
        _clip((entropy - 4.0) / 5.0),                                # 4 structural breadth (entropy)
        (reinforced / len(found)) if found else 0.0,                 # 5 claims integrity (self-reinforced)
        _sat(len(_SHIP_RE.findall(low)), 6.0),                       # 6 shipped products
        _sat(len(_CLOUD_RE.findall(low)), 4.0),                      # 7 deployment footprint
        _sat(len(_TEAM_RE.findall(low)), 5.0),                       # 8 collaboration density
        0.5 * _sat(len(_DOC_RE.findall(low)), 3.0) + 0.5 * _clip(avg_sentence / 25.0),  # 9 documentation
        sum(track_overlaps) / len(track_overlaps),                   # 10 domain proximity
        max(track_overlaps),                                         # 11 gap accessibility
        _clip(dispersion),                                           # 12 ecosystem dispersion
    ]
    return [round(_clip(p), 6) for p in props]


# --------------------------------------------------------------------------- #
# HTTP layer
# --------------------------------------------------------------------------- #
class GitHubError(RuntimeError):
    """Raised for any GitHub / network problem with a user-presentable message."""


def _http_get_json(url: str, token: Optional[str] = None, timeout: int = 15) -> Tuple[Any, Dict[str, str]]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token.strip()}"  # 5,000 req/hour instead of 60
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return json.loads(body), {k.lower(): v for k, v in response.headers.items()}
    except urllib.error.HTTPError as exc:
        remaining = exc.headers.get("X-RateLimit-Remaining") if exc.headers else None
        if exc.code == 404:
            raise GitHubError("GitHub user not found. Check the profile link.") from exc
        if exc.code == 401:
            raise GitHubError("GitHub rejected the access token (HTTP 401).") from exc
        if exc.code in (403, 429) and remaining == "0":
            raise GitHubError("GitHub API rate limit reached (60/hour without a token). "
                              "Add a personal access token to raise it to 5,000/hour.") from exc
        raise GitHubError(f"GitHub API returned HTTP {exc.code}.") from exc
    except urllib.error.URLError as exc:
        raise GitHubError(f"Network error while contacting GitHub: {exc.reason}") from exc
    except TimeoutError as exc:
        raise GitHubError("GitHub API request timed out.") from exc
    except json.JSONDecodeError as exc:
        raise GitHubError("GitHub returned a response that is not valid JSON.") from exc


# --------------------------------------------------------------------------- #
# Analyzer
# --------------------------------------------------------------------------- #
class PortfolioAnalyzer:
    """Resume + live GitHub telemetry extractor."""

    # ---- resume side ------------------------------------------------------ #
    def parse_document_text_entities(self, text: str) -> List[str]:
        """Return the self-claimed competencies found in the resume (master regex list)."""
        text = text or ""
        return [skill for skill in SKILLS if SKILL_REGEX[skill].search(text)]

    # ---- GitHub side ------------------------------------------------------ #
    @staticmethod
    def extract_username(link: str) -> Optional[str]:
        link = (link or "").strip()
        match = re.match(
            r"^(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))(?:[/?#].*)?$", link)
        if match:
            return match.group(1)
        if re.fullmatch(r"@?[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})", link):
            return link.lstrip("@")
        return None

    @staticmethod
    def _track_ctx(ctx: Dict[str, Any], headers: Dict[str, str]) -> None:
        ctx["calls"] += 1
        try:
            ctx["remaining"] = int(headers.get("x-ratelimit-remaining", ""))
            ctx["limit"] = int(headers.get("x-ratelimit-limit", ""))
        except ValueError:
            pass

    def _fetch_repositories(self, username: str, token: Optional[str], ctx: Dict[str, Any]) -> List[dict]:
        repos: List[dict] = []
        quoted = urllib.parse.quote(username)
        for page in range(1, MAX_PAGES + 1):
            url = f"{GITHUB_API}/users/{quoted}/repos?per_page=100&type=owner&sort=pushed&page={page}"
            data, headers = _http_get_json(url, token)
            self._track_ctx(ctx, headers)
            if not isinstance(data, list):
                raise GitHubError("Unexpected response shape from the GitHub repos endpoint.")
            repos.extend(r for r in data if isinstance(r, dict))
            if len(data) < 100:
                break
        return repos

    def _deep_scan_languages(self, repos: List[dict], token: Optional[str],
                             ctx: Dict[str, Any]) -> Dict[str, List[str]]:
        """Optional: query each original repo's languages_url (surfaces Dockerfile, Shell, CSS ...)."""
        extra: Dict[str, List[str]] = {}
        candidates = [r for r in repos if not r.get("fork")][:DEEP_SCAN_LIMIT]
        for repo in candidates:
            if ctx["remaining"] is not None and ctx["remaining"] <= 5:
                break
            url = repo.get("languages_url") or ""
            if not url.startswith(GITHUB_API + "/"):
                continue
            try:
                data, headers = _http_get_json(url, token)
            except GitHubError:
                continue
            self._track_ctx(ctx, headers)
            if isinstance(data, dict):
                extra[repo.get("name", "")] = [str(k).lower() for k in data.keys()]
        return extra

    @staticmethod
    def _repo_corpus(repo: dict) -> str:
        parts = [repo.get("name") or "", repo.get("description") or "", " ".join(repo.get("topics") or [])]
        return _norm(" ".join(parts))

    def _skill_evidence(self, repos: List[dict], extra_langs: Dict[str, List[str]]) -> Dict[str, int]:
        """skill -> number of repos that carry evidence for it."""
        evidence: Dict[str, int] = {s: 0 for s in SKILLS}
        for repo in repos:
            corpus = self._repo_corpus(repo)
            langs = set()
            if repo.get("language"):
                langs.add(str(repo["language"]).lower())
            langs.update(extra_langs.get(repo.get("name", ""), []))
            for skill in SKILLS:
                if skill == "Git":
                    evidence[skill] += 1
                    continue
                regex = _EVIDENCE_REGEX[skill]
                if (langs & _EVIDENCE_LANGS[skill]) or (regex and regex.search(corpus)):
                    evidence[skill] += 1
        return evidence

    # ---- main entry ------------------------------------------------------- #
    def post_analyze_candidate(self, request_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        request_payload keys:
            resume_text (str), github_url (str), track (str),
            github_token (str, optional), deep_scan (bool, optional)
        Returns a dict; on failure {"ok": False, "error": "..."}.
        """
        started = time.perf_counter()
        resume_text = request_payload.get("resume_text") or ""
        track = request_payload.get("track") or "Core Software Engineer"
        token = (request_payload.get("github_token") or "").strip() or None
        deep_scan = bool(request_payload.get("deep_scan", False))

        if track not in TRACK_BASELINES:
            return {"ok": False, "error": f"Unknown target track: {track}"}
        username = self.extract_username(request_payload.get("github_url", ""))
        if not username:
            return {"ok": False, "error": "Could not extract a GitHub username from the link provided."}

        claimed = self.parse_document_text_entities(resume_text)
        ctx: Dict[str, Any] = {"calls": 0, "remaining": None, "limit": None}
        try:
            repos = self._fetch_repositories(username, token, ctx)
            extra_langs = self._deep_scan_languages(repos, token, ctx) if (deep_scan and repos) else {}
        except GitHubError as exc:
            return {"ok": False, "error": str(exc)}
        latency = time.perf_counter() - started

        evidence = self._skill_evidence(repos, extra_langs)
        strength = {s: min(1.0, evidence[s] / 2.0) for s in SKILLS}  # 1 repo = 0.5, 2+ repos = 1.0
        github_verified = [s for s in SKILLS if evidence[s] > 0]

        verified_claims = [s for s in claimed if evidence[s] > 0]
        unverified_claims = [s for s in claimed if evidence[s] == 0]
        baseline = TRACK_BASELINES[track]
        missing = [s for s in baseline if evidence[s] == 0]

        metrics = self._compute_metrics(repos, extra_langs, claimed, evidence, strength, baseline, missing)

        return {
            "ok": True,
            "username": username,
            "track": track,
            "resume_skills": claimed,
            "verified_skills": verified_claims,
            "unverified_claims": unverified_claims,
            "github_verified_skills": github_verified,
            "track_baseline": baseline,
            "missing_track_skills": missing,
            "metrics": metrics,
            "vector": [metrics[k]["value"] for k in DIMENSION_KEYS],
            "meta": {
                "repos": len(repos),
                "api_calls": ctx["calls"],
                "rate_remaining": ctx["remaining"],
                "rate_limit": ctx["limit"],
                "latency_sec": round(latency, 3),
                "deep_scan": bool(extra_langs),
                "authenticated": token is not None,
                "fetched_at": time.time(),
            },
        }

    # ---- the 12 dimensions ------------------------------------------------ #
    def _compute_metrics(self, repos: List[dict], extra_langs: Dict[str, List[str]], claimed: List[str],
                         evidence: Dict[str, int], strength: Dict[str, float], baseline: List[str],
                         missing: List[str]) -> Dict[str, Dict[str, Any]]:
        total = len(repos)
        originals = [r for r in repos if not r.get("fork")]
        forked = total - len(originals)
        labels = dict(DIMENSIONS)

        def pack(key: str, value: float, display: str) -> Dict[str, Any]:
            return {"label": labels[key], "value": round(_clip(value), 4), "display": display}

        # 1. Consistency: total public repositories
        consistency = pack("consistency", total / 20.0, f"{total} public repos")

        # 2. Diversity: unique languages from the 'language' tags (+ deep-scan languages)
        languages = {str(r["language"]).lower() for r in repos if r.get("language")}
        for langs in extra_langs.values():
            languages.update(langs)
        tech_depth = pack("tech_depth", len(languages) / 6.0, f"{len(languages)} unique languages")

        # 3. Frameworks: keyword scan on names, descriptions, topics
        fw_found = set()
        for repo in repos:
            if _FRAMEWORK_REGEX:
                fw_found.update(m.group(0) for m in _FRAMEWORK_REGEX.finditer(self._repo_corpus(repo)))
        frameworks = pack("frameworks", len(fw_found) / 6.0, f"{len(fw_found)} frameworks detected")

        # 4. Breadth: complexity index from character length of names + summaries
        chars = sum(len(r.get("name") or "") + len(r.get("description") or "") +
                    len(" ".join(r.get("topics") or [])) for r in repos)
        breadth = pack("breadth", math.log1p(chars) / math.log1p(2500.0), f"{chars} chars of repo text")

        # 5. Claims integrity: strict cross-reference of resume claims vs GitHub evidence
        if claimed:
            weights = {s: (STRICT_WEIGHT if s in STRICT_CLAIM_SKILLS else 1.0) for s in claimed}
            ok_weight = sum(w for s, w in weights.items() if evidence[s] > 0)
            integrity_val = ok_weight / sum(weights.values())
            n_ok = sum(1 for s in claimed if evidence[s] > 0)
            integrity = pack("integrity", integrity_val, f"{n_ok}/{len(claimed)} resume claims verified")
        else:
            integrity = pack("integrity", 0.0, "no skills detected in resume")

        # 6. Products: unique non-forked personal repositories
        unique_originals = len({r.get("name") for r in originals})
        products = pack("products", unique_originals / 10.0, f"{unique_originals} original repos")

        # 7. Deployment: cloud / deploy anchors in text, or a live homepage URL
        deploy_repos = 0
        for repo in repos:
            if (_DEPLOY_REGEX and _DEPLOY_REGEX.search(self._repo_corpus(repo))) or (repo.get("homepage") or "").strip():
                deploy_repos += 1
        deployment = pack("deployment", deploy_repos / 4.0, f"{deploy_repos} repos with deploy signals")

        # 8. Collaboration: forked repos / total personal repos
        fork_ratio = (forked / total) if total else 0.0
        collaboration = pack("collaboration", fork_ratio / 0.35, f"{forked} forked / {total} repos ({fork_ratio:.0%})")

        # 9. Documentation: description coverage + mean description length
        desc_lengths = [len((r.get("description") or "").strip()) for r in repos]
        non_empty = [d for d in desc_lengths if d > 0]
        coverage = (len(non_empty) / total) if total else 0.0
        mean_len = (sum(non_empty) / len(non_empty)) if non_empty else 0.0
        documentation = pack("documentation", 0.5 * coverage + 0.5 * _clip(mean_len / 90.0),
                             f"{coverage:.0%} described, avg {mean_len:.0f} chars")

        # 10. Proximity: Euclidean distance between profile skill vector and the track baseline
        vec = [strength[s] for s in baseline]
        dist = math.sqrt(sum((1.0 - v) ** 2 for v in vec))
        proximity_val = 1.0 - dist / math.sqrt(len(baseline))
        proximity = pack("proximity", proximity_val, f"Euclidean distance {dist:.2f} / {math.sqrt(len(baseline)):.2f}")

        # 11. Gap index: which track skills are completely missing from verified GitHub tags
        gap_val = 1.0 - (len(missing) / len(baseline))
        gap_display = f"{len(missing)} missing: {', '.join(missing)}" if missing else "0 missing"
        gap = pack("gap", gap_val, gap_display)

        # 12. Ecosystem: community engagement (stars + forks received by original repos)
        stars = sum(int(r.get("stargazers_count") or 0) for r in originals)
        forks_received = sum(int(r.get("forks_count") or 0) for r in originals)
        community = stars + forks_received
        ecosystem = pack("ecosystem", math.log1p(community) / math.log1p(60.0),
                         f"{stars} stars + {forks_received} forks received")

        return {
            "consistency": consistency, "tech_depth": tech_depth, "frameworks": frameworks,
            "breadth": breadth, "integrity": integrity, "products": products,
            "deployment": deployment, "collaboration": collaboration, "documentation": documentation,
            "proximity": proximity, "gap": gap, "ecosystem": ecosystem,
        }
