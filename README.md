# TaskForge Django Web App

## Quick start

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser  # follow prompts
python manage.py seedgroups       # adds `admin` and `user` groups

# (optional) load .env locally
export MONDAY_API_KEY="<key>"
export MONDAY_BOARD_ID="<board_id>"

# run
python manage.py runserver
```

## Production (Railway)

1. Add environment variables in Railway dashboard:
   * `DATABASE_URL` – auto-populated by Railway Postgres add-on.
   * `SECRET_KEY` – random 50-char string.
   * `MONDAY_API_KEY` – Monday API token.
   * `MONDAY_BOARD_ID` – Board ID (digits only).
2. Deploy with **`gunicorn taskforge.wsgi --bind 0.0.0.0:$PORT`**.

## Runtime-editable settings

`App Setting` entries in Django admin allow ops to update **MONDAY_API_KEY**, **MONDAY_BOARD_ID**, or any future key/value without redeploying.

## Documentation

- [Admin Interface Improvements](docs/admin_improvements.md) - Details on the enhanced admin interface with custom confirmation dialogs and Monday.com integration
- [API Documentation](docs/api.md)
- [Architecture Overview](docs/architecture.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Setup Guide](docs/setup.md)

## Recent Improvements

- Enhanced admin interface with custom confirmation dialogs
- Added individual and bulk approve/reject actions for tasks
- Fixed Monday.com integration for task synchronization
- Improved public task review interface with modal confirmations 