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

import base64
import json
import math
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
GITHUB_API = "https://api.github.com"
USER_AGENT = "CareerLensAI/1.0 (DataQuest-3.0)"
MAX_PAGES = 3            # 3 x 100 = up to 300 repos per candidate
DEEP_SCAN_LIMIT = 12     # top original repositories inspected for languages, READMEs and commits
DEEP_SCAN_WORKERS = 4
ANONYMOUS_DEEP_SCAN_LIMIT = 5
COMMIT_DETAIL_LIMIT = 2  # one extra commit-detail request for two project samples
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
    ("collaboration", "Account-attributed Contributions"),
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


# --------------------------------------------------------------------------- #
# LinkedIn signal vocabulary (unstructured text pasted by the user)
# --------------------------------------------------------------------------- #
LINKEDIN_MILESTONES: Dict[str, "re.Pattern[str]"] = {
    "hackathon": re.compile(r"\bhackathons?\b", re.I),
    "shipped": re.compile(r"\bship(?:ped|ping)\b", re.I),
    "deployed": re.compile(r"\bdeploy(?:ed|ing|ment)\b", re.I),
    "conference": re.compile(r"\bconferences?\b", re.I),
    "open-source": re.compile(r"\bopen[\s-]?source\b", re.I),
    "engineered": re.compile(r"\bengineer(?:ed|ing)\b", re.I),
    "launched": re.compile(r"\blaunch(?:ed|ing)\b", re.I),
    "scaled": re.compile(r"\bscal(?:ed|ing)\b", re.I),
}
# term -> (regex, weight). Third-party language (recommended / endorsed) carries full weight;
# first-person managerial language is weaker evidence because the candidate controls it.
LINKEDIN_ATTESTATIONS: Dict[str, Tuple["re.Pattern[str]", float]] = {
    "recommended": (re.compile(r"\brecommend(?:ed|s|ation|ations)\b", re.I), 1.0),
    "endorsed": (re.compile(r"\bendors(?:ed|es|ement|ements)\b", re.I), 1.0),
    "managed": (re.compile(r"\bmanaged\b", re.I), 0.5),
    "supervised": (re.compile(r"\bsupervis(?:ed|ion)\b", re.I), 0.5),
    "collaborated with": (re.compile(r"\bcollaborated\s+with\b", re.I), 0.5),
}
LINKEDIN_TERM_CAP = 3            # one term counts at most 3x -> repeating a keyword cannot inflate the score
ECOSYSTEM_MAX_LIFT = 0.60        # share of the remaining headroom that LinkedIn milestones can fill
INTEGRITY_MAX_MULTIPLIER = 1.15  # attestations can raise integrity by at most +15 %
LINKEDIN_VERIFIED_LABEL = "Verified via LinkedIn Activity Stream and Peer Endorsements"


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

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class _IPv4Only:
    """Context manager: resolve hostnames to IPv4 only (fixes networks with a broken IPv6 route)."""

    def __enter__(self):
        self._orig = socket.getaddrinfo
        orig = self._orig

        def ipv4_only(host, port, family=0, type=0, proto=0, flags=0):
            return orig(host, port, socket.AF_INET, type, proto, flags)

        socket.getaddrinfo = ipv4_only
        return self

    def __exit__(self, *exc):
        socket.getaddrinfo = self._orig
        return False


def _urlopen_read(request: "urllib.request.Request", timeout: int) -> str:
    """Open GitHub API calls directly, avoiding broken local proxy settings."""
    hostname = urllib.parse.urlparse(request.full_url).hostname

    def open_request():
        if hostname == "api.github.com":
            # Some local/dev environments set a dead HTTP(S)_PROXY (for example
            # 127.0.0.1:9). GitHub is reachable directly, so bypass it for this
            # host while leaving proxy behavior unchanged for other destinations.
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            return opener.open(request, timeout=timeout)
        return urllib.request.urlopen(request, timeout=timeout)

    try:
        with open_request() as response:
            return response.read().decode("utf-8"), {k.lower(): v for k, v in response.headers.items()}
    except (urllib.error.URLError, TimeoutError) as exc:
        if isinstance(exc, urllib.error.HTTPError):
            raise
        with _IPv4Only():
            with open_request() as response:
                return response.read().decode("utf-8"), {k.lower(): v for k, v in response.headers.items()}


