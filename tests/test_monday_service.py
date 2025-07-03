"""Tests for Monday.com integration service."""
import json
import logging
import unittest
import requests
from unittest import mock, skipIf
from unittest.mock import patch, MagicMock, Mock
from django.test import TestCase, override_settings
from django.utils import timezone
from django.contrib.auth import get_user_model

from tasks.models import Meeting, Task, ReviewAction
from tasks.services import create_monday_item, _post_monday, _get_setting

User = get_user_model()


@override_settings(
    # Override settings to prevent real API calls during tests
    MONDAY_API_KEY="test-api-key",
    MONDAY_BOARD_ID="test-board-123",
    MONDAY_GROUP_ID="test-group-123",
    MONDAY_COLUMN_MAP='{"test": "column"}'
)
class MondayServiceTestCase(TestCase):
    """Test Monday.com integration service."""

    def setUp(self):
        """Set up test data."""
        # Create a test meeting
        self.meeting = Meeting.objects.create(
            meeting_id="test-meeting-123",
            title="Test Meeting",
            organizer_email="test@example.com",
            date=timezone.now(),
        )
        
        # Create a test task
        self.task = Task.objects.create(
            meeting=self.meeting,
            task_item="Test Task",
            assignee_names="Test User",
            assignee_emails="test@example.com",
            priority=Task.Priority.HIGH,
            brief_description="This is a test task",
            date_expected=timezone.now().date(),
        )
        
        # Create a test user for review actions
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpass123"
        )
        
        # Setup multiple tasks for bulk testing
        self.tasks = [self.task]
        for i in range(3):
            task = Task.objects.create(
                meeting=self.meeting,
                task_item=f"Bulk Test Task {i+1}",
                assignee_names="Test User",
                assignee_emails="test@example.com",
                priority=Task.Priority.MEDIUM,
                brief_description=f"This is bulk test task {i+1}",
                date_expected=timezone.now().date(),
            )
            self.tasks.append(task)

    @patch('tasks.services.requests.post')
    @patch('tasks.services._get_setting')
    def test_create_monday_item(self, mock_get_setting, mock_requests_post):
        """Test creating a Monday.com item."""
        # Mock _get_setting to return test values
        def mock_get_setting_func(key):
            settings_map = {
                "MONDAY_API_KEY": "test-api-key",
                "MONDAY_BOARD_ID": "12345",
                "MONDAY_GROUP_ID": "group_123",
                "MONDAY_COLUMN_MAP": json.dumps({
                    "team_member": "person",
                    "email": "email",
                    "priority": "priority",
                    "status": "status",
                    "due_date": "date",
                    "brief_description": "text"
                })
            }
            return settings_map.get(key)
        
        mock_get_setting.side_effect = mock_get_setting_func
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "create_item": {
                    "id": "987654321"
                }
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_requests_post.return_value = mock_response
        
        # Call the function
        result = create_monday_item(self.task)
        
        # Assertions
        self.assertEqual(result, "987654321")
        mock_requests_post.assert_called_once()
        
        # Verify the API call was made correctly
        call_args = mock_requests_post.call_args
        # Check that the URL contains the expected endpoint (works for both real and test URLs)
        url = call_args[0][0]
        self.assertTrue(url.endswith("/v2"), f"Expected URL to end with /v2, got: {url}")
        self.assertEqual(call_args[1]["headers"]["Authorization"], "Bearer test-api-key")
        self.assertEqual(call_args[1]["headers"]["Content-Type"], "application/json")
        self.assertEqual(call_args[1]["headers"]["API-Version"], "2023-10")
        
        # Verify the GraphQL mutation and variables
        json_payload = call_args[1]["json"]
        self.assertIn("mutation", json_payload["query"])
        self.assertIn("create_item", json_payload["query"])
        
        variables = json_payload["variables"]
        self.assertEqual(variables["board"], "12345")
        self.assertEqual(variables["group"], "group_123")
        self.assertEqual(variables["name"], "Test Task")
        
        # Verify column values
        column_values = json.loads(variables["cols"])
        self.assertEqual(column_values["person"], "Test User")
        self.assertEqual(column_values["email"], "test@example.com")
        self.assertEqual(column_values["priority"]["label"], "High")
        self.assertEqual(column_values["status"]["label"], "To Do")
        
    @patch('tasks.services.requests.post')
    @patch('tasks.services._get_setting')
    def test_create_monday_item_missing_board_id(self, mock_get_setting, mock_requests_post):
        """Test creating a Monday.com item with missing board ID."""
        # Mock _get_setting to return None for board ID
        def mock_get_setting_func(key):
            settings_map = {
                "MONDAY_API_KEY": "test-api-key",
                "MONDAY_BOARD_ID": None,  # Missing board ID
                "MONDAY_GROUP_ID": "group_123",
                "MONDAY_COLUMN_MAP": json.dumps({})
            }
            return settings_map.get(key)
        
        mock_get_setting.side_effect = mock_get_setting_func
        
        # Call the function
        result = create_monday_item(self.task)
        
        # Assertions
        self.assertIsNone(result)
        mock_requests_post.assert_not_called()
        
    @patch('tasks.services.requests.post')
    @patch('tasks.services._get_setting')
    def test_create_monday_item_api_error(self, mock_get_setting, mock_requests_post):
        """Test creating a Monday.com item with API error."""
        # Mock _get_setting to return test values
        def mock_get_setting_func(key):
            settings_map = {
                "MONDAY_API_KEY": "test-api-key",
                "MONDAY_BOARD_ID": "12345",
                "MONDAY_GROUP_ID": "group_123",
                "MONDAY_COLUMN_MAP": json.dumps({})
            }
            return settings_map.get(key)
        
        mock_get_setting.side_effect = mock_get_setting_func
        
        # Mock API error response
        mock_response = Mock()
        mock_response.json.return_value = {
            "errors": [
                {
                    "message": "Not authorized"
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_requests_post.return_value = mock_response
        
        # Call the function
        result = create_monday_item(self.task)
        
        # Assertions
        self.assertIsNone(result)
        mock_requests_post.assert_called_once()
        
    @patch('tasks.services.requests.post')
    @patch('tasks.services._get_setting')
    def test_post_monday(self, mock_get_setting, mock_requests_post):
        """Test posting to Monday.com API."""
        # Mock _get_setting to return API key
        mock_get_setting.return_value = "test-api-key"
        
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {"data": {"test": "value"}}
        mock_response.raise_for_status.return_value = None
        mock_requests_post.return_value = mock_response
        
        # Call the function
        result = _post_monday("test query", {"var": "value"})
        
        # Assertions
        self.assertEqual(result, {"data": {"test": "value"}})
        mock_requests_post.assert_called_once()
        
        # Verify headers
        call_args = mock_requests_post.call_args
        self.assertEqual(call_args[1]["headers"]["Authorization"], "Bearer test-api-key")
        self.assertEqual(call_args[1]["headers"]["Content-Type"], "application/json")
        self.assertEqual(call_args[1]["headers"]["API-Version"], "2023-10")
        
        # Verify payload
        self.assertEqual(call_args[1]["json"]["query"], "test query")
        self.assertEqual(call_args[1]["json"]["variables"], {"var": "value"})
        
    @patch('tasks.services._get_setting')
    def test_post_monday_missing_api_key(self, mock_get_setting):
        """Test posting to Monday.com API with missing API key."""
        # Mock missing API key
        mock_get_setting.return_value = None
        
        # Call the function
        result = _post_monday("test query")
        
        # Assertions
        self.assertEqual(result, {})
            
    @patch('tasks.services.requests.post')
    @patch('tasks.services._get_setting')
    def test_post_monday_request_exception(self, mock_get_setting, mock_requests_post):
        """Test posting to Monday.com API with request exception."""
        # Mock API key
        mock_get_setting.return_value = "test-api-key"
        
        # Configure the mock to raise a requests exception
        mock_requests_post.side_effect = requests.exceptions.ConnectionError("Connection error")
        
        # Call the function
        result = _post_monday("test query")
        
        # Assertions
        self.assertEqual(result, {"errors": [{"message": "Connection error"}]})
        
    @patch('tests.test_monday_service.create_monday_item')
    def test_bulk_create_monday_items(self, mock_create_monday_item):
        """Test creating multiple Monday.com items in bulk."""
        # Mock successful creation for each item
        mock_create_monday_item.side_effect = [f"item_{i}" for i in range(len(self.tasks))]
        
        # Process each task
        results = []
        for task in self.tasks:
            item_id = create_monday_item(task)
            results.append(item_id)
            
            # Update task if item was created
            if item_id:
                task.status = Task.Status.APPROVED
                task.reviewed_at = timezone.now()
                task.monday_item_id = item_id
                task.posted_to_monday = True
                task.save()
                
                # Create review action
                ReviewAction.objects.create(
                    task=task,
                    user=self.user,
                    action=ReviewAction.Action.APPROVE
                )
        
        # Assertions - all items should be successfully created
        self.assertEqual(len(results), len(self.tasks))
        self.assertTrue(all(results))  # All results should be truthy
        
        # Verify all tasks were updated
        for i, task in enumerate(self.tasks):
            task.refresh_from_db()
            self.assertEqual(task.status, Task.Status.APPROVED)
            self.assertEqual(task.monday_item_id, f"item_{i}")
            self.assertTrue(task.posted_to_monday)
            
            # Verify review action was created
            self.assertTrue(
                ReviewAction.objects.filter(
                    task=task,
                    action=ReviewAction.Action.APPROVE
                ).exists()
            )
            
    @patch('tests.test_monday_service.create_monday_item')
    def test_bulk_create_with_partial_failures(self, mock_create_monday_item):
        """Test bulk creation with some failures."""
        # Mock mixed success/failure responses
        # First and third tasks succeed, second and fourth fail
        mock_create_monday_item.side_effect = ["item_0", None, "item_2", None]
        
        # Process each task
        success_count = 0
        error_count = 0
        
        for task in self.tasks:
            item_id = create_monday_item(task)
            
            if item_id:
                task.status = Task.Status.APPROVED
                task.reviewed_at = timezone.now()
                task.monday_item_id = item_id
                task.posted_to_monday = True
                task.save()
                
                # Create review action
                ReviewAction.objects.create(
                    task=task,
                    user=self.user,
                    action=ReviewAction.Action.APPROVE
                )
                
                success_count += 1
            else:
                error_count += 1
        
        # Assertions
        self.assertEqual(success_count, 2)  # 2 successful items
        self.assertEqual(error_count, 2)    # 2 failed items
        
        # Verify task statuses
        self.tasks[0].refresh_from_db()
        self.assertEqual(self.tasks[0].status, Task.Status.APPROVED)
        self.assertEqual(self.tasks[0].monday_item_id, "item_0")
        
        self.tasks[1].refresh_from_db()
        self.assertEqual(self.tasks[1].status, Task.Status.PENDING)
        self.assertIsNone(self.tasks[1].monday_item_id)
        
        self.tasks[2].refresh_from_db()
        self.assertEqual(self.tasks[2].status, Task.Status.APPROVED)
        self.assertEqual(self.tasks[2].monday_item_id, "item_2")
        
        self.tasks[3].refresh_from_db()
        self.assertEqual(self.tasks[3].status, Task.Status.PENDING)
        self.assertIsNone(self.tasks[3].monday_item_id)


if __name__ == "__main__":
    unittest.main()
