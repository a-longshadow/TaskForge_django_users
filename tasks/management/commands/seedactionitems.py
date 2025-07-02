import json
import logging
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from tasks.models import Meeting, Task, AppSetting

logger = logging.getLogger(__name__)

DEFAULT_SETTINGS = {
    "MONDAY_BOARD_ID": "9212659997",
    "MONDAY_GROUP_ID": "group_mkqyryrz",
    "MONDAY_COLUMN_MAP": (
        '{"team_member":"text_mkr7jgkp","email":"text_mkr0hqsb","priority":"status_1","status":"status","due_date":"date5","brief_description":"long_text"}'
    ),
}

class Command(BaseCommand):
    help = "Seed meetings/tasks from a ACTION_ITEMS JSON export. Also populates Monday AppSettings if missing."

    def add_arguments(self, parser):
        parser.add_argument("filepath", type=str, help="Path to *_ACTION_ITEMS.json file")

    def handle(self, *args, **options):
        path = Path(options["filepath"]).expanduser()
        if not path.exists():
            raise CommandError(f"File not found: {path}")

        with path.open() as f:
            payload = json.load(f)

        # Apply default AppSettings if not present
        added_settings = 0
        for k, v in DEFAULT_SETTINGS.items():
            obj, created = AppSetting.objects.get_or_create(key=k, defaults={"value": v})
            if created:
                added_settings += 1
        if added_settings:
            self.stdout.write(self.style.SUCCESS(f"Created {added_settings} new AppSettings."))

        meeting_id = payload["meeting_id"]
        meeting, _ = Meeting.objects.get_or_create(
            meeting_id=meeting_id,
            defaults={
                "title": payload.get("meeting_title", "Untitled"),
                "organizer_email": payload.get("meeting_organizer", "unknown@example.com"),
                "date": timezone.now(),
            },
        )
        tasks_data = payload.get("tasks", [])
        created_tasks = 0
        for t in tasks_data:
            task_obj, created = Task.objects.get_or_create(
                meeting=meeting,
                task_item=t.get("task_item"),
                defaults={
                    "assignee_names": t.get("assignee(s)_full_names", ""),
                    "assignee_emails": t.get("assignee_emails", ""),
                    "priority": t.get("priority", Task.Priority.MEDIUM),
                    "brief_description": t.get("brief_description", ""),
                    "date_expected": t.get("date_expected", timezone.now().date()),
                    "auto_approved": t.get("auto_approved", False),
                    "status": Task.Status.APPROVED if t.get("approved") else Task.Status.PENDING,
                },
            )
            if created:
                created_tasks += 1
                logger.info("Created task %s", task_obj.id)

        self.stdout.write(self.style.SUCCESS(f"Seed completed: {created_tasks} tasks for meeting {meeting_id}")) 