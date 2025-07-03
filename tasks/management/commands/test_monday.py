from django.core.management.base import BaseCommand
from django.utils import timezone
import json

from tasks.services import create_monday_item, _post_monday, _get_setting
from tasks.models import Task, Meeting


class Command(BaseCommand):
    help = "Test Monday.com integration by creating a test item"

    def add_arguments(self, parser):
        parser.add_argument(
            "--create-task",
            action="store_true",
            help="Create a test task in the database and post it to Monday.com",
        )

    def handle(self, *args, **options):
        # Test API connection
        self.stdout.write("Testing Monday.com API connection...")
        
        api_key = _get_setting("MONDAY_API_KEY")
        board_id = _get_setting("MONDAY_BOARD_ID")
        group_id = _get_setting("MONDAY_GROUP_ID")
        
        if not api_key:
            self.stdout.write(self.style.ERROR("MONDAY_API_KEY not set"))
            return
            
        if not board_id:
            self.stdout.write(self.style.ERROR("MONDAY_BOARD_ID not set"))
            return
            
        if not group_id:
            self.stdout.write(self.style.ERROR("MONDAY_GROUP_ID not set"))
            return
            
        # Test API connection
        try:
            data = _post_monday("query { me { id name email } }")
            if "errors" in data:
                self.stdout.write(self.style.ERROR(f"API Error: {data['errors']}"))
                return
                
            me_data = data.get("data", {}).get("me", {})
            self.stdout.write(self.style.SUCCESS(f"Connected as: {me_data.get('name')} ({me_data.get('email')})"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Connection error: {str(e)}"))
            return
            
        # Create test task if requested
        if options["create_task"]:
            self.stdout.write("Creating test task in database...")
            
            # Create test meeting
            meeting = Meeting.objects.create(
                meeting_id=f"test-meeting-{timezone.now().timestamp()}",
                title="Test Meeting for Monday.com Integration",
                organizer_email="test@example.com",
                date=timezone.now(),
            )
            
            # Create test task
            task = Task.objects.create(
                meeting=meeting,
                task_item="Test Task for Monday.com Integration",
                assignee_names="Test User",
                assignee_emails="test@example.com",
                priority=Task.Priority.HIGH,
                brief_description="This is a test task created to verify Monday.com integration.",
                date_expected=timezone.now().date(),
                status=Task.Status.APPROVED,
                reviewed_at=timezone.now(),
            )
            
            self.stdout.write(self.style.SUCCESS(f"Created test task with ID: {task.id}"))
            
            # Post to Monday.com
            self.stdout.write("Posting task to Monday.com...")
            item_id = create_monday_item(task)
            
            if item_id:
                task.monday_item_id = item_id
                task.posted_to_monday = True
                task.save(update_fields=["monday_item_id", "posted_to_monday"])
                self.stdout.write(self.style.SUCCESS(f"Successfully posted to Monday.com with item ID: {item_id}"))
            else:
                self.stdout.write(self.style.ERROR("Failed to post to Monday.com"))
        else:
            # Test creating an item directly
            self.stdout.write("Testing item creation on Monday.com...")
            
            column_values = {
                "text_mkr7jgkp": "Test User",
                "text_mkr0hqsb": "test@example.com",
                "status_1": {"label": "High"},
                "status": {"label": "Approved"},
                "long_text": "This is a test item created by the Django management command."
            }
            
            # Mutation exactly matching the n8n production flow
            query = """
            mutation ($board:ID!, $group:String, $name:String!, $cols:JSON!){
              create_item(board_id:$board, group_id:$group, item_name:$name, column_values:$cols){ id }
            }
            """
            
            variables = {
                "board": board_id,  # Send as string for ID! type
                "group": group_id,
                "name": "Test Item from Django Command",
                "cols": json.dumps(column_values)  # JSON-encode once
            }
            
            try:
                data = _post_monday(query, variables)
                if "errors" in data:
                    self.stdout.write(self.style.ERROR(f"API Error: {data['errors']}"))
                    return
                    
                item_id = data.get("data", {}).get("create_item", {}).get("id")
                if item_id:
                    self.stdout.write(self.style.SUCCESS(f"Successfully created item with ID: {item_id}"))
                else:
                    self.stdout.write(self.style.ERROR("No item ID returned"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error creating item: {str(e)}")) 