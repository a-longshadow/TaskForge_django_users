import pytest
from django.urls import reverse
from django.utils import timezone

from tasks.models import Meeting, Task


@pytest.mark.django_db
def test_public_tasks_page(client):
    meeting = Meeting.objects.create(
        meeting_id="abc",
        title="Demo Meeting",
        organizer_email="demo@example.com",
        date=timezone.now(),
    )
    # task within expiry window
    Task.objects.create(
        meeting=meeting,
        task_item="foo",
        brief_description="bar",
        date_expected=timezone.now().date(),
    )

    url = reverse("public-tasks")
    resp = client.get(url)
    assert resp.status_code == 200
    assert b"Tasks Awaiting Review" in resp.content 