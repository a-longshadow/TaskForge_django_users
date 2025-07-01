"""Integration helpers for external services (Monday.com, n8n, etc.)"""
from __future__ import annotations

import logging
import os
from typing import Any

import requests
from django.conf import settings
from .models import AppSetting

logger = logging.getLogger(__name__)

MONDAY_API_URL = "https://api.monday.com/v2"  # GraphQL endpoint


def _get_setting(name: str) -> str | None:
    return AppSetting.get(name) or os.getenv(name) or getattr(settings, name, None)


def _post_monday(query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    api_key = _get_setting("MONDAY_API_KEY")
    if not api_key:
        logger.warning("MONDAY_API_KEY missing – skipping Monday API call")
        return {}

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
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
    if not board_id:
        logger.warning("MONDAY_BOARD_ID missing – cannot create Monday item")
        return None

    query = """
        mutation ($boardId: Int!, $itemName: String!) {
          create_item (board_id: $boardId, item_name: $itemName) { id }
        }
    """
    variables = {"boardId": int(board_id), "itemName": task.task_item[:100]}

    try:
        data = _post_monday(query, variables)
        item_id = data.get("data", {}).get("create_item", {}).get("id")
        if item_id:
            logger.info("Monday item created (ID=%s) for task %s", item_id, task.id)
        return item_id
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to create Monday item: %s", exc, exc_info=True)
        return None 