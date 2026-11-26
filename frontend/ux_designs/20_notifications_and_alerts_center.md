# 20 — Notifications & Job Match Digest Center (`/notifications` & Quick Drawer)

**Route / Trigger:** `/notifications` (Full Inbox) AND Global Bell Quick-Drawer (`[🔔 Alerts]`)  
**Implementation Status:** **Never Implemented**  
**Primary User Goal:** Review high-signal career alerts—new `≥85%` job matches from background Radar sweeps, `7-day` application follow-up nudges, CV/LaTeX compile outcomes, and low-credit alerts—and act on them in `1` click directly inside an adjacent preview without losing context.  
**Entry Points:** Global Sidebar Bell icon (Quick Drawer → `[Open Full Inbox ↗]`), email digest deep links, Command Palette (`Go to Notifications`).  
**Exit Destinations:** `/studio`, `/radar`, `/pipeline/:id`, `DispatchApplicationModal`, `/plans`.  
**Credit Model Impact:** **100% Free**; action buttons inside match alerts pre-stamp `[Tailor CV · 1 cr]` transparently.

---

## 1. UX Reference Benchmarks & Ergonomic Rationale

| Reference | Pattern Adopted | Ergonomic Benefit for Tailored |
| :--- | :--- | :--- |
| **Linear Inbox** | Master-detail triage queue (`40% / 60%`) with `J`/`K` navigation, `E` mark read/archive, and direct embedded contextual preview + action bar | Turns passive alerts into an active command queue—no clicking a notification only to hunt for the action on another screen. |
| **Superhuman Snooze** | `S` Snooze reminder (`Tomorrow`, `3 Days`, `Next Week`) directly on follow-up nudges | Lets candidates defer a follow-up cleanly instead of dismissing it and forgetting. |

---

## 2. Desktop Layout Architecture & ASCII Wireframe (`1440px`)

### Part A: Quick Slide-Over Drawer (From Global Rail Bell — Zero Context Loss)
```
+---------------------------------------------------------------+
| NOTIFICATIONS  (3 Unread)     [Mark all read] [Full Inbox ↗]  |
|---------------------------------------------------------------|
| • ★ 94% Match: Swvl — Lead Data Scientist (2h ago)            |
|   Matched 5/5 skills · [Quick Tailor · 1 cr] [Inspect]        |
|---------------------------------------------------------------|
| • ⏰ 7-Day Follow-Up Due: Instabug — ML Lead (6h ago)         |
|   Applied Nov 12 · [Draft Follow-Up ✉] [Snooze 3d]            |
|---------------------------------------------------------------|
| • ✓ PDF Ready: Noon — Senior ML Engineer v2 (1d ago)          |
|   1-Page ATS Compiled · [Download PDF] [Open Studio]          |
+---------------------------------------------------------------+
```

### Part B: Dedicated `/notifications` Triage Inbox (`1440px`)
```
+---------------------------------------------------------------------------------------------------+
| GLOBAL SHELL (Left Nav 220px) | NOTIFICATIONS INBOX (/notifications, flex-1)                      |
|-------------------------------|-------------------------------------------------------------------|
|                               | HEADER & CATEGORY FILTER BAR (60px)                               |
|                               | Inbox   [All (9)] [High-Fit Matches (4)] [Follow-Ups (2)] [System] |
|                               |         [Mark All Read] [Archive Read] [Alert Rules (/account ↗)] |
|                               |-------------------------------------------------------------------|
|                               | RESIZABLE MASTER-DETAIL SPLIT (40% List / 60% Resolution Preview) |
|                               |                                                                   |
|                               | LEFT ALERT STREAM (40%, 340-500px) | RIGHT RESOLUTION PANE (60%)  |
|                               |------------------------------------|------------------------------|
|                               | [●] ★ 94% Match: Swvl · Lead DS    | RESOLUTION HEADER            |
|                               |     Cairo · LinkedIn · 2h ago      | New Exceptional Match (94%)  |
|                               |     [Mark Read] [Snooze]           | Swvl — Lead Data Scientist   |
|                               |------------------------------------| [⚡ Tailor CV · 1 cr]        |
|                               | [●] ⏰ Follow-Up Due: Instabug     | [📌 Save to Interest]        |
|                               |     Applied 8 days ago · No reply  | [Open Full 5-D Fit ↗]        |
|                               |------------------------------------|------------------------------|
|                               | [ ] ✓ PDF Compiled: Noon ML Eng v2 | MATCH HIGHLIGHTS PREVIEW     |
|                               |     1-Page OK · Yesterday          | • Best Persona: AI Engineer  |
|                               |------------------------------------| • Matched: Python, PyTorch,  |
|                               | [ ] ⚡ Low Credit Notice (2 cr)    |   FastAPI, SQL, Docker       |
|                               |     1 full application remaining   | • Gap Bridge: Mention ECS    |
|                               |                                    |   experience for AWS ask.    |
|                               |                                    |                              |
|                               |                                    | Key Responsibilities & JD... |
+-------------------------------+------------------------------------+------------------------------+
```

