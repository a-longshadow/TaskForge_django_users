"""Integration helpers for external services (Monday.com, n8n, etc.)"""
from __future__ import annotations

import logging
import os
from typing import Any

import requests
from django.conf import settings
from .models import AppSetting
import json

logger = logging.getLogger(__name__)

MONDAY_API_URL = "https://api.monday.com/v2"  # GraphQL endpoint


def _get_setting(name: str) -> str | None:
    val = AppSetting.get(name) or os.getenv(name) or getattr(settings, name, None)
    if isinstance(val, str):
        return val.strip()
    return val


def _post_monday(query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    api_key = _get_setting("MONDAY_API_KEY")
    if not api_key:
        logger.warning("MONDAY_API_KEY missing – skipping Monday API call")
        return {}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "API-Version": "2023-10"  # Required for project tokens
    }

    resp = requests.post(MONDAY_API_URL, json={"query": query, "variables": variables}, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if data.get("errors"):
        logger.error("Monday API errors: %s", data["errors"])
    return data


def create_monday_item(task, board_id: str | None = None) -> str | None:
    """Creates an item on Monday.com and returns its item ID."""

    board_id = board_id or _get_setting("MONDAY_BOARD_ID")
    group_id = _get_setting("MONDAY_GROUP_ID")
    column_map_json = _get_setting("MONDAY_COLUMN_MAP")
    try:
        column_map = json.loads(column_map_json) if column_map_json else {}
    except Exception:
        column_map = {}
    if not board_id:
        logger.warning("MONDAY_BOARD_ID missing – cannot create Monday item")
        return None

    # Build column values according to map, ensuring forbidden column omitted
    def _safe(col):
        return col and col != "multiple_person_mkr7wdwf"

    column_values = {}
    if _safe(column_map.get("team_member")):
        column_values[column_map["team_member"]] = task.assignee_names
    if _safe(column_map.get("email")):
        column_values[column_map["email"]] = task.assignee_emails
    if _safe(column_map.get("priority")):
        column_values[column_map["priority"]] = {"label": task.priority}
    if _safe(column_map.get("status")):
        # Map Django task status to Monday.com status options
        status_map = {
            "pending": "To Do",
            "approved": "Approved",
            "rejected": "Deprioritized"
        }
        monday_status = status_map.get(task.status, "To Do")
        column_values[column_map["status"]] = {"label": monday_status}
    if _safe(column_map.get("due_date")):
        column_values[column_map["due_date"]] = {"date": str(task.date_expected)}
    if _safe(column_map.get("brief_description")):
        column_values[column_map["brief_description"]] = task.brief_description[:2000]

    # Mutation exactly matching the n8n production flow
    query = """
    mutation ($board:ID!, $group:String, $name:String!, $cols:JSON!){
      create_item(board_id:$board, group_id:$group, item_name:$name, column_values:$cols){ id }
    }
    """

    variables = {
        "board": board_id,  # Send as string for ID! type
        "group": group_id,
        "name": task.task_item[:100],
        "cols": json.dumps(column_values)  # JSON-encode once
    }

    try:
        data = _post_monday(query, variables)
        item_id = data.get("data", {}).get("create_item", {}).get("id")
        if item_id:
            logger.info("Monday item created (ID=%s) for task %s", item_id, task.id)
        return item_id
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to create Monday item: %s", exc, exc_info=True)
        return None 