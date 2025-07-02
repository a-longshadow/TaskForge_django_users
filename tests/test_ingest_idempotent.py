import json
import pytest
from django.urls import reverse
from django.utils import timezone

from tasks.models import Meeting, Task


@pytest.fixture()
def sample_payload():
    return {
        "monday_tasks": [
            {
                "meeting_id": "mid1",
                "meeting_title": "Demo",
                "meeting_organizer": "x@example.com",
                "meeting_date": timezone.now().isoformat(),
                "task_item": "Test task",
                "brief_description": "Desc",
                "date_expected": timezone.now().date().isoformat(),
                "priority": "Medium",
            }
        ]
    }


@pytest.mark.django_db
def test_ingest_first_time(client, sample_payload):
    url = reverse("tasks:ingest")
    resp = client.post(url, data=json.dumps(sample_payload), content_type="application/json")
    assert resp.status_code == 200
    assert resp.json() == {"created": 1}
    assert Meeting.objects.filter(meeting_id="mid1").exists()
    assert Task.objects.count() == 1


@pytest.mark.django_db
def test_ingest_duplicate_skipped(client, sample_payload):
    url = reverse("tasks:ingest")
    # first ingest
    client.post(url, data=json.dumps(sample_payload), content_type="application/json")
    # duplicate ingest
    resp = client.post(url, data=json.dumps(sample_payload), content_type="application/json")
    assert resp.status_code == 200
    assert resp.json()["detail"] == "already_ingested"
    # still only one meeting & one task
    assert Meeting.objects.count() == 1
    assert Task.objects.count() == 1 