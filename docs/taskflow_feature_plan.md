# TaskFlow Feature Plan (Action-Item Review + Monday Sync)

_Last updated: 2025-07-02_

## 1. Data Model

| Model | Field | Notes |
|-------|-------|-------|
| **Task** | description (Text) | Editable by public UI |
|         | posted_to_monday (Bool, default False) | Flip after successful sync |
|         | reviewed_at (DateTime, null) | Set on approve / reject |
|         | rejected_reason (Text, blank) | ≥ 10 words when rejecting |
|         | expires_after_h (PositiveSmallInt, default **24**) | Age window for public visibility |
|         | meeting → Meeting FK | For grouping |
|         | created_at (auto) | Existing |
| **SecurityQuestion** | question_text | Seed 3 rows |
| **UserSecurityAnswer** | user FK / question FK / answer_hash | For optional reset |

Migration set will add the new Task columns and create the two security-question tables.

---

## 2. Public Interface (`/tasks/`)

* Group tasks by `meeting.title` in collapsible cards.
* Show only tasks matching:
  ```python
  Task.objects.filter(
      reviewed_at__isnull=True,
      created_at__gt=timezone.now() - timedelta(hours=F("expires_after_h"))
  )
  ```
* Card layout:
  * Description (textarea if user clicks _Edit_)
  * Countdown badge: "17 h left"
  * Buttons: **Edit (save)**, **Approve**, **Reject**
* UX details
  * HTMX / Alpine.js – no heavy framework
  * Toasts for success / failure (Tailwind + Toastify)
  * Buttons disabled once actioned
  * Page auto-refreshes every 30 s

Routes (Ajax JSON):
| Method | Path | Payload | Result |
|--------|------|---------|--------|
| PATCH  | `/api/task/<id>/edit/` | `{description}` | 200 or 400 |
| POST   | `/api/task/<id>/approve/` | – | 200 → toast, remove card |
| POST   | `/api/task/<id>/reject/` | `{reason}` | 200→remove / 400 on short reason |

---

## 3. Admin

* `/admin/tasks/actionitem/` proxy list shows all tasks, never pruned.
* Columns: description · meeting · posted_to_monday · reviewed_at · rejected_reason.
* Bulk action "Resend to Monday" (for approved ⇢ posted_to_monday=False).

---

## 4. Sync to Monday.com (synchronous)

* On approve, view posts to Monday immediately (max ≈50/day ⇒ OK).  
* Success → `posted_to_monday=True`; failures return 500 so UI shows "Sync failed".
* Mapping: task → Monday board, columns mapped in `settings.MONDAY_COLUMN_MAP`.

---

## 5. Reports

Management command `generate_task_report --period daily|weekly|monthly`  
Writes CSV + JSON to `media/reports/…` and registers a model in admin for download.

Scheduled via Railway cron:
```
0 0 * * *    daily
0 1 * * MON  weekly
0 2 1 * *    monthly
```

---

## 6. Password Reset (security-question)
* Endpoint `/api/reset-password-questions/` implemented (POST JSON).

---

## 7. Tech Stack & Packages
* Django 4.2, DRF, HTMX, Alpine.js, Tailwind (via CDN), Toastify.js.

---

## 8. Implementation Steps

1. **Models & Migrations** (Task new fields, questions tables).
2. Admin tweaks & bulk action.
3. REST endpoints (approve/reject/edit) + validations.
4. Public template + HTMX/JS interactions + toast styling.
5. Monday sync helper in `tasks/services.py`.
6. Management command for reports + Railway cron setup.
7. Unit & integration tests.
8. Update docs (`api.md`, architecture diagram).

---

_Approved_by_: `(awaiting review)` 