def _http_get_json(url: str, token: Optional[str] = None, timeout: int = 25) -> Tuple[Any, Dict[str, str]]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token.strip()}"  # 5,000 req/hour instead of 60
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        body, resp_headers = _urlopen_read(request, timeout)
        return json.loads(body), resp_headers
    except urllib.error.HTTPError as exc:
        remaining = exc.headers.get("X-RateLimit-Remaining") if exc.headers else None
        if exc.code == 404:
            raise GitHubError("GitHub profile or public repository not found. Check the profile link and repository visibility.", 404) from exc
        if exc.code == 401:
            raise GitHubError("GitHub rejected the access token (HTTP 401).") from exc
        if exc.code in (403, 429) and remaining == "0":
            raise GitHubError("GitHub API rate limit reached (60/hour without a token). "
                              "Add a personal access token to raise it to 5,000/hour.") from exc
        raise GitHubError(f"GitHub API returned HTTP {exc.code}.") from exc
    except urllib.error.URLError as exc:
        raise GitHubError(f"Network error while contacting GitHub: {exc.reason}. Check VPN/proxy/firewall, "
                          "or test: curl -4 https://api.github.com") from exc
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

    def _fetch_profile(self, username: str, token: Optional[str], ctx: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{GITHUB_API}/users/{urllib.parse.quote(username)}"
        data, headers = _http_get_json(url, token)
        self._track_ctx(ctx, headers)
        if not isinstance(data, dict) or str(data.get("login", "")).lower() != username.lower():
            raise GitHubError("GitHub returned a profile that does not match the supplied username.")
        return data

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

    def _fetch_public_activity(self, username: str, token: Optional[str],
                               owned_repos: List[dict], ctx: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize one page of recent public events, including contributions outside owned repos."""
        url = f"{GITHUB_API}/users/{urllib.parse.quote(username)}/events/public?per_page=100"
        try:
            data, headers = _http_get_json(url, token)
            self._track_ctx(ctx, headers)
        except GitHubError:
            ctx["calls"] += 1
            return {
                "available": False, "events_reviewed": 0, "push_events": 0,
                "pushed_commits": 0, "pull_requests_opened": 0,
                "pull_requests_merged": 0, "external_repositories": [],
            }
        if not isinstance(data, list):
            return {
                "available": False, "events_reviewed": 0, "push_events": 0,
                "pushed_commits": 0, "pull_requests_opened": 0,
                "pull_requests_merged": 0, "external_repositories": [],
            }

        owned = {str(repo.get("full_name", "")).lower() for repo in owned_repos}
        external_repos = set()
        push_events = pushed_commits = prs_opened = prs_merged = 0
        for event in data:
            if not isinstance(event, dict):
                continue
            repo = event.get("repo") or {}
            repo_name = str(repo.get("name") or "")
            if repo_name and repo_name.lower() not in owned:
                external_repos.add(repo_name)
            payload = event.get("payload") or {}
            if event.get("type") == "PushEvent":
                push_events += 1
                pushed_commits += int(payload.get("distinct_size") or payload.get("size") or 0)
            elif event.get("type") == "PullRequestEvent":
                if payload.get("action") == "opened":
                    prs_opened += 1
                pull_request = payload.get("pull_request") or {}
                if payload.get("action") == "closed" and pull_request.get("merged_at"):
                    prs_merged += 1
        return {
            "available": True,
            "events_reviewed": len(data),
            "push_events": push_events,
            "pushed_commits": pushed_commits,
            "pull_requests_opened": prs_opened,
            "pull_requests_merged": prs_merged,
            "external_repositories": sorted(external_repos)[:20],
        }

    def _deep_scan_repositories(self, username: str, repos: List[dict], token: Optional[str],
                                ctx: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Inspect a bounded set of non-fork repositories using public GitHub REST data."""
        maximum = DEEP_SCAN_LIMIT if token else ANONYMOUS_DEEP_SCAN_LIMIT
        if ctx.get("remaining") is not None:
            # Keep room for other app routes sharing this machine's unauthenticated API budget.
            scan_budget = max(0, ctx["remaining"] - 5 - COMMIT_DETAIL_LIMIT)
            maximum = min(maximum, scan_budget // 4)
        ctx["deep_scan_limit"] = maximum
        candidates = [repo for repo in repos if not repo.get("fork")][:maximum]

        def inspect(repo: dict, position: int) -> Dict[str, Any]:
            full_name = str(repo.get("full_name") or "")
            try:
                owner, name = full_name.split("/", 1)
            except ValueError:
                return {"full_name": full_name, "errors": 1, "api_calls": 0}
            owner_path = urllib.parse.quote(owner, safe="")
            name_path = urllib.parse.quote(name, safe="")
            details: Dict[str, Any] = {
                "full_name": full_name,
                "languages": [],
                "readme": "",
                "authored_commits": 0,
                "commit_count_capped": False,
                "signed_commits": 0,
                "total_contributions": 0,
                "contributor_count": 0,
                "account_contribution_share": 0.0,
                "sample_commit_additions": 0,
                "sample_commit_deletions": 0,
                "sample_commit_files_changed": 0,
                "rate_remaining": None,
                "first_authored_commit": None,
                "last_authored_commit": None,
                "sample_commit_urls": [],
                "api_calls": 0,
                "errors": 0,
            }

            endpoints = [
                ("languages", f"{GITHUB_API}/repos/{owner_path}/{name_path}/languages"),
                ("readme", f"{GITHUB_API}/repos/{owner_path}/{name_path}/readme"),
                ("commits", f"{GITHUB_API}/repos/{owner_path}/{name_path}/commits?author={urllib.parse.quote(username)}&per_page=100"),
                ("contributors", f"{GITHUB_API}/repos/{owner_path}/{name_path}/contributors?per_page=100"),
            ]
            sample_sha: Optional[str] = None
            for kind, url in endpoints:
                details["api_calls"] += 1
                try:
                    data, headers = _http_get_json(url, token, timeout=15)
                    remaining = headers.get("x-ratelimit-remaining")
                    if remaining and remaining.isdigit():
                        remaining_value = int(remaining)
                        details["rate_remaining"] = min(
                            remaining_value,
                            details["rate_remaining"] if details["rate_remaining"] is not None else remaining_value,
                        )
                except GitHubError as exc:
                    if not (kind == "readme" and exc.status_code == 404):
                        details["errors"] += 1
                    continue

                if kind == "languages" and isinstance(data, dict):
                    details["languages"] = [str(language).lower() for language in data]
                elif kind == "readme" and isinstance(data, dict):
                    if data.get("encoding") == "base64" and isinstance(data.get("content"), str):
                        try:
                            raw = base64.b64decode(data["content"], validate=False)
                            details["readme"] = raw[:160_000].decode("utf-8", errors="replace")
                        except (ValueError, UnicodeError):
                            details["errors"] += 1
                elif kind == "commits" and isinstance(data, list):
                    attributed = [
                        commit for commit in data
                        if isinstance(commit, dict)
                        and isinstance(commit.get("author"), dict)
                        and str(commit["author"].get("login", "")).lower() == username.lower()
                    ]
                    details["authored_commits"] = len(attributed)
                    details["commit_count_capped"] = len(data) == 100
                    details["signed_commits"] = sum(
                        1 for commit in attributed
                        if ((commit.get("commit") or {}).get("verification") or {}).get("verified") is True
                    )
                    dates = sorted(
                        str(((commit.get("commit") or {}).get("author") or {}).get("date", ""))
                        for commit in attributed
                        if ((commit.get("commit") or {}).get("author") or {}).get("date")
                    )
                    if dates:
                        details["first_authored_commit"] = dates[0]
                        details["last_authored_commit"] = dates[-1]
                    details["sample_commit_urls"] = [
                        str(commit.get("html_url")) for commit in attributed[:3] if commit.get("html_url")
                    ]
                    if attributed:
                        sample_sha = str(attributed[0].get("sha") or "") or None
                elif kind == "contributors" and isinstance(data, list):
                    contributions = [
                        int(item.get("contributions") or 0)
                        for item in data if isinstance(item, dict)
                    ]
                    total_contributions = sum(contributions)
                    account_contributions = sum(
                        int(item.get("contributions") or 0)
                        for item in data
                        if isinstance(item, dict)
                        and isinstance(item.get("login"), str)
                        and item["login"].lower() == username.lower()
                    )
                    details["total_contributions"] = account_contributions
                    details["contributor_count"] = len(data)
                    details["account_contribution_share"] = (
                        round(account_contributions / total_contributions, 4)
                        if total_contributions else 0.0
                    )

            if sample_sha and position < COMMIT_DETAIL_LIMIT:
                details["api_calls"] += 1
                commit_url = f"{GITHUB_API}/repos/{owner_path}/{name_path}/commits/{urllib.parse.quote(sample_sha, safe='')}"
                try:
                    commit_data, headers = _http_get_json(commit_url, token, timeout=15)
                    remaining = headers.get("x-ratelimit-remaining")
                    if remaining and remaining.isdigit():
                        remaining_value = int(remaining)
                        details["rate_remaining"] = min(
                            remaining_value,
                            details["rate_remaining"] if details["rate_remaining"] is not None else remaining_value,
                        )
                    if isinstance(commit_data, dict):
                        stats = commit_data.get("stats") or {}
                        details["sample_commit_additions"] = int(stats.get("additions") or 0)
                        details["sample_commit_deletions"] = int(stats.get("deletions") or 0)
                        details["sample_commit_files_changed"] = len(commit_data.get("files") or [])
                except GitHubError:
                    details["errors"] += 1
            return details

        scanned: Dict[str, Dict[str, Any]] = {}
        if not candidates:
            return scanned
        with ThreadPoolExecutor(max_workers=DEEP_SCAN_WORKERS) as executor:
            futures = [executor.submit(inspect, repo, position) for position, repo in enumerate(candidates)]
            for future in as_completed(futures):
                details = future.result()
                scanned[details["full_name"]] = details
                ctx["calls"] += details["api_calls"]
                ctx["deep_scan_errors"] += details["errors"]
                if details["rate_remaining"] is not None:
                    ctx["remaining"] = min(ctx["remaining"], details["rate_remaining"]) if ctx["remaining"] is not None else details["rate_remaining"]
        return scanned

    @staticmethod
    def _repo_corpus(repo: dict) -> str:
        parts = [repo.get("name") or "", repo.get("description") or "", " ".join(repo.get("topics") or [])]
        return _norm(" ".join(parts))

    def _skill_evidence(self, repos: List[dict], deep_scan: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
        """Count skills with public signals in non-fork repos; this is not proof of authorship."""
        evidence: Dict[str, int] = {s: 0 for s in SKILLS}
        for repo in repos:
            if repo.get("fork"):
                continue
            detail = deep_scan.get(str(repo.get("full_name") or ""), {})
            corpus = self._repo_corpus(repo) + " " + _norm(detail.get("readme", ""))
            langs = set()
            if repo.get("language"):
                langs.add(str(repo["language"]).lower())
            langs.update(detail.get("languages", []))
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
        linkedin_text = request_payload.get("linkedin_text", "") or ""

        if track not in TRACK_BASELINES:
            return {"ok": False, "error": f"Unknown target track: {track}"}
        username = self.extract_username(request_payload.get("github_url", ""))
        if not username:
            return {"ok": False, "error": "Could not extract a GitHub username from the link provided."}

        claimed = self.parse_document_text_entities(resume_text)
        ctx: Dict[str, Any] = {"calls": 0, "remaining": None, "limit": None, "deep_scan_errors": 0}
        ctx["deep_scan_limit"] = 0
        try:
            profile = self._fetch_profile(username, token, ctx)
            repos = self._fetch_repositories(username, token, ctx)
            public_activity = self._fetch_public_activity(username, token, repos, ctx)
            repo_details = (
                self._deep_scan_repositories(username, repos, token, ctx)
                if deep_scan and repos else {}
            )
        except GitHubError as exc:
            return {"ok": False, "error": str(exc)}
        latency = time.perf_counter() - started

        evidence = self._skill_evidence(repos, repo_details)
        strength = {s: min(1.0, evidence[s] / 2.0) for s in SKILLS}  # 1 repo = 0.5, 2+ repos = 1.0
        github_verified = [s for s in SKILLS if evidence[s] > 0]

        verified_claims = [s for s in claimed if evidence[s] > 0]
        unverified_claims = [s for s in claimed if evidence[s] == 0]
        baseline = TRACK_BASELINES[track]
        missing = [s for s in baseline if evidence[s] == 0]

        metrics = self._compute_metrics(repos, repo_details, claimed, evidence, strength, baseline, missing)
        linkedin = self.analyze_linkedin_text(linkedin_text)
        self._apply_linkedin_signals(metrics, linkedin)
        originals = [repo for repo in repos if not repo.get("fork")]
        attributed_commits = sum(detail.get("authored_commits", 0) for detail in repo_details.values())
        contribution_commits = sum(detail.get("total_contributions", 0) for detail in repo_details.values())
        signed_commits = sum(detail.get("signed_commits", 0) for detail in repo_details.values())
        authored_repo_count = sum(1 for detail in repo_details.values() if detail.get("total_contributions", 0) > 0)
        complete_repo_scans = sum(1 for detail in repo_details.values() if detail.get("errors", 0) == 0)

        return {
            "ok": True,
            "username": username,
            "profile": {
                "name": profile.get("name"),
                "created_at": profile.get("created_at"),
                "public_repos": profile.get("public_repos"),
                "followers": profile.get("followers"),
                "html_url": profile.get("html_url"),
            },
            "track": track,
            "resume_skills": claimed,
            "verified_skills": verified_claims,
            "unverified_claims": unverified_claims,
            "github_verified_skills": github_verified,
            "track_baseline": baseline,
            "missing_track_skills": missing,
            "metrics": metrics,
            "linkedin": linkedin,
            "public_activity": public_activity,
            "vector": [metrics[k]["value"] for k in DIMENSION_KEYS],
            "repository_evidence": [
                {
                    "name": str(repo.get("full_name") or repo.get("name") or ""),
                    "url": str(repo.get("html_url") or ""),
                    "description": str(repo.get("description") or ""),
                    "fork": bool(repo.get("fork")),
                    "language": repo.get("language"),
                    "pushed_at": repo.get("pushed_at"),
                    "details": {
                        key: value
                        for key, value in repo_details.get(str(repo.get("full_name") or ""), {}).items()
                        if key != "readme"
                    },
                }
                for repo in repos
            ],
            "meta": {
                "repos": len(repos),
                "original_repos": len(originals),
                "deep_scanned_repos": len(repo_details),
                "deep_scan_limit": ctx["deep_scan_limit"],
                "complete_repo_scans": complete_repo_scans,
                "deep_scan_errors": ctx["deep_scan_errors"],
                "authored_commit_count": attributed_commits,
                "contribution_commits": contribution_commits,
                "authored_repositories": authored_repo_count,
                "signed_commit_count": signed_commits,
                "identity_confirmed": False,
                "api_calls": ctx["calls"],
                "rate_remaining": ctx["remaining"],
                "rate_limit": ctx["limit"],
                "latency_sec": round(latency, 3),
                "deep_scan": bool(repo_details),
                "authenticated": token is not None,
                "fetched_at": time.time(),
            },
        }

    # ---- LinkedIn text stream --------------------------------------------- #
    def analyze_linkedin_text(self, text: str) -> Dict[str, Any]:
        """Ecosystem Density Scan + Peer-Attestation Verification Matrix over pasted LinkedIn text."""
        text = text or ""
        milestones = {term: min(LINKEDIN_TERM_CAP, len(rx.findall(text))) for term, rx in LINKEDIN_MILESTONES.items()}
        milestones = {t: c for t, c in milestones.items() if c > 0}
        attestations = {term: min(LINKEDIN_TERM_CAP, len(rx.findall(text)))
                        for term, (rx, _) in LINKEDIN_ATTESTATIONS.items()}
        attestations = {t: c for t, c in attestations.items() if c > 0}

        # density: 60 % coverage of distinct milestone types, 40 % capped frequency
        distinct_ratio = len(milestones) / len(LINKEDIN_MILESTONES)
        freq_ratio = min(1.0, sum(milestones.values()) / 10.0)
        density = 0.6 * distinct_ratio + 0.4 * freq_ratio

        attest_weight = sum(LINKEDIN_ATTESTATIONS[t][1] * c for t, c in attestations.items())
        return {
            "provided": bool(text.strip()),
            "chars": len(text),
            "milestones": milestones,
            "attestations": attestations,
            "density": round(density, 4),
            "attestation_weight": round(attest_weight, 2),
            "milestones_active": bool(milestones),
            "attestations_active": bool(attestations),
        }

    @staticmethod
    def _apply_linkedin_signals(metrics: Dict[str, Dict[str, Any]], linkedin: Dict[str, Any]) -> None:
        """Fold LinkedIn evidence into the existing 12-D dictionary (in place).
        Both boosts are bounded and are applied ON TOP of the GitHub-derived base value:
          ecosystem: base + (1 - base) * 0.6 * density
          integrity: base * min(1.15, 1 + 0.05 * attestation_weight)   (a 0 base stays 0)
        """
        if linkedin["milestones_active"]:
            m = metrics["ecosystem"]
            base = m["value"]
            m["base_value"] = base
            m["value"] = round(_clip(base + (1.0 - base) * ECOSYSTEM_MAX_LIFT * linkedin["density"]), 4)
            m["display"] = f"{LINKEDIN_VERIFIED_LABEL} \u00b7 {m['display']}"
        if linkedin["attestations_active"]:
            m = metrics["integrity"]
            base = m["value"]
            m["base_value"] = base
            multiplier = min(INTEGRITY_MAX_MULTIPLIER, 1.0 + 0.05 * linkedin["attestation_weight"])
            m["value"] = round(_clip(base * multiplier), 4)
            m["display"] = f"{LINKEDIN_VERIFIED_LABEL} \u00b7 {m['display']}"

    # ---- the 12 dimensions ------------------------------------------------ #
    def _compute_metrics(self, repos: List[dict], repo_details: Dict[str, Dict[str, Any]], claimed: List[str],
                         evidence: Dict[str, int], strength: Dict[str, float], baseline: List[str],
                         missing: List[str]) -> Dict[str, Dict[str, Any]]:
        total = len(repos)
        originals = [r for r in repos if not r.get("fork")]
        forked = total - len(originals)
        authored_repositories = [
            repo for repo in originals
            if repo_details.get(str(repo.get("full_name") or ""), {}).get("total_contributions", 0) > 0
        ]
        labels = dict(DIMENSIONS)

        def pack(key: str, value: float, display: str) -> Dict[str, Any]:
            return {"label": labels[key], "value": round(_clip(value), 4), "display": display}

        # 1. Consistency: original repositories with commits attributed to this GitHub account
        consistency = pack("consistency", len(authored_repositories) / 8.0,
                           f"{len(authored_repositories)} scanned repos with account-attributed commits")

        # 2. Diversity: languages from non-fork repos, enriched by language API calls
        languages = {str(r["language"]).lower() for r in originals if r.get("language")}
        for detail in repo_details.values():
            languages.update(detail.get("languages", []))
        tech_depth = pack("tech_depth", len(languages) / 6.0, f"{len(languages)} unique languages")

        # 3. Frameworks: keyword scan across repo metadata and README text
        fw_found = set()
        for repo in originals:
            if _FRAMEWORK_REGEX:
                corpus = self._repo_corpus(repo) + " " + _norm(
                    repo_details.get(str(repo.get("full_name") or ""), {}).get("readme", "")
                )
                fw_found.update(m.group(0) for m in _FRAMEWORK_REGEX.finditer(corpus))
        frameworks = pack("frameworks", len(fw_found) / 6.0, f"{len(fw_found)} frameworks detected")

        # 4. Breadth: descriptive content available on original repositories
        chars = sum(len(r.get("name") or "") + len(r.get("description") or "") +
                    len(" ".join(r.get("topics") or [])) + len(
                        repo_details.get(str(r.get("full_name") or ""), {}).get("readme", "")
                    ) for r in originals)
        breadth = pack("breadth", math.log1p(chars) / math.log1p(2500.0), f"{chars} chars of repo text")

        # 5. Claims integrity: strict cross-reference of resume claims vs GitHub evidence
        if claimed:
            weights = {s: (STRICT_WEIGHT if s in STRICT_CLAIM_SKILLS else 1.0) for s in claimed}
            ok_weight = sum(w for s, w in weights.items() if evidence[s] > 0)
            integrity_val = ok_weight / sum(weights.values())
            n_ok = sum(1 for s in claimed if evidence[s] > 0)
            integrity = pack("integrity", integrity_val, f"{n_ok}/{len(claimed)} claims have matching public-repo signals")
        else:
            integrity = pack("integrity", 0.0, "no skills detected in resume")

        # 6. Products: original repositories with at least one commit attributed to this account
        unique_originals = len({r.get("full_name") for r in authored_repositories})
        products = pack("products", unique_originals / 8.0,
                        f"{unique_originals} original repos with account-attributed commits")

        # 7. Deployment: cloud / deploy anchors in text, or a live homepage URL
        deploy_repos = 0
        for repo in originals:
            if (_DEPLOY_REGEX and _DEPLOY_REGEX.search(self._repo_corpus(repo))) or (repo.get("homepage") or "").strip():
                deploy_repos += 1
        deployment = pack("deployment", deploy_repos / 4.0, f"{deploy_repos} repos with deploy signals")

        # 8. Contribution density: breadth of repos with commits linked to the account
        authored_commit_count = sum(
            detail.get("total_contributions", 0) for detail in repo_details.values()
        )
        collaboration = pack("collaboration", min(1.0, len(authored_repositories) / 5.0),
                             f"{len(authored_repositories)} repos; {authored_commit_count} sampled account-attributed commits")

        # 9. Documentation: README and description coverage across original repos
        documented = [
            r for r in originals
            if (r.get("description") or "").strip()
            or repo_details.get(str(r.get("full_name") or ""), {}).get("readme")
        ]
        desc_lengths = [len((r.get("description") or "").strip()) for r in documented]
        non_empty = [d for d in desc_lengths if d > 0]
        coverage = (len(documented) / len(originals)) if originals else 0.0
        mean_len = (sum(non_empty) / len(non_empty)) if non_empty else 0.0
        readmes = sum(bool(repo_details.get(str(r.get("full_name") or ""), {}).get("readme")) for r in originals)
        documentation = pack("documentation", 0.5 * coverage + 0.5 * _clip(mean_len / 90.0),
                             f"{coverage:.0%} have a README or description; {readmes} README files scanned")

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
