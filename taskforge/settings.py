"""Django settings for taskforge project.

The configuration follows 12-factor principles:
• All sensitive values are taken from environment variables (with safe fallbacks for local dev).
• Postgres (DATABASE_URL) is preferred; falls back to local SQLite automatically.
"""
from __future__ import annotations

import os
from pathlib import Path

import environ

# ---------------------------------------------------------------------------
# BASE DIR & ENV INITIALISATION
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# Load variables from a .env file if present (local dev). This is a no-op in prod.
env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, "unsafe-secret-key"),
    ALLOWED_HOSTS=(list[str], ["*"]),
)
if (env_file := BASE_DIR / ".env") and env_file.exists():  # pragma: no cover
    environ.Env.read_env(str(env_file))

# ---------------------------------------------------------------------------
# CORE SETTINGS
# ---------------------------------------------------------------------------
SECRET_KEY = env("SECRET_KEY")
# WARNING: Forced debug mode as per project requirement.
DEBUG: bool = True
ALLOWED_HOSTS: list[str] = env("ALLOWED_HOSTS")
# Allow all Railway-generated domains to pass CSRF origin checks (HTTPS).
CSRF_TRUSTED_ORIGINS: list[str] = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=["https://*.railway.app"],
)

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    # Project apps
    "tasks",
    # theme
    
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Custom request logging
    "tasks.middleware.RequestLoggingMiddleware",
    # Admin action logging middleware
    "tasks.middleware.AdminActionLogMiddleware",
    # Page logging middleware (replaces RequestLoggingMiddleware)
    "tasks.middleware.PageLogMiddleware",
]

ROOT_URLCONF = "taskforge.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "taskforge.wsgi.application"
ASGI_APPLICATION = "taskforge.asgi.application"

# ---------------------------------------------------------------------------
# DATABASE
# ---------------------------------------------------------------------------

if env("DATABASE_URL", default=None):
    DATABASES = {
        "default": env.db(),  # type: ignore[arg-type]
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ---------------------------------------------------------------------------
# PASSWORD VALIDATION
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# ---------------------------------------------------------------------------
# INTERNATIONALISATION
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# STATIC & MEDIA
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---------------------------------------------------------------------------
# REST FRAMEWORK DEFAULTS
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# ---------------------------------------------------------------------------
# LOGGING – simple stdout + DB audit via tasks.middleware
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO" if not DEBUG else "DEBUG",
    },
}

# ---------------------------------------------------------------------------
# MONDAY.COM API – token pulled from env (integration service uses)
# ---------------------------------------------------------------------------
# Secrets come only from env/AppSetting; board/group/map have safe code defaults.
MONDAY_API_KEY: str | None = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjUxMjY3Mjg4OCwiYWFpIjoxMSwidWlkIjo3NTc1NzcxNiwiaWFkIjoiMjAyNS0wNS0xNFQxMTowNzowMS4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6Mjg0NjkxNTUsInJnbiI6InVzZTEifQ.DiRDF-_B--_QqgBLrhg3L_Z22d3IiQhQC9jpLrblnpg"

# Safe-to-commit defaults (can be overridden by env or AppSetting)
MONDAY_API_URL: str | None = env("MONDAY_API_URL", default="https://api.monday.com/v2")
MONDAY_BOARD_ID: str | None = env("MONDAY_BOARD_ID", default="9212659997")
MONDAY_GROUP_ID: str | None = env("MONDAY_GROUP_ID", default="group_mkqyryrz")
MONDAY_COLUMN_MAP: str = env(
    "MONDAY_COLUMN_MAP",
    default='{"team_member":"text_mkr7jgkp","email":"text_mkr0hqsb","priority":"status_1","status":"status","due_date":"date5","brief_description":"long_text"}',
) 