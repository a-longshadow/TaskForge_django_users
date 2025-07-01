# Railway Deployment

> Railway "Add Project" ➜ **Deploy from GitHub**.

## 1. Provision PostgreSQL
Add the Postgres plugin. Railway sets `DATABASE_URL` automatically.

## 2. Environment Variables
| Key | Example |
|-----|---------|
| `SECRET_KEY` | `django-insecure-x0o_...` |
| `MONDAY_API_KEY` | `eyJ0eXAiOiJK...` |
| `MONDAY_BOARD_ID` | `1234567890` |

## 3. Build & Start Commands
| Phase | Command |
|-------|---------|
| Build | `pip install -r requirements.txt && python manage.py migrate` |
| Start | `gunicorn taskforge.wsgi --bind 0.0.0.0:$PORT` |

## 4. Force `DEBUG=True`
The project settings keep DEBUG hard-coded to `True` in **all** envs per client request—no action needed.

## 5. Static files
We rely on Django's built-in static serving (DEBUG=True) for expediency. If/when DEBUG is disabled, add Whitenoise or S3.

---

## Troubleshooting
* **`OperationalError: no such table`** – Ship failed migrations? Trigger a redeploy or run `python manage.py migrate` via Railway console.
* **CSRF failures** – Ensure you access via the primary Railway domain or configure `CSRF_TRUSTED_ORIGINS`. 