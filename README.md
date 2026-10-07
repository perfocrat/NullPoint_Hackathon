# CareerLens (Flask + HTML frontend)

    pip install -r requirements.txt
    set GITHUB_TOKEN=...        (optional; PowerShell: $env:GITHUB_TOKEN="...")
    python app.py               -> http://127.0.0.1:5000

Flow: input.html -> POST /api/analyze (returns jobId) -> loading.html polls /api/status/<id>
-> dashboard.html loads /api/result/<id>.

Optional: put your Kaggle CSV in data/market_jds.csv and run `python train_market_engine.py`
to create market_latent_space.pth (needs torch, numpy, pandas). Retired: CareerLens.py (Streamlit).
