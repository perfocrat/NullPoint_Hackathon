from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, redirect, request

from backend.portfolio_analyzer import PortfolioAnalyzer
from backend.reporting import ROLE_TRACKS, build_career_analysis
from backend.resume_reader import ResumeReadError, extract_resume_text


def load_local_secrets() -> None:
    """Load the optional ignored local config without adding a dotenv dependency."""
    config_path = Path(__file__).with_name(".env.local")
    try:
        lines = config_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return

    for line in lines:
        key, separator, value = line.partition("=")
        key = key.strip()
        # An empty inherited variable should not shadow the local token file.
        # A non-empty process environment value still takes precedence.
        if separator and key == "GITHUB_TOKEN" and not os.environ.get(key, "").strip():
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            if value:
                os.environ[key] = value


load_local_secrets()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 11 * 1024 * 1024


@app.get("/")
def home():
    """Keep the old Flask address useful while Next serves the actual UI."""
    return redirect("http://127.0.0.1:3000", code=302)


@app.get("/api/health")
def health():
    return jsonify({"success": True, "service": "careerlens-api"})


@app.errorhandler(413)
def request_too_large(_error):
    return jsonify({"success": False, "error": "Your resume must be smaller than 10 MB."}), 413


@app.post("/api/analyze")
def analyze():
    resume = request.files.get("resume")
    github_url = request.form.get("github", "").strip()
    target_role = request.form.get("targetRole", "").strip()

    if not resume or not resume.filename:
        return jsonify({"success": False, "error": "A resume is required."}), 400
    if not github_url:
        return jsonify({"success": False, "error": "Add your public GitHub profile link to analyze project evidence."}), 400
    if target_role not in ROLE_TRACKS:
        return jsonify({"success": False, "error": "Choose a supported target role."}), 400
    linkedin_text = request.form.get("linkedinText", "")
    if len(linkedin_text) > 10000:
        return jsonify({"success": False, "error": "LinkedIn activity text must be 10,000 characters or fewer."}), 400

    try:
        resume_text = extract_resume_text(resume.filename, resume.read())
    except ResumeReadError as error:
        return jsonify({"success": False, "error": str(error)}), 400

    try:
        result = PortfolioAnalyzer().post_analyze_candidate({
            "resume_text": resume_text,
            "github_url": github_url,
            "track": ROLE_TRACKS[target_role],
            "github_token": os.environ.get("GITHUB_TOKEN", ""),
            "deep_scan": os.environ.get("CAREERLENS_DEEP_SCAN", "1").lower() not in {"0", "false", "no"},
            "linkedin_text": linkedin_text,
        })

        if not result.get("ok"):
            return jsonify({"success": False, "error": result.get("error", "The profile analysis failed.")}), 502

        return jsonify({"success": True, "analysis": build_career_analysis(result, target_role)})
    except Exception:
        app.logger.exception("Unexpected error during CareerLens analysis")
        return jsonify({"success": False, "error": "The analysis hit an unexpected error. Please try again."}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
