import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from unittest.mock import patch
from django.contrib.auth.models import User

from tasks.models import Meeting, Task, ReviewAction


@pytest.fixture()
def api_client():
    user = User.objects.create_user(username="tester", password="x", is_staff=True)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_task_approve_flow(api_client):
    meeting = Meeting.objects.create(
        meeting_id="m1",
        title="T",
        organizer_email="t@example.com",
        date=timezone.now(),
    )
    task = Task.objects.create(
        meeting=meeting,
        task_item="Foo",
        brief_description="Bar",
        date_expected=timezone.now().date(),
    )

    url = reverse("tasks:task-approve", args=[task.id]) + "?confirm=true"
    with patch("tasks.views.create_monday_item", return_value="123"):
        resp = api_client.post(url)
    assert resp.status_code == 200
    task.refresh_from_db()
    assert task.status == Task.Status.APPROVED
    assert task.monday_item_id == "123"
    assert task.reviewed_at is not None
    # ReviewAction created
    assert ReviewAction.objects.filter(task=task, action=ReviewAction.Action.APPROVE).exists()


@pytest.mark.django_db
def test_task_reject_requires_reason(api_client):
    meeting = Meeting.objects.create(
        meeting_id="m2",
        title="T2",
        organizer_email="x@example.com",
        date=timezone.now(),
    )
    task = Task.objects.create(
        meeting=meeting,
        task_item="Foo",
        brief_description="Bar",
        date_expected=timezone.now().date(),
    )
    url = reverse("tasks:task-reject", args=[task.id]) + "?confirm=true"
    # insufficient reason words
    resp = api_client.post(url, data={"reason": "Too short"}, format="json")
    assert resp.status_code == 400
    # proper reason
    reason = "This task is no longer relevant because the project was cancelled."  # 12 words
    resp = api_client.post(url, data={"reason": reason}, format="json")
    assert resp.status_code == 200
    task.refresh_from_db()
    assert task.status == Task.Status.REJECTED
    assert task.rejected_reason == reason
    assert task.reviewed_at is not None


@pytest.mark.django_db
def test_task_edit_description(api_client):
    meeting = Meeting.objects.create(
        meeting_id="m3",
        title="T3",
        organizer_email="x@example.com",
        date=timezone.now(),
    )
    task = Task.objects.create(
        meeting=meeting,
        task_item="Foo",
        brief_description="Old",
        date_expected=timezone.now().date(),
    )
    url = reverse("tasks:task-edit", args=[task.id])
    resp = api_client.patch(url, data={"new_brief_description": "New desc"}, format="json")
    assert resp.status_code == 200
    task.refresh_from_db()
    assert "New desc" in task.brief_description 