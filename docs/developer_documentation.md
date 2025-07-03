# TaskForge Developer Documentation

## Introduction

TaskForge is a Django-based system that automates the extraction of action items from meeting transcripts and facilitates their review and management. This document provides comprehensive technical information for developers working on the TaskForge codebase.

## System Architecture

TaskForge consists of three main components:

1. **Data Collection Pipeline** - Connects to Fireflies.ai at midnight to retrieve meeting transcripts
2. **Django Web Application** - Processes, stores, and displays tasks for review
3. **Monday.com Integration** - Syncs approved tasks to Monday.com boards

For a high-level overview of the system, see [TaskForge System Overview](./taskforge_system_overview.md).

## Core Technologies

- **Backend**: Django 4.2 with Django REST Framework
- **Database**: PostgreSQL (Railway deployment), SQLite (local development)
- **Frontend**: Tailwind CSS, HTMX for dynamic interactions
- **Deployment**: Railway platform
- **API Integration**: Monday.com GraphQL API

For detailed architecture information, see [Architecture Documentation](./architecture.md).

## Project Structure

The project follows a standard Django structure with these key components:

- **taskforge/** - Project settings, URLs, and global configuration
- **tasks/** - Core application containing models, views, and business logic
- **templates/** - HTML templates for public and admin interfaces
- **tests/** - Comprehensive test suite
- **docs/** - Project documentation

## Key Models

- **Meeting** - Represents a recorded meeting with metadata
- **Task** - Individual action items extracted from meetings
- **AppSetting** - Runtime configuration for Monday.com integration
- **ReviewAction** - Audit trail of approval/rejection decisions

For complete data model information, see [Project Overview](./project_overview.md).

## API Endpoints

TaskForge provides both REST API endpoints and HTML views:

- **POST /api/ingest/** - Accepts meeting transcripts and extracted tasks
- **GET /api/tasks/** - Lists tasks with optional filtering
- **POST /api/tasks/{id}/approve/** - Approves a specific task
- **POST /api/tasks/{id}/reject/** - Rejects a task with reason
- **GET /health/** - System health check endpoint

For complete API documentation, see [API Reference](./api.md).

## Admin Interface

The Django admin interface has been enhanced with:

- Custom confirmation dialogs for task actions
- Bulk approval/rejection functionality
- Improved Monday.com integration

For details on admin improvements, see [Admin Improvements](./admin_improvements.md).

## Monday.com Integration

TaskForge integrates with Monday.com to sync approved tasks:

- GraphQL API communication
- Configurable column mapping
- Error handling and logging

For troubleshooting Monday.com integration issues, see [Monday API Troubleshooting](./monday_api_troubleshooting.md).

## Local Development Setup

To set up a local development environment:

1. Clone the repository
2. Create a Python virtual environment
3. Install dependencies
4. Run migrations
5. Create a superuser
6. Start the development server

For detailed setup instructions, see [Setup Guide](./setup.md).

## Deployment

TaskForge is deployed on Railway with:

- PostgreSQL database
- Environment variables for configuration
- Automatic deployments from GitHub

For deployment details, see [Deployment Guide](./deployment.md).

## Testing

The project includes comprehensive tests:

- Unit tests for models and business logic
- Integration tests for API endpoints
- Mock-based tests for Monday.com integration

Run tests with:
```bash
pytest
```

For testing Monday.com integration specifically, use:
```bash
python manage.py test tests.test_monday_service --settings=tests.test_settings
```

## UI Improvements

The user interface has been enhanced with:

- Modern Tailwind CSS styling
- Modal confirmation dialogs
- Improved task editing workflow

For UI improvement details, see [UI Revision Plan](./ui_revision_plan.md).

## Contributing

When contributing to TaskForge:

1. Follow conventional commits
2. Ensure tests pass
3. Update documentation as needed

For contribution guidelines, see [Contributing Guide](./contributing.md).

## Troubleshooting

Common issues and their solutions:

- Monday.com API authentication errors
- Task approval/rejection issues
- Deployment problems

For detailed troubleshooting information, see [Project Overview](./project_overview.md) and [Monday API Troubleshooting](./monday_api_troubleshooting.md).

## Future Development

Planned enhancements include:

- Two-way Monday.com synchronization
- Real-time WebSocket updates
- Dark mode support
- Fine-grained permissions

## References

- [Project Overview](./project_overview.md)
- [Architecture Documentation](./architecture.md)
- [API Reference](./api.md)
- [Setup Guide](./setup.md)
- [Deployment Guide](./deployment.md)
- [Admin Improvements](./admin_improvements.md)
- [UI Revision Plan](./ui_revision_plan.md)
- [Monday API Troubleshooting](./monday_api_troubleshooting.md)
- [Contributing Guide](./contributing.md)
- [TaskForge System Overview](./taskforge_system_overview.md) 