# Public Tasks UI — Rev 2 Plan

_Last updated: 2025-07-02_

This document captures the agreed-upon improvements to the `/tasks/` public interface and the small back-end tweaks that support them.

---
## 1. Visual Design

| Area | Current | Change |
|------|---------|--------|
| Page background | LIGHT - Purple gradient | Light gray-blue app shell (#F5F7FB), white content area |
| Card container | Semi-transparent GRAY | White cards with `border border-gray-200` & subtle shadow |
| Typography | White text | Dark gray (`text-gray-800`) primary, `text-gray-500` meta |
| Buttons | Green / red / LIGHT GREEN | Context colours: **Edit** `bg-gray-100` hover `bg-gray-200`; **Save** `bg-blue-600`; **Cancel** `bg-gray-100`; **Approve** `bg-emerald-600`; **Reject** `bg-red-600` |
| Accent colour | Toastify green only | Primary accent #0A57FF for links/tabs; Toasts use the same palette |

---
## 2. Interaction Changes

1. **Dropdowns** remain as meeting headers, but arrow rotates to show state.
2. **Editing flow**
   * Default description is plain `<p>`.
   * Clicking **Edit** converts it to a `<textarea>` and shows **Save** / **Cancel**.
   * **Save** → `PATCH /api/tasks/<id>/edit/?confirm=true` with `new_brief_description`.
   * On success, card re-renders with updated text and back to read-only mode.
3. **Reject**
   * Opens a Tailwind modal overlay (not browser `prompt`).
   * Modal contains a textarea + helper text "≥ 5 words" + **Submit**.
   * On submit via HTMX `POST /reject/?confirm=true` including `reason`, modal closes and task card is removed.
4. Word-count threshold lowered from 10 → **5**.

---
## 3. Back-end Adjustments

1. `TaskActionSerializer` validation: change minimum words to 5.
2. Update unit tests that assert the old 10-word limit.

_No DB migrations required._

---
## 4. Implementation Steps

1. **Serializer** update.
2. **Template** `templates/public_tasks.html`
   * Switch colour scheme (Tailwind classes).
   * Remove default autosave; add Edit/Save/Cancel JS.
   * Add modal markup for rejection.
3. **JavaScript**
   * Utility functions: `enterEdit(id)`, `saveEdit(id)`, `cancelEdit(id)`.
   * Modal logic `openRejectModal(id)`.
   * Toast handling unchanged.
4. **Tests**
   * Adjust `test_task_reject_requires_reason` to expect 5-word failure + success.
5. **Commit & deploy**.

---
## 5. Nice-to-haves (deferred)

* Countdown badge (time left) coloured by urgency.
* Keyboard shortcuts: `e` to edit, `a` approve, `r` reject.
* Real-time WebSocket updates.

These can be scheduled after UI Rev 2 is validated in production. 