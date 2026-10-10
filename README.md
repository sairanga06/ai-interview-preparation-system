# CareerCraft AI — Interview & Career Preparation

CareerCraft AI is a Flask app for mock interviews, coding practice, career profiles and plans, AI career coaching, and a personal knowledge library with document search.

Existing demo: https://ai-interview-preparation-system-lk14.onrender.com/

## Run locally on Windows

1. Open PowerShell in the project folder.
2. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies and create your local environment file:

   ```powershell
   python -m pip install -r requirements.txt
   Copy-Item .env.example .env
   ```

4. Add your own `GROQ_API_KEY` to `.env` to enable AI responses. Without `DATABASE_URL`, local development uses `interview.db` in this folder.
5. Start the app:

   ```powershell
   python app.py
   ```

   Open `http://127.0.0.1:5000` in your browser. To use Flask's local debug page, set `FLASK_DEBUG=1` in your local `.env`; debug mode is disabled in production.

## Environment variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `GROQ_API_KEY` | For AI features | API key used for generated answers and feedback. |
| `DATABASE_URL` | Production | PostgreSQL connection string. If omitted locally, the app uses SQLite. |
| `SECRET_KEY` | Production | Flask session signing key; use a random value of at least 32 characters. |
| `APP_ENV` | Recommended | Set to `production` on a hosted service. |
| `ADMIN_EMAIL` | Optional | Admin account email when initializing the admin account. |
| `ADMIN_PASSWORD` | Optional | Admin account password; use at least 12 characters. |
| `CAREERCRAFT_DB_PATH` | Optional | Custom path for a local SQLite database. |

Keep real credentials in `.env` locally or in the hosting provider's secret settings. The `.env` file is ignored by Git.

## Render deployment settings

For the existing Render web service, use these settings in its dashboard:

- **Build command:** `pip install -r requirements.txt`
- **Start command:** `gunicorn app:app`
- **Health check path:** `/health`
- **Environment:** set `APP_ENV` to `production` and provide a random `SECRET_KEY` of at least 32 characters, `GROQ_API_KEY`, and your PostgreSQL `DATABASE_URL`.
- If you use the admin dashboard, configure `ADMIN_EMAIL` and a strong `ADMIN_PASSWORD` in Render's environment settings.

The application also serves `/health`, which returns success only when the configured database can answer a query. Use PostgreSQL for hosted data so it remains available across service restarts. Do not run the SQLite-to-PostgreSQL migration script automatically on each deploy; review the migration and backup steps before using it.

Render's official [Flask deployment guide](https://render.com/docs/deploy-flask) documents the Python build and Gunicorn start commands. Render's [health check guide](https://render.com/docs/health-checks) explains how the `/health` path controls deploy readiness.

## Main project files

- `app.py` — Flask routes, authentication, database access, interviews, and application startup.
- `rag_knowledge.py` — bounded document extraction, chunking, and local lexical retrieval.
- `career_agent.py` — personalized career planning.
- `templates/` — Flask/Jinja pages.
- `static/` — styles, scripts, and static assets.
- `migrate_sqlite_to_neon.py` — manual SQLite-to-PostgreSQL migration utility; review and back up data before running it.
- `verify_neon_migration.py` — compares local SQLite and configured PostgreSQL table contents; run only when both database targets are intentional.
