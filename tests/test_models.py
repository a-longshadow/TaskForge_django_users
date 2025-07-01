import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from tasks.models import Meeting, Task, ReviewAction


@pytest.mark.django_db
def test_task_approval_flow():
    # Arrange
    meeting = Meeting.objects.create(
        meeting_id="123",
        title="Weekly Sync",
        organizer_email="owner@example.com",
        date=timezone.now(),
    )
    task = Task.objects.create(
        meeting=meeting,
        task_item="Prepare report",
        priority=Task.Priority.HIGH,
        brief_description="Prepare quarterly financial report",
        date_expected=timezone.now().date(),
    )
    user = User.objects.create_user(username="alice", password="pass")

    # Act → approve
    task.status = Task.Status.APPROVED
    task.save()

    ReviewAction.objects.create(
        task=task,
        user=user,
        action=ReviewAction.Action.APPROVE,
        reason="Looks good",
    )

    # Assert
    assert task.status == Task.Status.APPROVED
    assert task.reviews.count() == 1
    review = task.reviews.first()
    assert review.reason == "Looks good" 