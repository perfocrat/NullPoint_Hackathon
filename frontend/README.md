# CareerLens

CareerLens is a DATAQUEST 3.0 project. The web experience uses Next.js App
Router, React, TypeScript, and Tailwind CSS. Its Flask API calls the shared
resume and GitHub evidence analyzer in `backend/portfolio_analyzer.py`.

## Project layout

- `app/`, `components/`, and `lib/` contain the Next.js application.
- `backend/` contains the Flask analysis engine, resume readers, the original
  Streamlit interface, and optional market-model training scripts.
- `legacy-static/` preserves the original HTML/CSS/JavaScript pages; the active
  site is the Next.js application.
- `app.py` runs the Flask API on port 5000. Next.js proxies `/api/*` requests
  to that API.

## Run locally

From the repository root, create a Python environment and install the API
dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r frontend/requirements.txt
```

Start the API in one terminal from the repository root:

```powershell
.\.venv\Scripts\python.exe frontend/app.py
```

From a second terminal, start the web app:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:3000`; the Flask root at port 5000 redirects there.
Submit a PDF or DOCX resume, a public GitHub profile URL, and a target role.
The Flask API extracts resume text, fetches up to 300 public repositories from
GitHub, compares the evidence with the selected role, and returns the report to
the Next.js app. Optional LinkedIn activity text is analyzed locally. Check
`http://127.0.0.1:5000/api/health` to confirm the API is running.

The Flask process needs outbound access to `api.github.com`. A standard scan
reviews the public profile and up to 300 repositories, plus one page of recent
public activity. The detailed scan is on by default; it reads language
breakdowns, README text, contributor totals, and one page of up to 100
default-branch commits attributed by GitHub to the profile. Without a server
token, detailed scans cover up to five non-fork repositories and sample commit
change stats in two; with `GITHUB_TOKEN`, they can cover up to 12 and sample
two commit diffs. The report shows the actual scan count and limit. Set
`CAREERLENS_DEEP_SCAN=0` to disable per-repository inspection. If GitHub's
rate limit is reached, set `GITHUB_TOKEN` in the Flask environment. Keep the
token on the server; the browser never receives it. This token raises API
limits only; it does not sign in the candidate or verify that they own the
profile being analyzed.

### Add a local GitHub token

Copy `frontend/.env.example` to `frontend/.env.local`, then put your token after
`GITHUB_TOKEN=` in `.env.local`. The Flask API reads this file when it starts;
the file is ignored by Git. Restart the Flask API after changing it. You can
also set `GITHUB_TOKEN` in the API process environment, which takes precedence
over `.env.local`. Never put the token in frontend code, a browser environment
variable, or a committed file.

Commit attribution and signature status are GitHub signals, not proof that the
resume owner controls the account or wrote original code. The public-evidence
score is capped at 85. The report excludes forks from skill evidence and links
the scanned projects and sample commits so reviewers can inspect the sources.
It does not compare source code against every public GitHub repository. GitHub's
own [code search](https://docs.github.com/en/code-security/reference/security-incident-response/investigation-tools#github-code-search)
requires a signed-in user for public searches and searches only indexed default
branches; it is not a complete plagiarism check.

PDF and DOCX resumes are supported. Legacy `.doc` files are not supported.

## Optional market model

The live analyzer does not require the model. To run the preserved Streamlit
interface or train the market model, install `backend/requirements-ml.txt`.
From the `frontend` folder, install those optional dependencies. Place the
ResumeRishi dataset at `backend/data/market_jds.csv`, then run:

```powershell
python backend/train_market_engine.py
```

The training script writes `backend/market_latent_space.pth`.