---

## 3. Eye-Scan Path & Anti-Saccade Map

1. **Fixation 1 (Top Filter Tabs):** Segregate urgent outreach nudges (`Follow-Ups`) from job discoveries (`High-Fit Matches`).
2. **Fixation 2 (Left Alert Row → Adjacent Right Resolution Pane):** Selecting an alert immediately displays the full resolution preview and 1-click CTA (`[Tailor CV · 1 cr]`, `[Draft Follow-Up]`, or `[Top Up]`) right across the `8px` splitter.
3. **Anti-Saccade Rule:** Never require navigating through 3 pages just to check why an alert fired or snooze a follow-up.

---

## 4. Proximity & Click-Depth Budget

| User Intent | Click / Keystroke Depth | Spatial Location |
| :--- | :--- | :--- |
| **Peek recent unread alerts from anywhere** | `1` click on `[🔔 Alerts]` | Global Sidebar bottom utility → Quick Slide-Over Drawer |
| **Triage notifications rapidly via keyboard** | `J` / `K` (`1` key) + `E` archive / `S` snooze | Full Inbox (`/notifications`) |
| **Act directly on a match or follow-up** | `1` click (`[Tailor CV · 1 cr]` or `[Draft Follow-Up ✉]`) | Directly on Drawer item OR Right Resolution Header |
| **Adjust alert rules / digest frequency** | `1` click (`[Alert Rules ↗]`) | Top-right Inbox Toolbar → `/account#notifications` |

---

## 5. Detailed Zone-by-Zone Component & Interaction Spec

- **Four Signal-Focused Notification Categories (Zero Spam):**
  1. **High-Fit Matches:** Jobs crossing user's configured threshold (`≥85%` or `≥90%`) during background sweeps, grouped cleanly to avoid notification floods.
  2. **Pipeline Follow-Up Nudges:** `7-day` unresponded applications or upcoming interview reminders.
  3. **Document & Compile Status:** Async `.tex → PDF` compile results or automatic failure credit refunds.
  4. **Credits & Billing:** Low-balance warning (`≤ 2 cr`) or confirmed Paymob/Stripe pack credit top-ups.
- **Snooze Control (`S`):** Clicking `[Snooze]` lets user pick `Tomorrow 9 AM`, `In 3 Days`, or `Next Monday` cleanly.

---

## 6. Interactivity, Adjustability & Keyboard Shortcuts

- **Resizable Split:** `40% / 60%` default (`340px–500px` left stream), double-click resets, persisted in `localStorage`.
- **Keyboard:** `J`/`K` traverse alerts, `E` mark read/archive (with `[Undo]` toast), `S` open snooze menu, `Enter` execute primary resolution CTA.

---

## 7. State Matrix & Edge Cases

| State | Behavior |
| :--- | :--- |
| **Inbox Zero (All Caught Up)** | *"You're all caught up — no unread matches or overdue follow-ups."* + `[Run Live Radar Sweep]` + `[Adjust Alert Thresholds in Account]`. |
| **Stale Job Alert (Listing Expired)** | Clearly marks right resolution pane: *"This role closed since the alert was sent."* + `[Archive]` + `[See Similar Active Jobs in Radar →]`. |

---

## 8. Frontend UI Implementation Contract

- **Suggested Components:** `NotificationsInboxPage`, `NotificationsQuickDrawer`, `NotificationCategoryTabs`, `NotificationAlertRow`, `NotificationResolutionPane`, `SnoozePopover`.
- **State:** `notifications: NotificationItem[]`, `unreadCount`, `selectedId`, `categoryFilter`, `isDrawerOpen`.
- **Backend Hooks:**
  - `GET /api/v1/notifications`, `PATCH /api/v1/notifications/{id}/read`, `PATCH /api/v1/notifications/{id}/snooze`, `POST /api/v1/notifications/mark-all-read` `[New Endpoints Needed]`
- **UX Acceptance Criteria:**
  1. Quick Drawer lets users act on or snooze alerts without losing their place in Radar, Studio, or Pipeline.
  2. Zero noisy marketing popups; every alert maps directly to a concrete action.
  3. Keyboard triage (`J`/`K`/`E`/`S`) operates smoothly with `5s` `[Undo]` safety.
