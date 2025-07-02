# TaskForge HITL – Deployment Guide

This document explains how the project was migrated from a local SQLite setup to a production-ready PostgreSQL deployment on Railway and how to reproduce the process from scratch.

---

## 1. Prerequisites

* Railway CLI (`brew install railway` or see docs)
* GitHub repository linked: `https://github.com/a-longshadow/taskforge-approval-dashboard`
* PostgreSQL client (`psql`) if you want to connect manually
* A Railway account with a **handsome-nature** project

---

## 2. Local Development

```bash
# 1. Clone & create venv
git clone https://github.com/a-longshadow/taskforge-approval-dashboard.git
cd taskforge-approval-dashboard
python -m venv venv && source venv/bin/activate
pip install -r app/requirements.txt

# 2. Provide .env (or export) – example values live in env.example
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/hitl
export FLASK_ENV=development  # set to production in prod
python app/server.py  # http://localhost:8080/health
```

---

## 3. Migration Steps Performed

1. **Database switch** – replaced SQLite with pooled `psycopg2` connections and automatic schema creation (`init_database()`).
2. **Environment variable** – server now derives `DATABASE_URL`; when not present it falls back to a local SQLite file (dev only).
3. **Gunicorn** – added to `requirements.txt` and changed `Procfile` to
   ```
   web: gunicorn -w 4 -b 0.0.0.0:$PORT app.server:app
   ```
4. **.gitignore** – ignores local artefacts: `_temp/`, `*.db`, `venv/`, caches.
5. **Integration test** – `test_flow.py` exercises the full API flow.
6. **Railway CLI automation**
   - Linked repo: `railway link b7380a3c-c370-4006-9ea2-f206ea4b525f`
   - Added Postgres service: `railway add --database postgres`
   - Propagated `DATABASE_URL` to the **web** service:
     ```bash
     export URL=$(railway variables --service Postgres --kv | grep DATABASE_URL | cut -d= -f2-)
     railway variables --service web --set "DATABASE_URL=$URL"
     ```
   - Overrode **web** start command so Railway uses gunicorn:
     ```bash
     railway variables --service web --set "NIXPACKS_START_CMD=gunicorn -w 4 -b 0.0.0.0:$PORT app.server:app"
     ```
   - Triggered deploy: `railway up --service web --detach`.

---

## 4. Production Environment Variables

| Variable | Value (example) | Why |
|----------|-----------------|-----|
| `DATABASE_URL` | Provided by Railway Postgres | Connection string for pooled DB |
| `NIXPACKS_START_CMD` | `gunicorn -w 4 -b 0.0.0.0:$PORT app.server:app` | Ensures WSGI server in prod |
| `FLASK_DEBUG` | `false` | Disables verbose debug logs |
| `FLASK_ENV` | `production` | Hides Werkzeug dev warnings |

Set or update with:
```bash
railway variables --service web --set "FLASK_DEBUG=false" --set "FLASK_ENV=production"
```

---

## 5. Health-check

```
GET /health → { "status": "healthy", "database": "connected", ... }
```

If `database` is not `connected`, re-verify `DATABASE_URL`.

---

## 6. Redeploying

```bash
git pull origin main  # ensure up-to-date
railway up --service web --detach  # push and build
```

---

## 7. Troubleshooting

* 502 / Gunicorn not found → verify `requirements.txt` contains `gunicorn` and `NIXPACKS_START_CMD` is set.
* `psycopg2` errors → Postgres service may be sleeping; open Railway GUI or `railway connect postgres` to wake up.
* `Tasks not found` → links expire after 15 min; generate new execution.

---

## 8. Approval-Flow Behaviour (2024-07 update)

### Partial approval (hand-pick)
* The dashboard now sends an `approved` boolean with every task.
* `/submit-approval` stores **only** the items where `approved: true` – rejected/untouched tasks are dropped.

### Auto-approval after wait timeout
* `/approved` blocks up to `APPROVAL_WAIT_SEC` (default 300 s).
* If no manual approval arrives, it auto-sets `approved: true` on every pending task and returns the payload with
  ```json
  {
    "method": "auto_wait_timeout",
    "approved_monday_tasks": [...]
  }
  ```
* The old 202 `{"status":"pending"}` response is gone; the endpoint **always** returns 200.

### Local development note (SQLite only)
* SQLite connections are now opened with `check_same_thread=False` so Flask's threaded dev server no longer raises
  "Cannot operate on a closed database."  Production (Postgres) remains unchanged. 