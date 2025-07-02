from __future__ import annotations

import json
from importlib import import_module
import subprocess, os
from pathlib import Path

from django.db import connections
from django.db.migrations.executor import MigrationExecutor
from django.http import JsonResponse
from django.utils.timezone import now
from django.core.cache import cache

# Monday probe utilities
from tasks.services import _post_monday, _get_setting  # type: ignore


def _check_database() -> dict[str, str]:
    try:
        connection = connections["default"]
        connection.cursor()  # forces connection
        return {"database": "ok"}
    except Exception as exc:  # pragma: no cover
        return {"database": f"error: {exc}"}


def _check_migrations() -> dict[str, str]:
    try:
        executor = MigrationExecutor(connections["default"])
        targets = executor.loader.graph.leaf_nodes()
        plan = executor.migration_plan(targets)
        if plan:
            return {"migrations": "pending"}
        return {"migrations": "ok"}
    except Exception as exc:  # pragma: no cover
        return {"migrations": f"error: {exc}"}


def health_view(request):  # noqa: D401
    """Return JSON with app, DB, and migrations status."""

    # Monday status cached for 60s
    monday_cache = cache.get("health_monday")
    if monday_cache is None:
        token_present = bool(_get_setting("MONDAY_API_KEY"))
        status_msg = "missing-token"
        if token_present:
            try:
                # Simple query to check if API key is valid
                data = _post_monday("query { me { id } }")
                if data.get("errors"):
                    status_msg = data["errors"][0].get("message", "error")
                else:
                    status_msg = "ok"
            except Exception as exc:  # pragma: no cover
                status_msg = str(exc)
        monday_cache = {
            "token_present": token_present,
            "api_status": status_msg,
        }
        cache.set("health_monday", monday_cache, 60)

    # git sha
    try:
        git_sha = (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=Path(__file__).resolve().parent.parent)
            .decode()
            .strip()
        )
    except Exception:  # pragma: no cover
        git_sha = "unknown"

    payload = {
        "timestamp": now().isoformat(),
        **_check_database(),
        **_check_migrations(),
        "monday": monday_cache,
        "version": git_sha,
    }
    status = 200 if payload.get("database") == "ok" and payload.get("migrations") == "ok" else 503
    return JsonResponse(payload, status=status) 