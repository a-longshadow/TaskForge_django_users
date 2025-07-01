from __future__ import annotations

import json
from importlib import import_module

from django.db import connections
from django.db.migrations.executor import MigrationExecutor
from django.http import JsonResponse
from django.utils.timezone import now


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

    payload = {
        "timestamp": now().isoformat(),
        **_check_database(),
        **_check_migrations(),
    }
    status = 200 if payload.get("database") == "ok" and payload.get("migrations") == "ok" else 503
    return JsonResponse(payload, status=status) 