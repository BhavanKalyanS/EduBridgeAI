# EduBridge AI

EduBridge AI is a stage-aware multilingual learning MVP for CBSE Class 10. It tracks concept understanding (`M`) separately from English-keyword understanding (`L`) and selects one of five authored support stages per student and concept. The app includes a Flask API, a React/Vite frontend, and MongoDB Atlas persistence.

The starter curriculum contains 22 original sample concepts. An optional importer can load chapter PDFs supplied by the operator into Atlas. The textbook ZIPs are not included in this repository; the supplied set currently covers First Flight English, Mathematics, Science, and Democratic Politics chapters, not the complete CBSE Class 10 book list.

**Phase 1 only:** authentication and four roles, curriculum, lessons and quizzes, BKT and rule-based stage control, validated answer events, student/teacher/parent/admin dashboards, Docker, tests, and CI. The tutor and offline event-sync endpoints are explicit 501 placeholders. There are no LLM calls, embeddings, vector database, offline packs, support scoring, voice features, or tuned learning parameters.

The BKT values and stage thresholds are configurable defaults, not validated or tuned parameters. No controlled field study has been run, and the project makes no learning-outcome claims. Use synthetic data only in development and testing. Confirm institutional approval and parental-consent procedures before any use with real minors.

## Requirements

- MongoDB Atlas development cluster and database user.
- Docker Desktop with Docker Compose **or** Python 3.12 and Node.js 26 LTS for running services directly on the host.
- Git and a modern browser.
- For textbook import only: the relevant textbook ZIP archives, Python dependencies, and permission to reproduce and display that material in this app.

Do not commit `.env`, credentials, or textbook archives to GitHub. Never use a production Atlas database for development, seed scripts, or tests.

## Configure MongoDB Atlas

1. Create a development cluster and a database user in Atlas.
2. In Atlas Network Access, allow the IP address of the machine that will run the backend. Avoid `0.0.0.0/0` except for a temporary, controlled test.
3. Copy `.env.example` to `.env` in the repository root.
4. Set `MONGO_URI` to the Atlas SRV connection string targeting the `edubridge` database. URL-encode special characters in the database password.
5. Replace the local Flask and JWT secret values with separate random secrets. Keep `.env` private; it is ignored by Git.

Example PowerShell setup:

```powershell
Copy-Item .env.example .env
notepad .env
```

`TEST_MONGO_URI` is optional and must point to a separate disposable Atlas database with `test` in its name. Integration tests drop that database's data. Do not set it to `MONGO_URI`.

The backend reads `MONGO_URI` for runtime data and initializes database indexes when the Docker backend starts. `APP_ENV=production` requires non-default Flask and JWT secrets.

## Quick start with Docker Compose

Run these commands from the repository root after configuring `.env`:

```powershell
docker compose -f infra/docker-compose.yml up --build -d
docker compose -f infra/docker-compose.yml ps
```

The Compose file starts the backend and Vite frontend; it does not start a local MongoDB service. The backend waits for Atlas health before the frontend starts.

### Load curriculum and demo accounts

The initial Docker startup creates indexes but does not seed curriculum or demo accounts. Load the starter curriculum and synthetic accounts:

```powershell
docker compose -f infra/docker-compose.yml exec backend python scripts/seed_curriculum.py
docker compose -f infra/docker-compose.yml exec backend python scripts/seed_users.py
```

The scripts write to the Atlas database in `MONGO_URI`. Rerunning `seed_users.py` resets the documented demo passwords and demo-account details, rebuilds the demo class roster, and seeds synthetic mastery records. Use a development database only.

### Import supplied textbook ZIPs (optional)

The textbook ZIPs are intentionally not stored in Git. Place the archives at the repository root using these exact names:

```text
English BOOK.zip
Maths Book.zip
Science book.zip
SOCIAL BOOK.zip
```

From the repository root, install the backend requirements into the host Python environment if needed, then run:

```powershell
python -m pip install -r backend/requirements.txt
python -m scripts.import_textbooks
```

The importer connects using root `.env` and upserts records in Atlas. It stores extracted text and source metadata in `textbook_sources`, original PDFs in Atlas GridFS, and approved chapter entries in the curriculum. It does not delete user or curriculum data. Re-running it replaces the matching source records and reuses unchanged PDF files. Only import content you are authorized to reproduce and display.

The current archives contain 41 chapter PDFs and 8 supplementary PDFs: 9 English, 14 Mathematics, 13 Science, and 5 Political Science chapter PDFs. They do not contain every Class 10 CBSE English or Social Science textbook. Imported lessons display extracted English text; the original PDF is available from the lesson view for its layout and illustrations. This importer does not translate textbook material.

When textbook chapters are imported, student curriculum routes prefer those chapters over the 22 starter samples. If importing from a fresh database, run `seed_users.py` after importing the curriculum so demo progress is generated for the imported chapters too.

### Open the app

