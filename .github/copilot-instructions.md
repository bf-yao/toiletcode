# Workspace instructions

- This is a Traditional Chinese FastAPI + Leaflet prototype for recording restroom codes in European countries.
- Local records are stored in `data/records.json`; Vercel deployments must not claim filesystem writes are persistent.
- Run locally with `uvicorn api.index:app --reload` after installing `requirements.txt`.
