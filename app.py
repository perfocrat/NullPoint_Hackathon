import os
from flask import Flask, send_from_directory, jsonify, request
from backend.portfolio_analyzer import PortfolioAnalyzer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app = Flask(__name__)

analyzer = PortfolioAnalyzer()


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
    linkedin = request.form.get("linkedin", "")
    target_role = request.form.get("targetRole", "")

    if not resume:
        return jsonify({
            "success": False,
            "error": "Resume is required."
        }), 400

    if not github:
        return jsonify({
            "success": False,
            "error": "GitHub URL is required."
        }), 400

    if not target_role:
        return jsonify({
            "success": False,
            "error": "Target role is required."
        }), 400

    # Read resume
    try:
        if resume.filename.lower().endswith(".pdf"):
            from pypdf import PdfReader
            import io

            reader = PdfReader(io.BytesIO(resume.read()))

            resume_text = "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )
        else:
            resume_text = resume.read().decode("utf-8", errors="ignore")

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Could not read resume: {str(e)}"
        }), 400

    # Send data to the real CareerLens analysis engine
    result = analyzer.post_analyze_candidate({
        "resume_text": resume_text,
        "github_url": github,
        "track": target_role,
        "github_token": "",
        "deep_scan": False,
        "linkedin_text": linkedin
    })

    if not result.get("ok"):
        return jsonify({
            "success": False,
            "error": result.get("error", "Analysis failed.")
        }), 400

    return jsonify({
        "success": True,
        "analysis": result
    })


if __name__ == "__main__":
    app.run(debug=True)