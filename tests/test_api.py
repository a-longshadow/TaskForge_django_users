import pytest
from django.urls import reverse
from django.utils import timezone

from tasks.models import Meeting, Task


@pytest.mark.django_db
def test_public_approved_endpoint(client):
    meeting = Meeting.objects.create(
        meeting_id="a1",
        title="Title",
        organizer_email="x@y.com",
        date=timezone.now(),
    )
    Task.objects.create(
        meeting=meeting,
        task_item="Foo",
        brief_description="Bar",
        date_expected=timezone.now().date(),
        status=Task.Status.APPROVED,
    )

    url = reverse("public:approved-list")
    resp = client.get(url)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1 