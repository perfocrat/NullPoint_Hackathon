from __future__ import annotations

from typing import Any

from .portfolio_analyzer import DIMENSIONS, TRACK_TARGETS

ROLE_TRACKS = {
    "backend-developer": "Core Software Engineer",
    "frontend-developer": "UI/UX Product Architect",
    "fullstack-developer": "Core Software Engineer",
    "data-scientist": "Data Scientist / AI Engineer",
    "ml-engineer": "Data Scientist / AI Engineer",
    "software-engineer": "Core Software Engineer",
}

ROLE_LABELS = {
    "backend-developer": "Backend Developer",
    "frontend-developer": "Frontend Developer",
    "fullstack-developer": "Full Stack Developer",
    "data-scientist": "Data Scientist",
    "ml-engineer": "Machine Learning Engineer",
    "software-engineer": "Software Engineer",
}

SKILL_ACTIONS = {
    "Python": "Publish a small Python tool or API with a clear README.",
    "PyTorch": "Build and document a small PyTorch model.",
    "Git": "Publish a project with a clear commit history.",
    "Linux": "Add a shell automation project or Linux deployment notes.",
    "AWS": "Deploy a project to an AWS service and document the setup.",
    "Figma": "Publish a Figma prototype and link it from an implementation repo.",
    "HTML": "Ship a public page and document the structure.",
    "CSS": "Show a styled project with responsive layouts.",
    "Tailwind": "Add a Tailwind project with a responsive component set.",
    "JavaScript": "Publish a small interactive app with a live demo.",
    "SQL": "Add a project with a documented schema and useful queries.",
    "Docker": "Containerize an existing project and add a Dockerfile.",
}


MAX_PUBLIC_EVIDENCE_SCORE = 85.0


def _score(metrics: dict[str, dict[str, Any]], track: str,
           meta: dict[str, Any]) -> tuple[float, dict[str, float]]:
    shortfalls = {
        key: max(0.0, target - metrics[key]["value"]) / target
        for key, target in TRACK_TARGETS[track].items()
    }
    values = list(shortfalls.values())
    mean = sum(values) / len(values)
    rms = (sum(value * value for value in values) / len(values)) ** 0.5
    raw_score = max(0.0, min(100.0, 100.0 * (1.0 - 0.5 * rms - 0.5 * mean)))
    expected = min(int(meta.get("deep_scan_limit", 0)), int(meta.get("original_repos", 0)))
    if expected > 0:
        scan_coverage = min(1.0, int(meta.get("complete_repo_scans", 0)) / expected)
        contribution_coverage = min(1.0, int(meta.get("authored_repositories", 0)) / expected)
    else:
        scan_coverage = contribution_coverage = 0.0
    evidence_factor = 0.75 + 0.15 * scan_coverage + 0.10 * contribution_coverage
    score = min(MAX_PUBLIC_EVIDENCE_SCORE, raw_score * evidence_factor)
    return round(score, 1), shortfalls


