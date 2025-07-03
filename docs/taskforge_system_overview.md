# TaskForge System Overview

## Overview

TaskForge is an automated system that extracts action items from meeting transcripts and makes them available for team review. The system runs daily at midnight, processes meeting recordings, and creates structured tasks that can be reviewed by both administrators and team members.

## Process Flow

1. **Data Collection** - At midnight, the system connects to Fireflies to retrieve meeting transcripts from the day.

2. **Task Extraction** - An AI assistant analyzes the transcripts to identify action items, including:
   - Task descriptions
   - Assigned team members
   - Priority levels
   - Due dates
   - Detailed context

3. **Admin Review** - A designated administrator receives a notification with all extracted tasks and can:
   - Approve tasks that are accurate
   - Reject tasks that are incorrect or unnecessary
   - Edit task details if needed

4. **User Review** - After admin approval, tasks are published to a web application where team members can:
   - View tasks assigned to them
   - Review task details and context
   - Mark tasks as complete
   - Provide updates on progress

5. **Task Lifecycle** - Approved tasks remain in the review system for 24 hours, giving team members time to acknowledge and begin work on their assignments.

## Key Features

- **Automated Extraction**: Eliminates manual note-taking during meetings
- **Intelligent Assignment**: Correctly identifies who should complete each task
- **Priority Management**: Categorizes tasks by importance (High/Medium/Low)
- **Due Date Tracking**: Sets reasonable deadlines based on meeting context
- **Two-Stage Review**: Admin verification followed by team member acknowledgment
- **Consolidated Dashboard**: All tasks visible in one central location

## Benefits

- Ensures important action items aren't forgotten after meetings
- Reduces miscommunication about task ownership and deadlines
- Provides accountability through the review process
- Creates a searchable record of all meeting-generated tasks
- Saves time by automating the task creation process

The system operates seamlessly in the background, requiring minimal intervention except for the admin approval step, which helps maintain task quality and relevance. 