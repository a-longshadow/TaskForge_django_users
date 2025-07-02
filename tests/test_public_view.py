import pytest
from django.urls import reverse
from django.utils import timezone
import json

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

@pytest.mark.django_db
def test_public_decline_flow(client):
    meeting = Meeting.objects.create(meeting_id="m4", title="T", organizer_email="x@y.com", date=timezone.now())
    task = Task.objects.create(meeting=meeting, task_item="Foo", brief_description="Bar", date_expected=timezone.now().date())
    # perform decline via api with header
    url=f"/api/tasks/{task.id}/reject/?confirm=true"
    resp=client.post(url, data=json.dumps({"reason":"This task is obsolete no longer needed."}), content_type="application/json", HTTP_X_PUBLIC_UI="true")
    assert resp.status_code==200
    task.refresh_from_db()
    assert task.status==Task.Status.REJECTED 