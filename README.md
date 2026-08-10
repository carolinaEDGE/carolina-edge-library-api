# Carolina EDGE Library API v0.1

GitHub/Render-ready starter service for the Carolina EDGE Drill & Practice Library.

## What v0.1 does
- Seeds the first 25 legacy/canonical drill records from `Carolina_EDGE_Drill_Library_v2.0_Step3.1.xlsx`.
- Searches drills by text, game problem, family, age, ice, and goalie context.
- Retrieves a drill by stable Drill ID (`IQ-001`, `PP-006`, `RT-021`, etc.).
- Creates contextual **EDGE 5 Elements** evaluations.
- Calculates Repetitions from active-player percentage; `>=50%` is Met.
- Never blocks drill creation/use because of a low EDGE 5 Elements score.
- Stores Decision Cues and Decisions/Responses Available.
- Saves private user-created drills and practices to **My Library**.
- Separates saving from contributing. Contribution requires explicit consent.
- Creates an immutable JSON snapshot when a user submits content to the EDGE review queue.

## EDGE 5 Elements
1. Fun & Challenging
2. Age-Appropriate
3. Game-Like Context
4. Repetitions — at least 50% active at one time
5. Decisions — players read/anticipate cues and choose/respond

## Local run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export WRITE_API_KEY=dev-secret
uvicorn app.main:app --reload
```
Open `http://127.0.0.1:8000/docs`.

Without `DATABASE_URL`, local development uses SQLite. Render should use PostgreSQL via `render.yaml`.

## Render
1. Create/push a GitHub repo named `carolina-edge-library-api` with these files.
2. In Render, create from the repo using the included `render.yaml`, or create a Python web service manually.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Health check: `/health`
6. Add PostgreSQL and set `DATABASE_URL`.
7. Set a strong `WRITE_API_KEY` and use the same value in GPT Actions for write endpoints.

## Important v0.1 limits
- This is the schema/API foundation, not a public multi-user authentication system.
- `owner_key` is a caller-supplied opaque key. Before broad public rollout, add real authentication/authorization.
- The first 25 records retain source uncertainty/TBD fields rather than inventing exact player counts, time, or age limits.
- EDGE 5 Elements evaluations are contextual and informative, not certification and not a pass/fail gate.
