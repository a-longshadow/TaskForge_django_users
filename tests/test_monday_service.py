import json

import pytest
from django.utils import timezone

from tasks.models import Meeting, Task
from tasks.services import create_monday_item


@pytest.mark.django_db
def test_create_monday_item_skips_forbidden_column(monkeypatch):
    """`multiple_person_mkr7wdwf` must never be sent to Monday."""

    captured: dict = {}

    # Fake _post_monday to capture the variables sent to the API
    def fake_post(query: str, variables: dict):  # noqa: D401
        captured["vars"] = variables
        return {"data": {"create_item": {"id": "123"}}}

    # Column map with the forbidden key included
    column_map = {
        "team_member": "text_tm",
        "multiple_person_mkr7wdwf": "multiple_person_mkr7wdwf",
    }

    # Patch helpers inside tasks.services
    from tasks import services as svc

    monkeypatch.setattr(svc, "_post_monday", fake_post)

    def fake_get_setting(name: str):  # noqa: D401
        if name == "MONDAY_GROUP_ID":
            return "g_test"
        if name == "MONDAY_COLUMN_MAP":
            return json.dumps(column_map)
        return None

    monkeypatch.setattr(svc, "_get_setting", fake_get_setting)

    # Create dummy task
    meeting = Meeting.objects.create(
        meeting_id="mX",
        title="Demo",
        organizer_email="demo@example.com",
        date=timezone.now(),
    )
    task = Task.objects.create(
        meeting=meeting,
        task_item="Do something important",
        assignee_names="Alice",
        assignee_emails="alice@example.com",
        brief_description="Important work",
        date_expected=timezone.now().date(),
    )

    # Run – board_id passed explicitly to avoid env reliance
    create_monday_item(task, board_id="999")

    cols_json = captured["vars"]["cols"]
    cols = json.loads(cols_json)

    # Forbidden column should not be present
    assert "multiple_person_mkr7wdwf" not in cols
    # Allowed column included
    assert "text_tm" in cols

    # Add more tests as needed
    # ...

    # If all tests pass, return None
    return None 