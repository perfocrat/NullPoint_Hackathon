"""
app.py -- CareerLens web server (Flask). Serves the frontend and the analysis API.

Run:   python app.py        then open http://127.0.0.1:5000
Env:   GITHUB_TOKEN (optional) raises the GitHub rate limit from 60 to 5,000 requests/hour.
"""
import os
# FIXED: Hardcode the environment string at the root entry point so background threads see it
os.environ["GITHUB_TOKEN"] = "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"


from flask import Flask, jsonify, request, send_from_directory

import analysis_service as svc

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 11 * 1024 * 1024  # frontend limit is 10 MB + form overhead


def _error(message: str, status: int):
    return jsonify({"success": False, "error": message}), status


# ------------------------------ frontend ---------------------------------- #
@app.route("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:path>")
def serve_frontend(path):
    return send_from_directory(FRONTEND_DIR, path)


# --------------------------------- API ------------------------------------ #
@app.route("/api/analyze", methods=["POST"])
def analyze():
    """Validate the form and start a background analysis. Returns a job id immediately."""
    resume = request.files.get("resume")
    github = request.form.get("github", "").strip()
    linkedin_text = request.form.get("linkedinText", "")
    role_key = request.form.get("targetRole", "")

    if not resume or not resume.filename:
        return _error("Resume is required.", 400)
    if role_key not in svc.ROLE_TO_TRACK:
        return _error("Please select a valid target role.", 400)
    if not github:
        return _error("A GitHub profile is required: skills are verified against your public repositories.", 400)

    job_id = svc.start_job(resume.filename, resume.read(), github, linkedin_text, role_key)
    return jsonify({"success": True, "jobId": job_id}), 202


@app.route("/api/status/<job_id>")
def status(job_id):
    job = svc.get_job(job_id)
    if not job:
        return _error("Unknown or expired analysis.", 404)
    body = {"success": True, "status": job["status"], "stage": job["stage"], "totalStages": svc.STAGES}
    if job["status"] == "error":
        body["error"] = job.get("error", "Analysis failed.")
    return jsonify(body)


@app.route("/api/result/<job_id>")
def result(job_id):
    job = svc.get_job(job_id)
    if not job:
        return _error("Unknown or expired analysis.", 404)
    if job["status"] != "done":
        return _error("Analysis is not finished yet.", 409)
    return jsonify({"success": True, "analysis": job["result"]})


@app.errorhandler(413)
def too_large(_):
    return _error("File is too large (max 10 MB).", 413)


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)

