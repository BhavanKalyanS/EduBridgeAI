# EduBridge AI

EduBridge AI is a stage-aware multilingual learning MVP for Grade 9 Mathematics. It tracks concept understanding (`M`) separately from English-keyword understanding (`L`) and selects one of five authored support stages per student and concept.

**Phase 1 only:** authentication and four roles, curriculum, lessons and quizzes, BKT and rule-based stage control, validated answer events, student/teacher/parent/admin dashboards, Docker, tests, and CI. The tutor and offline event-sync endpoints are explicit 501 placeholders. There are no LLM calls, embeddings, vector database, offline packs, support scoring, voice features, or tuned learning parameters.

The BKT values and stage thresholds are configurable defaults, not validated or tuned parameters. No controlled field study has been run, and the project makes no learning-outcome claims. Use synthetic data only in development and testing. Confirm institutional approval and parental-consent procedures before any use with real minors.

## Run locally

Prerequisites: Docker Desktop with Compose, Git, and a modern browser. Node.js 26 LTS is needed only for running the frontend outside Docker.

1. Copy `.env.example` to `.env` and replace the local secret values.
2. From the repository root, start the services:

   ```powershell
   docker compose -f infra/docker-compose.yml up --build -d
   ```

3. Load the sample curriculum and synthetic accounts:

   ```powershell
   docker compose -f infra/docker-compose.yml exec backend python scripts/seed_curriculum.py
   docker compose -f infra/docker-compose.yml exec backend python scripts/seed_users.py
   ```

4. Open [http://localhost:5173](http://localhost:5173). The API health check is at [http://localhost:5000/api/health](http://localhost:5000/api/health).

The seed scripts are for local demonstration only. They reset demo-account passwords when rerun and create synthetic progress records; do not run them against staging or production data.

## Demo accounts

All seeded accounts use `EduBridgeDemo!2026` locally:

| Role | Email |
| --- | --- |
| Student | `student@example.com` |
| Student | `student2@example.com` |
| Student | `student3@example.com` |
| Teacher | `teacher@example.com` |
| Parent | `parent@example.com` |
| Admin | `admin@example.com` |

## Tests and checks

Backend (Python 3.12 is the CI target):

```powershell
python -m pip install -r backend/requirements-dev.txt
python -m pytest backend/tests --cov=backend.services.bkt --cov=backend.services.stage_controller --cov=backend.services.event_validator --cov-report=term-missing --cov-fail-under=85
ruff check backend scripts
```

API integration tests use `TEST_MONGO_URI` and skip when MongoDB is unavailable. To run the frontend checks outside Docker, use Node 26 LTS:

```powershell
cd frontend
npm install
npm run lint
npm test
npm run build
```

## Architecture

- `backend/`: Flask API, blueprints, pure learning services, Pydantic schemas, tests, and OpenAPI contract.
- `frontend/`: React/Vite SPA, role routes, five UI locales, and dashboards.
- `infra/`: local Docker Compose.
- `scripts/`: synthetic curriculum and account seeders.
- `.github/`: pull-request CI and ownership/review templates.

See [`backend/openapi.yaml`](backend/openapi.yaml) for the API contract. Tamil and English sample lesson content is included. Malayalam, Kannada, and Telugu content is marked `TODO_REVIEW` and displays the Tamil fallback until a fluent reviewer approves translations.

## Collaboration

Use a short `feat/...` or `fix/...` branch, open a pull request, wait for CI, and request review from the other owner. Protect `main` in GitHub with required pull requests and one approval. Backend ownership is assigned to Bhavan Kalyan S and frontend ownership to Vishak P in `.github/CODEOWNERS`.