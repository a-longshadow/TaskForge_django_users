# Monday Sync & Inline Decline — Implementation Plan

_Last updated: 2025-07-02_

---
## 1 · Public "Decline" fix

| Topic | Decision |
|-------|----------|
| 403 issue | Allow anonymous Decline when the request bears `X-Public-UI: true` header. |
| How | Amend `IsTaskReviewer` to **permit non-auth** requests if that header is present **and** the HTTP verb is unsafe. |
| Audit trail | `ReviewAction.user = NULL` for these actions. |
| Front-end | The HTMX call in the Decline button already lives in `public_tasks.html`; we'll add `hx-headers='{"X-Public-UI":"true"}'`. |

---
## 2 · Monday.com approve sync

### 2.1 Column map

| Field | Monday column ID |
|-------|------------------|
| team_member | `text_mkr7jgkp` |
| email | `text_mkr0hqsb` |
| person (people) | `people` |
| priority | `status_1` |
| status | `status` |
| due_date | `date5` |
| brief_description | `long_text` |

*Column `multiple_person_mkr7wdwf` is **never** sent.*

### 2.2 Config via AppSetting

* `MONDAY_BOARD_ID` – int
* `MONDAY_GROUP_ID` – string
* `MONDAY_COLUMN_MAP` – JSON blob (see table)

`create_monday_item(task)` will load these at runtime.

---
## 3 · Admin Enhancements

1. `ActionItemAdmin`
   * list_display → `status`, `priority`, `reviewed_at`, `posted_to_monday`
   * list_filter → same
2. Bulk actions
   * **Approve & Send to Monday** – uses helper, marks approved.
   * **Decline** – sets `status=rejected` and prompts for reason via admin's built-in confirmation page.

---
## 4 · Steps to code

1. Update `IsTaskReviewer` permission.
2. Front-end: add header in Decline HTMX.
3. Add AppSetting key + safe JSON getter.
4. Extend `tasks/services.py::create_monday_item` for group & columns.
5. Add admin actions and extra columns.
6. Unit tests:
   * Anonymous decline passes.
   * Monday payload omits forbidden column.
7. Commit & deploy. 