- Frontend: [http://localhost:5173](http://localhost:5173)
- API health: [http://localhost:5000/api/health](http://localhost:5000/api/health)
- API contract: [`backend/openapi.yaml`](backend/openapi.yaml)

The health endpoint should return `{"status":"ok","database":"connected"}`. Public sign-up is limited to student accounts. Teacher, parent, and admin accounts must be created by a school administrator.

## Run without Docker

Open two PowerShell terminals at the repository root. Ensure `.env` has been configured first.

### Backend

Create and activate a Python 3.12 virtual environment, install dependencies, initialize indexes, then start Flask:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements-dev.txt
python -m backend.db_init
python -m backend.app
```

The API listens on port `5000`.

### Frontend

In the second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

The Vite development server listens on port `5173` and uses `http://localhost:5000/api` by default. To use a different API address, set `VITE_API_URL` before starting Vite.

### Seed Atlas from a host-based setup

With the Python virtual environment active and `.env` configured, run these commands from the repository root. To use supplied textbook chapters, import them before seeding users so demo progress is generated for the imported chapters:

```powershell
python -m scripts.seed_curriculum
# Optional; requires the textbook ZIPs described above
python -m scripts.import_textbooks
python -m scripts.seed_users
```

These commands write to the same Atlas database configured in `.env`. Run them only against a development database.

## Demo accounts

After running `seed_users.py`, all seeded accounts use the local development password `EduBridgeDemo!2026`:

| Role | Email |
| --- | --- |
| Student | `student@example.com` |
| Student | `student2@example.com` |
| Student | `student3@example.com` |
| Teacher | `teacher@example.com` |
| Parent | `parent@example.com` |
| Admin | `admin@example.com` |

These are synthetic demo accounts, not production credentials. Reset or remove them before any non-development use.

## Stop, inspect, and restart Docker services

Run commands from the repository root:

```powershell
# Follow service logs
docker compose -f infra/docker-compose.yml logs -f backend frontend

# Restart services after configuration changes
docker compose -f infra/docker-compose.yml restart

# Stop services without deleting Atlas data
docker compose -f infra/docker-compose.yml down

# Rebuild images after code or dependency changes
docker compose -f infra/docker-compose.yml up --build -d
```

`docker compose down` stops and removes local containers and networks; Atlas data is remote and is not deleted by it.

## Troubleshooting

- **Compose reports that `MONGO_URI` is missing:** make sure `.env` is in the repository root and contains a valid `mongodb+srv://` URI.
- **Atlas health returns 503 / database unavailable:** verify the Atlas cluster is running, the database username/password are correct, special password characters are URL-encoded, and the backend machine's IP is allowed in Atlas Network Access. Check backend logs with the Compose logs command above.
- **Frontend cannot reach the API:** verify backend health at `http://localhost:5000/api/health`; check that `VITE_API_URL` points to the API address reachable by the browser.
- **No lessons appear:** seed the starter curriculum or run the textbook importer, then sign in with a student account.
- **Textbook import cannot find ZIPs:** place each archive in the repository root with the exact filenames listed above. The ZIPs are not supplied by GitHub.
- **PDF text extraction fails:** ensure the archive contains valid, readable PDFs. The importer stops and reports the affected file instead of silently skipping it.
- **Port 5000 or 5173 is occupied:** stop the process using the port or adjust the port mappings in `infra/docker-compose.yml`.

## Tests and checks

Backend (Python 3.12 is the CI target):

```powershell
python -m pip install -r backend/requirements-dev.txt
python -m pytest backend/tests --cov=backend.services.bkt --cov=backend.services.stage_controller --cov=backend.services.event_validator --cov-report=term-missing --cov-fail-under=85
ruff check backend scripts
```

API integration tests use `TEST_MONGO_URI` for a separate Atlas database with `test` in its name and skip when it is not configured. The tests delete data in that database, so never point it at development, staging, or production data. GitHub Actions uses the `TEST_MONGO_URI` secret when configured.

Frontend checks require Node.js 26 LTS:

```powershell
cd frontend
npm ci
npm run lint
npm test
npm run build
```

## Architecture

- `backend/`: Flask API, blueprints, pure learning services, Pydantic schemas, tests, and OpenAPI contract.
- `frontend/`: React/Vite SPA, role routes, five UI locales, and dashboards.
- `infra/`: Docker Compose configured to use MongoDB Atlas; no local MongoDB service is included.
- `scripts/`: curriculum, synthetic account, and optional textbook import scripts.
- `.github/`: pull-request CI and ownership/review templates.

Tamil and English starter lesson content is included. Malayalam, Kannada, and Telugu starter content is marked `TODO_REVIEW` and uses the Tamil fallback until a fluent reviewer approves translations. Imported textbook source text is in English unless the source PDFs themselves provide otherwise.

## Collaboration

Use a short `feat/...` or `fix/...` branch, open a pull request, wait for CI, and request review from the other owner. Protect `main` in GitHub with required pull requests and one approval. Backend ownership is assigned to Bhavan Kalyan S and frontend ownership to Vishak P in `.github/CODEOWNERS`.
