# Updated Plan – 2025-07-02

_Incorporating live-run logs & current issues_

## 0 · Immediate environment gap

* Your dev server logs `MONDAY_API_KEY missing – skipping Monday API call`; the env variable is not loaded.
  * For local runs: `export MONDAY_API_KEY="sk-proj-…"` before `runserver`, or save it in `.env` (loaded by `environ.Env`).

---
## 1 · Public UI fixes

### 1-A Two-step **Approve** with "Undo"
1. Button triggers `confirmApprove(id)`.
2. Step 1 → `POST /api/tasks/<id>/act/` (no `confirm=true`) returns **202**; card shows a 3-sec bar with **Undo**.
3. After timeout JS sends same call with `?confirm=true` → only then HTMX removes the element.
4. If user clicks **Undo** → cancel timer; no second call.

### 1-B **Reject** UX
* Disable **Submit** until ≥ 5 words typed.
* On **400** response show toast with server error (e.g. "Rejection reason must be at least 5 words.").

---
## 2 · Seed command / data volume

### 2-A `seedactionitems`
* Switch from `get_or_create` to unconditional `create` so **all 14** tasks insert.
* Report inserted count at the end.

### 2-B Auto-defaults
* Command still ensures `MONDAY_BOARD_ID`, `MONDAY_GROUP_ID`, `MONDAY_COLUMN_MAP` exist.
* These rows override code defaults, so Admin can tweak later.

---
## 3 · `/api/health/` endpoint

Return sample JSON:
```json
{
  "postgres": "ok",
  "monday": {
    "token_present": true,
    "board": 9212659997,
    "group": "group_mkqyryrz",
    "api_status": "401 Unauthorized"  // or "ok"
  },
  "version": "git 238ab86"
}
```
* Probe Monday via `{ me { id } }` with 3-s timeout.
* Cache for 60 s to avoid spamming.
* Include short git SHA via `git rev-parse --short HEAD`.

---
## 4 · Admin side

* Run `python manage.py seedmonday` on fresh DBs.
* Admin → _App Settings_ shows board/group/column map for easy edits.
* **API key stays in env** – never committed.
* Verify bulk action **"Approve & send to Monday"** under `Tasks › Action items` works end-to-end after the Monday token is valid (look for success toast + item ID in logs).

---
## 5 · Execution order

1. Patch `templates/public_tasks.html` (confirm/undo + improved Reject).
2. Update `seedactionitems`; rerun:
   ```sh
   python manage.py flush
   python manage.py migrate
   python manage.py seedactionitems ACTION_ITEMS/…json
   ```
3. Add Monday probe to `tasks/health.py` and wire route.
4. Start dev server with `MONDAY_API_KEY` exported; check `/api/health/`.
5. Push & deploy.

---
_End of plan_ 