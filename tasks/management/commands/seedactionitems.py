import os
import json
from datetime import datetime
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
    help = "Seed database with tasks from ACTION_ITEMS JSON files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            help="Path to specific *_ACTION_ITEMS.json file",
            required=False
        )
        parser.add_argument(
            "--dir",
            type=str,
            help="Path to directory containing ACTION_ITEMS JSON files",
            default="ACTION_ITEMS"
        )
        parser.add_argument(
            "--apply-settings",
            action="store_true",
            help="Apply default Monday.com settings if not present"
        )

    def handle(self, *args, **options):
        # Apply default AppSettings if requested
        if options["apply_settings"]:
            added_settings = 0
            for k, v in DEFAULT_SETTINGS.items():
                obj, created = AppSetting.objects.get_or_create(key=k, defaults={"value": v})
                if created:
                    added_settings += 1
            if added_settings:
                self.stdout.write(self.style.SUCCESS(f"Created {added_settings} new AppSettings."))

        total_meetings = 0
        total_tasks = 0

        # Handle single file case
        if options["file"]:
            path = Path(options["file"]).expanduser()
            if not path.exists():
                raise CommandError(f"File not found: {path}")
            
            self.stdout.write(f"Processing single file: {path}")
            meetings, tasks = self._process_file(path)
            total_meetings += meetings
            total_tasks += tasks
        
        # Handle directory case
        else:
            action_items_dir = options["dir"]
            if not os.path.exists(action_items_dir):
                self.stdout.write(self.style.ERROR(f"Directory {action_items_dir} not found"))
                return

            files = [f for f in os.listdir(action_items_dir) if f.endswith('.json')]
            if not files:
                self.stdout.write(self.style.ERROR(f"No JSON files found in {action_items_dir}"))
                return

            self.stdout.write(f"Found {len(files)} JSON files")
            
            for file_name in files:
                file_path = os.path.join(action_items_dir, file_name)
                self.stdout.write(f"Processing {file_name}...")
                
                meetings, tasks = self._process_file(file_path)
                total_meetings += meetings
                total_tasks += tasks
        
        self.stdout.write(self.style.SUCCESS(f"Seeding completed. Created {total_meetings} meetings and {total_tasks} tasks."))

    def _process_file(self, file_path):
        """Process a single JSON file and return (meetings_created, tasks_created)"""
        meetings_created = 0
        tasks_created = 0
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Create or get meeting
            meeting_date = None
            if 'meeting_date' in data:
                try:
                    # Convert from milliseconds timestamp to datetime
                    meeting_date = datetime.fromtimestamp(int(data['meeting_date']) / 1000, tz=timezone.utc)
                except (ValueError, TypeError):
                    meeting_date = timezone.now()
            else:
                meeting_date = timezone.now()
                
            # Parse generated_at if available
            generated_at = None
            if 'generated_at' in data:
                try:
                    generated_at = datetime.fromisoformat(data['generated_at'].replace('Z', '+00:00'))
                except (ValueError, TypeError, AttributeError):
                    pass
            
            meeting, created = Meeting.objects.get_or_create(
                meeting_id=data.get('meeting_id', f"meeting_{os.path.basename(file_path)}"),
                defaults={
                    'title': data.get('meeting_title', 'Untitled Meeting'),
                    'organizer_email': data.get('meeting_organizer', 'unknown@example.com'),
                    'date': meeting_date,
                    'execution_id': data.get('execution_id'),
                    'generated_at': generated_at
                }
            )
            
            # Update meeting with execution_id and generated_at if they weren't set before
            if created is False:
                update_fields = []
                if data.get('execution_id') and not meeting.execution_id:
                    meeting.execution_id = data.get('execution_id')
                    update_fields.append('execution_id')
                if generated_at and not meeting.generated_at:
                    meeting.generated_at = generated_at
                    update_fields.append('generated_at')
                if update_fields:
                    meeting.save(update_fields=update_fields)
            
            if created:
                meetings_created += 1
                self.stdout.write(self.style.SUCCESS(f"Created meeting: {meeting.title}"))
            else:
                self.stdout.write(f"Using existing meeting: {meeting.title}")
            
            # Process tasks
            tasks = data.get('tasks', [])
            for task_data in tasks:
                # Convert date string to datetime object
                date_expected = None
                if 'date_expected' in task_data:
                    try:
                        # First try standard ISO format
                        date_expected = datetime.strptime(task_data['date_expected'], '%Y-%m-%d').date()
                    except ValueError:
                        try:
                            # Try to parse from a more human-readable format
                            date_expected = datetime.strptime(task_data['date_expected'], '%B %d, %Y').date()
                        except ValueError:
                            # If all parsing fails, use current date
                            date_expected = timezone.now().date()
                else:
                    date_expected = timezone.now().date()
                
                # Determine status based on approved flag
                status = Task.Status.APPROVED if task_data.get('approved', False) else Task.Status.PENDING
                
                # Create task
                task, task_created = Task.objects.get_or_create(
                    meeting=meeting,
                    task_item=task_data.get('task_item', 'Untitled Task'),
                    defaults={
                        'assignee_names': task_data.get('assignee(s)_full_names', ''),
                        'assignee_emails': task_data.get('assignee_emails', ''),
                        'priority': task_data.get('priority', Task.Priority.MEDIUM),
                        'brief_description': task_data.get('brief_description', ''),
                        'date_expected': date_expected,
                        'status': status,
                        'auto_approved': task_data.get('auto_approved', False),
                        'source_payload': task_data
                    }
                )
                
                if task_created:
                    tasks_created += 1
                    if status == Task.Status.APPROVED:
                        task.reviewed_at = timezone.now()
                        task.save()
                    self.stdout.write(self.style.SUCCESS(f"Created task: {task.task_item[:50]}..."))
                else:
                    self.stdout.write(f"Task already exists: {task.task_item[:50]}...")
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error processing {file_path}: {str(e)}"))
        
        return meetings_created, tasks_created 