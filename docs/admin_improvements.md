# Admin Interface Improvements

This document outlines the improvements made to the Django admin interface for the TaskForge application, focusing on task review workflows and Monday.com integration.

## Overview of Changes

1. **Custom Confirmation Dialogs**
   - Replaced native browser confirmation dialogs with styled modal dialogs
   - Added dedicated confirmation templates for both individual and bulk actions
   - Improved user experience with clear visual feedback

2. **Individual Task Actions**
   - Added direct approve/reject buttons to task detail pages
   - Added action buttons to the task list view for quick actions
   - Implemented proper confirmation flow for all actions

3. **Monday.com Integration Fixes**
   - Fixed bulk actions for Monday.com integration
   - Corrected status mapping between Django and Monday.com
   - Added proper error handling and success/failure messages

## Implementation Details

### Custom Confirmation Templates

Two new templates were created:

1. `templates/admin/tasks/confirm_action.html` - For individual task approve/reject confirmations
   - Shows detailed task information
   - Provides clear action buttons
   - Includes rejection reason field when declining tasks

2. `templates/admin/tasks/confirm_bulk_action.html` - For bulk approve/reject confirmations
   - Lists all selected tasks
   - Provides clear action buttons
   - Handles multiple tasks in a single view

### Admin Model Improvements

The `ActionItemAdmin` class in `tasks/admin.py` was enhanced with:

- Custom `admin_actions` method to display action buttons in the list view
- Custom `action_buttons` method to display action buttons in the detail view
- Custom URL patterns for approve/reject actions
- Fixed bulk action handling by replacing `admin.ACTION_CHECKBOX_NAME` with `"_selected_action"`

### Monday.com Integration

### Overview
The TaskForge application integrates with Monday.com to synchronize approved tasks. Each approved task is sent to Monday.com as a new item in a specified board and group.

### Key Components
1. **API Integration**
   - Uses GraphQL API for Monday.com communication
   - Requires API key, board ID, group ID, and column mapping
   - All settings stored in AppSettings for runtime configurability

2. **Status Mapping**
   - Django task statuses map to Monday.com status options:
     - `pending` → "To Do"
     - `approved` → "Approved"
     - `rejected` → "Deprioritized"

3. **Error Handling**
   - Comprehensive logging of all API calls and responses
   - Detailed error messages for failed operations
   - Tracking of Monday.com item IDs for successful submissions

### Bulk Operations
Monday.com API does not support creating multiple items in a single request. Therefore, bulk operations are implemented by:

1. Processing each task individually in a loop
2. Tracking success/failure counts
3. Providing detailed error messages for failed items
4. Ensuring transaction integrity by only updating tasks that were successfully sent

### Configuration Requirements
To ensure Monday.com integration works properly, the following settings must be configured in AppSettings:

1. `MONDAY_API_KEY`: Your Monday.com API key (starts with "eyJhbG...")
2. `MONDAY_BOARD_ID`: ID of the target Monday.com board (e.g., "9212659997")
3. `MONDAY_GROUP_ID`: ID of the group within the board (e.g., "group_mkqyryrz")
4. `MONDAY_COLUMN_MAP`: JSON mapping of TaskForge fields to Monday.com columns

Example column map:
```json
{
  "team_member": "text",
  "email": "email",
  "priority": "status",
  "status": "status",
  "due_date": "date",
  "brief_description": "text"
}
```

### Troubleshooting
If tasks are not being sent to Monday.com, check:

1. **API Key**: Ensure the API key is valid and has write permissions
2. **Board/Group IDs**: Verify the board and group exist and are accessible
3. **Column Mapping**: Ensure column IDs match those in your Monday.com board
4. **Logs**: Check application logs for detailed error messages
5. **Network**: Verify the server can reach api.monday.com

Common errors:
- "Not authorized" - API key issues or permission problems
- "Board not found" - Incorrect board ID
- "Column not found" - Incorrect column mapping

## Technical Notes

### Django Admin Action Flow

1. User selects tasks in the admin list view
2. User selects an action from the dropdown
3. System redirects to a confirmation page
4. Upon confirmation, the action is executed
5. User is redirected back to the list view with success/error messages

### Monday.com API Integration

The Monday.com integration follows these steps:

1. Task is approved in Django admin
2. System calls `create_monday_item()` from `tasks/services.py`
3. GraphQL mutation is sent to Monday.com API
4. Response is processed and item ID is stored in the task
5. Task is marked as posted to Monday.com

## Troubleshooting

Common issues and their solutions:

1. **AttributeError: module 'django.contrib.admin' has no attribute 'ACTION_CHECKBOX_NAME'**
   - Fixed by replacing `admin.ACTION_CHECKBOX_NAME` with `"_selected_action"` in bulk action methods

2. **Monday.com API Errors**
   - Check API key in settings
   - Verify board ID and group ID
   - Ensure column mappings are correct
   - Check logs for detailed error messages

## Future Improvements

Potential areas for further enhancement:

1. Add more detailed status tracking for Monday.com sync
2. Implement two-way sync between Django and Monday.com
3. Add more granular permissions for task approval
4. Enhance the UI with more interactive elements 