# API Reference

> All endpoints accept/return JSON unless stated otherwise.

## Authentication
Currently no authentication is enforced (development phase). In production you should add Token or Session auth.

## Endpoints

### POST `/api/ingest/`
Ingest Fireflies → n8n payload.

**Request (truncated):**
```json
{
  "meeting_id": "01JYVYVEBV3VAK39NZTF1W12W1",
  "title": "Acme Q1 Planning",
  "tasks": [
    {
      "text": "Prepare Q1 roadmap",
      "assignee": "Alex",
      "due_date": "2025-01-15"
    }
  ],
  "transcript": {...}
}
```

**Response 201:**
```json
{"created": 5, "meeting": "01JYV...W1"}
```

---

### GET `/health/`
Returns migration status & DB connectivity.

```json
{"database":"OK","migrations":"Up-to-date"}
```

---

### HTML views
| Path | Template | Purpose |
|------|----------|---------|
| `/` | `home.html` | Marketing landing page |
| `/tasks/` | `public_tasks.html` | Public list of approved tasks |

### Admin paths
See Django admin for full CRUD. Relevant model proxies:
* `/admin/tasks/actionitem/` – review & approve tasks
* `/admin/tasks/rawtranscript/` – view raw transcripts 