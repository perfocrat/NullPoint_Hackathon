from flask import Flask, send_from_directory, jsonify, request
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app = Flask(__name__)


# =========================
# FRONTEND
# =========================

@app.route("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:path>")
def serve_frontend(path):
    return send_from_directory(FRONTEND_DIR, path)


# =========================
# ANALYSIS API
# =========================

@app.route("/api/analyze", methods=["POST"])
def analyze():

    resume = request.files.get("resume")
    github = request.form.get("github", "")
    portfolio = request.form.get("portfolio", "")
    linkedin = request.form.get("linkedin", "")
    target_role = request.form.get("targetRole", "")

    if not resume:
        return jsonify({
            "success": False,
            "error": "Resume is required."
        }), 400

    if not target_role:
        return jsonify({
            "success": False,
            "error": "Target role is required."
        }), 400

    # Temporary result
    analysis = {
        "score": 78,
        "targetRole": target_role,
        "scoreStatus": "Strong",

        "breakdown": {
            "skillMatch": 82,
            "projectEvidence": 78,
            "projectQuality": 74,
            "activity": 69,
            "roleRequirements": 76
        },

        "skills": [
            {
                "name": "Python",
                "status": "verified",
                "evidence": "6 repositories"
            },
            {
                "name": "SQL",
                "status": "verified",
                "evidence": "3 projects"
            }
        ],

        "gaps": [
            {
                "priority": "High Priority",
                "name": "Docker",
                "description": "Limited Docker evidence.",
                "action": "Containerize one existing project."
            }
        ],

        "roles": [
            {
                "name": "Backend Developer",
                "fit": 84,
                "primary": True,
                "description": "Strong backend alignment."
            }
        ],

        "roadmap": [
            {
                "phase": "Phase 01",
                "duration": "Week 1",
                "title": "Build a REST API",
                "description": "Create a Flask REST API.",
                "task": "Build a Flask REST API"
            }
        ]
    }

    return jsonify({
        "success": True,
        "analysis": analysis
    })


if __name__ == "__main__":
    app.run(debug=True)