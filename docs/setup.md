# Local Setup

## Prerequisites
* Python ⩾ 3.11
* (optional) [Poetry](https://python-poetry.org/) or `virtualenv`

## 1. Clone & create venv
```bash
git clone https://github.com/a-longshadow/TaskForge_django_users.git
cd TaskForge_django_users
python -m venv .venv
source .venv/bin/activate
```

## 2. Install deps
```bash
pip install -r requirements.txt
```

## 3. Database & admin user
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py seedgroups  # optional convenience
```

## 4. Environment variables (optional)
```bash
export MONDAY_API_KEY="<token>"
export MONDAY_BOARD_ID="123456789"
```
If omitted, Monday sync will no-op.

## 5. Run
```bash
python manage.py runserver
```
Navigate to `http://127.0.0.1:8000/`.

## 6. Tests
```bash
pytest -q
``` 