# CareerLens analysis backend

`portfolio_analyzer.py` reads resume text and public GitHub repository data.
`reporting.py` converts its metrics into the report schema consumed by the
Next.js app. `resume_reader.py` extracts text from PDF and DOCX uploads.

`CareerLens.py` preserves the original Streamlit analysis view. The model
utilities in `core_model.py` and `train_market_engine.py` are optional; the
web API does not require the trained model.

For the full web application, run Flask from the parent `frontend` directory:

```powershell
python app.py
```

For the optional Streamlit view, install `requirements-ml.txt` from the parent
directory, then run:

```powershell
streamlit run backend/CareerLens.py
```