def build_career_analysis(result: dict[str, Any], target_role: str) -> dict[str, Any]:
    track = result["track"]
    metrics = result["metrics"]
    score, shortfalls = _score(metrics, track, result["meta"])
    claimed = result["resume_skills"]
    evidenced = set(result["github_verified_skills"])
    missing = result["missing_track_skills"]
    label = ROLE_LABELS[target_role]

    skills = [
        {
            "name": skill,
            "status": "signal" if skill in evidenced else "unverified",
            "evidence": (
                "Matching signal found in a non-fork public repository. This does not verify account identity or code authorship."
                if skill in evidenced
                else "Claimed on the resume, with no matching GitHub evidence"
            ),
        }
        for skill in claimed
    ]
    for skill in result["github_verified_skills"]:
        if skill not in claimed:
            skills.append({
                "name": skill,
                "status": "observed",
                "evidence": "Matching signal found in a non-fork public repository. This does not verify account identity or code authorship.",
            })

    gaps = [
        {
            "priority": "High Priority",
            "name": skill,
            "description": f"The {track} baseline expects visible evidence for {skill}.",
            "action": SKILL_ACTIONS.get(skill, f"Publish a project that demonstrates {skill}."),
        }
        for skill in missing
    ]
    for skill in result["unverified_claims"]:
        if skill not in missing:
            gaps.append({
                "priority": "Medium Priority",
                "name": f"Verify {skill}",
                "description": f"{skill} appears on the resume but wasn't found in public GitHub evidence.",
                "action": SKILL_ACTIONS.get(skill, f"Add a public project that demonstrates {skill}."),
            })

    roadmap = [
        {
            "phase": f"Phase {index + 1:02d}",
            "duration": f"Week {index + 1}",
            "title": f"Show evidence for {skill}",
            "description": SKILL_ACTIONS.get(skill, f"Publish a project that demonstrates {skill}."),
            "task": SKILL_ACTIONS.get(skill, f"Publish a project that demonstrates {skill}."),
        }
        for index, skill in enumerate(missing[:4])
    ]
    if not roadmap:
        weakest = sorted(
            (key for key, _ in DIMENSIONS if key in shortfalls and key not in ("gap", "proximity")),
            key=lambda key: shortfalls[key],
            reverse=True,
        )
        for index, key in enumerate(weakest[:3]):
            metric = metrics[key]
            roadmap.append({
                "phase": f"Phase {index + 1:02d}",
                "duration": f"Week {index + 1}",
                "title": f"Improve {metric['label']}",
                "description": f"Current evidence: {metric['display']}.",
                "task": f"Add a focused project or improve the documentation for {metric['label'].lower()}.",
            })

    skill_match = 100.0 * len(result["verified_skills"]) / max(1, len(claimed))
    breakdown = {
        "skillMatch": round(skill_match),
        "projectEvidence": round(100 * metrics["products"]["value"]),
        "projectQuality": round(100 * metrics["documentation"]["value"]),
        "activity": round(100 * metrics["consistency"]["value"]),
        "roleRequirements": round(100 * metrics["proximity"]["value"]),
    }

    if score >= 80:
        score_status = "Strong match"
    elif score >= 65:
        score_status = "Building momentum"
    else:
        score_status = "Room to grow"

    evidenced_names = ", ".join(result["verified_skills"][:5])
    explanation = (
        f"Public GitHub profile and repository signals were compared with the {track} baseline. "
        + (f"Matching signals include {evidenced_names}. " if evidenced_names else "No resume skills matched the scanned repositories. ")
        + f"{len(missing)} baseline skill{'s' if len(missing) != 1 else ''} still need visible evidence. This public-evidence score is capped at {int(MAX_PUBLIC_EVIDENCE_SCORE)} because GitHub signals cannot confirm identity or original authorship."
    )

    return {
        "score": score,
        "targetRole": target_role,
        "scoreStatus": score_status,
        "explanation": explanation,
        "breakdown": breakdown,
        "skills": skills,
        "gaps": gaps,
        "roles": [{
            "name": label,
            "fit": round(score),
            "primary": True,
            "description": f"Matched to the {track} evidence baseline.",
        }],
        "roadmap": roadmap,
        "sources": {
            "githubUser": result["username"],
            "githubProfileName": result["profile"].get("name"),
            "githubAccountCreatedAt": result["profile"].get("created_at"),
            "githubPublicRepoCount": result["profile"].get("public_repos"),
            "githubFollowers": result["profile"].get("followers"),
            "repositoriesReviewed": result["meta"]["repos"],
            "originalRepositories": result["meta"]["original_repos"],
            "deepScannedRepositories": result["meta"]["deep_scanned_repos"],
            "deepScanLimit": result["meta"]["deep_scan_limit"],
            "completeRepositoryScans": result["meta"]["complete_repo_scans"],
            "deepScanErrors": result["meta"]["deep_scan_errors"],
            "accountAttributedRepositories": result["meta"]["authored_repositories"],
            "accountAttributedCommits": result["meta"]["contribution_commits"],
            "sampledAccountAttributedCommits": result["meta"]["authored_commit_count"],
            "signedCommitCount": result["meta"]["signed_commit_count"],
            "identityConfirmed": result["meta"]["identity_confirmed"],
            "publicActivity": {
                "available": result["public_activity"]["available"],
                "eventsReviewed": result["public_activity"]["events_reviewed"],
                "pushEvents": result["public_activity"]["push_events"],
                "pushedCommits": result["public_activity"]["pushed_commits"],
                "pullRequestsOpened": result["public_activity"]["pull_requests_opened"],
                "pullRequestsMerged": result["public_activity"]["pull_requests_merged"],
                "externalRepositories": result["public_activity"]["external_repositories"],
            },
            "apiCalls": result["meta"]["api_calls"],
            "rateLimitRemaining": result["meta"]["rate_remaining"],
            "analysisSeconds": result["meta"]["latency_sec"],
            "linkedinSignals": result["linkedin"],
            "projects": [
                {
                    "name": item["name"],
                    "url": item["url"],
                    "description": item["description"],
                    "language": item["language"],
                    "pushedAt": item["pushed_at"],
                    "languages": item["details"].get("languages", []),
                    "accountAttributedCommits": item["details"].get("total_contributions", 0),
                    "sampledAccountAttributedCommits": item["details"].get("authored_commits", 0),
                    "commitCountCapped": item["details"].get("commit_count_capped", False),
                    "signedCommits": item["details"].get("signed_commits", 0),
                    "firstAccountAttributedCommit": item["details"].get("first_authored_commit"),
                    "lastAccountAttributedCommit": item["details"].get("last_authored_commit"),
                    "sampleCommitUrls": item["details"].get("sample_commit_urls", []),
                    "accountContributionShare": item["details"].get("account_contribution_share", 0.0),
                    "totalContributors": item["details"].get("contributor_count", 0),
                    "sampleCommitAdditions": item["details"].get("sample_commit_additions", 0),
                    "sampleCommitDeletions": item["details"].get("sample_commit_deletions", 0),
                    "sampleCommitFilesChanged": item["details"].get("sample_commit_files_changed", 0),
                }
                for item in result["repository_evidence"]
                if not item["fork"] and item["details"].get("api_calls", 0) > 0
            ],
        },
    }
