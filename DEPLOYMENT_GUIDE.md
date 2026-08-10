# Beginner Deployment Guide — Carolina EDGE Library API v0.1

## A. GitHub
1. Create repository: `carolina-edge-library-api`.
2. Upload every file/folder from this package, preserving `app/`, `data/`, and `tests/`.
3. Commit with message: `Initial Carolina EDGE Library API v0.1`.

## B. Render
Recommended: use the repository's `render.yaml` Blueprint.

If creating manually:
- Service type: Web Service
- Runtime: Python
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health Check Path: `/health`

Create a PostgreSQL database in Render and set `DATABASE_URL` to its connection string.
Set `WRITE_API_KEY` to a long random secret.

## C. Verify
Open:
- `/health` — should show version `0.1.0` and `drills: 25`.
- `/docs` — interactive API documentation.
- `/v1/drills?limit=5` — returns drills.
- `/v1/drills/RT-021` — returns Retrieval to Attack.

## D. GPT Action
Use `openapi-action.yaml`. Replace the placeholder server URL with your Render service URL before importing it into the GPT Action editor.
For write actions, configure the Action API key/header as `X-API-Key` using the same `WRITE_API_KEY` value from Render.
