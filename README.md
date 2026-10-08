# CareerLens

**AI-powered career readiness analyzer.** CareerLens checks the skills on your resume against your live public GitHub footprint, scores how ready you are for a target role, and generates a roadmap to close the gaps.

Built for DataQuest 3.0.

Instead of trusting keywords on a resume, CareerLens asks for evidence. A skill only counts as verified if your public repositories actually show it.

## Features

- **Evidence verification:** every skill found on the resume is cross-checked against your GitHub repositories (languages, names, descriptions, topics, and optionally per-repo language breakdowns).
- **Job readiness score (0-100):** an explainable score computed from 12 measured dimensions, compared against the targets for your chosen role.
- **Skill gap analysis:** missing skills for the target role, resume claims with no evidence, and weak dimensions, each with a concrete next step.
- **Role fit:** the same evidence scored against each career track, so you can see where you fit best.
- **Personalized roadmap:** ordered phases built from your gaps.
- **LinkedIn signals (optional):** paste LinkedIn text and milestone or endorsement language gives a small, capped boost.
- **Market latent space (optional):** a conditional VAE trained on a resume corpus reports how typical your resume is of the market. It is informational and is not part of the score.

## How it works

```
input.html  --POST /api/analyze-->  Flask starts a background job, returns a jobId
loading.html --polls /api/status/<jobId>-->  real progress (resume, GitHub, scoring, roadmap)
dashboard.html --GET /api/result/<jobId>-->  score, breakdown, skills, gaps, roles, roadmap
```

1. The resume (PDF or DOCX) is converted to text.
2. `portfolio_analyzer.py` calls the GitHub REST API for the user's public repositories and computes the 12 dimensions.
3. `analysis_service.py` scores the result against the target track and reshapes it into the JSON the dashboard renders.

### The 12 dimensions

| Dimension | What it measures |
|---|---|
| Consistency | Number of public repositories |
| Tech depth | Number of distinct languages |
| Framework complexity | Frameworks detected in repo names, descriptions and topics |
| Structural breadth | Volume of descriptive repo text |
| Claims integrity | Share of resume claims verified on GitHub (expensive-to-fake skills such as Docker, SQL, AWS weigh double) |
| Shipped products | Original, non-forked repositories |
| Deployment footprint | Repos with deploy keywords or a live homepage |
| Collaboration density | Forked repos as a share of all repos |
| Documentation quality | Description coverage and length |
| Domain proximity | Distance between your evidenced skills and the track baseline |
| Gap accessibility | How many baseline skills are missing entirely |
| Ecosystem | Stars and forks received (plus capped LinkedIn lift) |

### Scoring

For each dimension, `shortfall = max(0, target - value) / target`. The score is:

```
distance  = 0.5 * RMS(shortfalls) + 0.5 * mean(shortfalls)
readiness = 100 * (1 - distance)
```

Exceeding a target is never penalised and never rewarded twice. The dashboard's five breakdown bars group the 12 dimensions (each used exactly once) and show attainment against target.

### Career tracks

| Track | Baseline skills |
|---|---|
| Core Software Engineer | Python, JavaScript, Git, SQL, Docker |
| Data Scientist / AI Engineer | Python, PyTorch, Git, Linux, AWS |
| UI/UX Product Architect | Figma, HTML, CSS, Tailwind, JavaScript |

The form offers six roles, which map onto these three tracks: Backend, Full Stack and Software Engineer map to Core Software Engineer; Data Scientist and ML Engineer map to Data Scientist / AI Engineer; Frontend maps to UI/UX Product Architect. The mapping is in `ROLE_TO_TRACK` in `analysis_service.py`.

## Getting started

### Requirements

- Python 3.10+
- Internet access (the analyzer calls `api.github.com`)

### Install and run

```bash
git clone <your-repo-url>
cd careerlens
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000.

### GitHub token (recommended)

Unauthenticated GitHub requests are limited to 60 per hour. A personal access token raises that to 5,000 per hour and enables the deep language scan (reads each repo's language breakdown, which surfaces Dockerfiles, shell scripts and CSS).

```bash
export GITHUB_TOKEN=ghp_your_token      # Windows PowerShell: $env:GITHUB_TOKEN="ghp_your_token"
python app.py
```

The token stays on the server and is only sent to `api.github.com`. A token with no scopes is enough for public data.

## Training the market model (optional)

The app works without this. To enable the market-typicality readout:

1. Download the ResumeRishi resume dataset from Kaggle and save it as `data/market_jds.csv`.
2. Install the extra dependencies: `pip install torch numpy pandas`
3. Train:

```bash
python train_market_engine.py                 # 25 epochs
python train_market_engine.py --epochs 40 --batch-size 128
```

This writes `market_latent_space.pth`. The model is a 12-condition recurrent VAE: a BiLSTM encoder and an LSTM decoder, with the 12 text-derived market parameters concatenated to the input at every time step. Resume text is tokenized, encoded to a 128-dimensional latent code, and compared to the corpus centroid.

## API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/analyze` | Multipart form: `resume` (file), `github`, `targetRole`, optional `linkedinText`. Returns `202` with `{ "jobId": "..." }`. |
| `GET` | `/api/status/<jobId>` | `{ status: "running" \| "done" \| "error", stage, totalStages, error? }` |
| `GET` | `/api/result/<jobId>` | The dashboard payload once the job is done. |

Valid `targetRole` values: `backend-developer`, `frontend-developer`, `fullstack-developer`, `data-scientist`, `ml-engineer`, `software-engineer`.

Jobs are kept in memory for one hour.

## Project structure

```
careerlens/
├── app.py                  # Flask server and API routes
├── analysis_service.py     # Resume parsing, scoring, roadmap, background jobs
├── portfolio_analyzer.py   # GitHub extraction and the 12 dimensions
├── core_model.py           # Conditional VAE, tokenizer, checkpoint helpers
├── train_market_engine.py  # Offline training script
├── requirements.txt
├── data/                   # Put market_jds.csv here for training
└── frontend/
    ├── index.html          # Landing page
    ├── input.html          # Profile form
    ├── loading.html        # Live analysis progress
    ├── dashboard.html      # Results
    ├── css/
    └── js/                 # api.js is shared by the input, loading and dashboard pages
```

## Limitations

- **Public GitHub only.** Private work is invisible, so strong engineers with mostly private repos will score low.
- **Keyword-based evidence.** Skills are matched from repo languages, names, descriptions and topics, not from reading code. Well-labelled repos score better than well-written but unlabelled ones.
- **Resume formats.** PDF and DOCX only. Scanned or image-only resumes cannot be read, and legacy `.doc` files are not supported.
- **LinkedIn is not scraped.** Users paste text, so the signal is self-supplied and its effect is capped (ecosystem lift at most 60% of headroom, integrity at most +15%).
- **Approximate role mapping.** Six form roles share three scoring tracks.
- **In-memory jobs.** Results disappear on server restart and the job store is not shared across workers, so run a single process.
- **Roadmap timing.** "Week N" labels are sequential markers, not time estimates.

## Tech stack

Python, Flask, vanilla HTML/CSS/JavaScript, GitHub REST API, PyTorch (optional).

