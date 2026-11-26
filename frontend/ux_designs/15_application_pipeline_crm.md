# 15 — Application Pipeline & Outreach CRM (`/pipeline`)

**Route:** `/pipeline` (supports `?stage=...`)  
**Implementation Status:** Implemented (`AtelierPipelinePage.tsx`) — **Redesigned from Noisy Kanban Grid to Linear Low-Strain Action-Sorted Master-Detail Split** (`Kanban Board` and `Dense Table` preserved as optional view toggles)  
**Primary User Goal:** Focus calmly on **what needs action today** (overdue 7-day follow-ups, ready-to-send applications, upcoming interviews) inside a low-strain master-detail workspace—without sensory overload from 40 colorful Kanban cards screaming for attention at once.  
**Entry Points:** Global Sidebar (`G` then `P`), Dashboard (`[Action Queue]` / `Pipeline Pulse`), Radar (`Send Email Application` / `Add to Pipeline`), Interest List.  
**Exit Destinations:** `/pipeline/:id` (Full Dossier & Interview Prep Hub), `/studio`, `/cover-letters`, `DispatchApplicationModal`.  
**Credit Model Impact:** Tracking, filtering, stage changes, inline email edits, and follow-up dispatching are **100% Free**; missing asset generation stamps `· 1 cr` transparently.

---

## 1. UX Reference Benchmarks & Ergonomic Rationale

| Reference | Pattern Adopted | Why It Beats Legacy Kanban Grids (Huntr / Teal) |
| :--- | :--- | :--- |
| **Linear Issues & Inbox** | **Default Action-Sorted Master-Detail Split (`42% / 58%`)** + single daily priority focus in header (*"2 follow-ups due today"*) + `J`/`K` keyboard flow | Huntr/Teal 5-column Kanban boards cause choice paralysis and visual glare at 25+ cards; grouping by *Next Action* keeps daily execution calm and clear. |
| **Attio CRM** | Click-to-edit inline recruiter email & stage pills + optional `[Board]` & `[Table]` view parity | Gives visual Kanban fans and spreadsheet power-users full flexibility without making everyone suffer visual clutter by default. |
| **Superhuman** | Single-key triage (`E` Archive, `Enter` Open Full Dossier, `S` Snooze reminder) + `5s` Undo toasts | High-velocity maintenance in `< 60 seconds` per day. |

---

## 2. Desktop Layout Architecture & ASCII Wireframe (`1440px`)

```
+---------------------------------------------------------------------------------------------------+
| GLOBAL SHELL (Left Nav 212px) | APPLICATION PIPELINE (/pipeline, flex-1)                          |
|-------------------------------|-------------------------------------------------------------------|
|                               | CALM PRIORITY HEADER & TOOLBAR (56px, Sticky)                     |
|                               | Pipeline · 2 follow-ups due today · 1 ready to send               |
|                               | [🔍 Search...]  Filter: [All Active (10) ▾]                       |
|                               | View: [● Focus Split] [Board] [Table]    [+ Paste Recruiter Post] |
|                               |-------------------------------------------------------------------|
|                               | DEFAULT VIEW: ACTION-SORTED FOCUS SPLIT (42% List / 58% Dossier)  |
|                               |                                                                   |
|                               | LEFT ACTION QUEUE (42%, 340-500px) | RIGHT ISOLATED PEEK (58%)    |
|                               |------------------------------------|------------------------------|
|                               | SECTION: FOLLOW-UP DUE (2)         | TechStart · AI Engineer      |
|                               | [●] Instabug — ML Lead             | Riyadh · LinkedIn Post ↗     |
|                               |     Cairo · Applied 8d ago · Due   | Stage: [In Process ▾]        |
|                               |------------------------------------| Recruiter: hr@techstart.io ✏ |
|                               | SECTION: READY TO DISPATCH (2)     |------------------------------|
|                               | [ ] TechStart — AI Engineer        | [✉ Dispatch Outreach]        |
|                               |     Riyadh · CV ✓ · CL ✓ · hr@...  | [Open Full Dossier (/id) ↗]  |
|                               |------------------------------------|------------------------------|
|                               | SECTION: INTERVIEWING (1)          | ASSETS & READINESS           |
|                               | [ ] Noon — Senior ML Engineer      | • Tailored CV v2 (1-Page OK) |
|                               |     Interview Tue 11:00 AM         |   [Open Studio] [↓ PDF]      |
|                               |------------------------------------| • Cover Letter Ready         |
|                               | SECTION: WAITING / SAVED (5)       |   [Edit in CL Studio]        |
|                               | [ ] Careem — Platform AI (87% Fit) |                              |
|                               |     Saved · Needs CV (1 cr)        | LATEST NOTES / TIMELINE      |
|                               | [ ] Fawry — Data Lead (81% Fit)    | Inline quick scratchpad...   |
+-------------------------------+------------------------------------+------------------------------+
```

---

## 3. Eye-Scan Path & Anti-Saccade Map

1. **Fixation 1 (Single Priority Line in Header):** Instead of 6 competing KPI counter cards, 1 clear sentence summarizes today's actionable load (*"2 follow-ups due today · 1 ready to send"*).
2. **Fixation 2 (Left Action-Sorted Queue):** Eyes scan clean, quiet, single-purpose rows grouped naturally by urgency (`Follow-Up Due` → `Ready to Dispatch` → `Interviewing` → `Waiting / Saved`) with **zero button walls on cards**.
3. **Fixation 3 (Adjacent Right Isolated Peek):** Clicking or `J`/`K` traversing any row populates its contact, CV/CL readiness, notes, and primary CTA (`[✉ Dispatch]`, `[Draft Follow-Up]`, or `[Tailor CV · 1 cr]`) immediately beside the row.

---

## 4. Proximity & Click-Depth Budget

| User Intent | Click / Keystroke Depth | Spatial Location |
| :--- | :--- | :--- |
| **Step through active applications** | `J` / `K` (`1` key) or `1` click | Left Action Queue updates Right Peek instantaneously |
| **Send ready application or 7-day follow-up** | `1` click (`[✉ Dispatch Outreach]`) | Top of Right Isolated Peek |
| **Edit missing recruiter email** | `1` click on `hr@techstart.io ✏` | Right Peek Header (or Table email cell) |
| **Change stage (`Saved` → `Interview`)** | `1` click dropdown OR drag in `[Board]` view | Right Peek Header (or Board/Table) |
| **Open full Frozen Snapshot & Interview Notes** | `Enter` on focused item OR `1` click `[Open Full Dossier ↗]` | Right Peek Header → `/pipeline/:id` |

---

## 5. Detailed Zone-by-Zone Component & Interaction Spec

### 5.1 Three Coordinated Views (`[● Focus Split]` | `[Board]` | `[Table]`)
1. **Focus Split (Default — Lowest Eye Strain):** Grouped by *Next Action*. Keeps secondary metadata hidden in the Right Peek until selected (`Linear` calm philosophy).
2. **Kanban Board (`[Board]`):** Clean 4 active columns (`Saved`, `In Process`, `Applied`, `Interview`, with `Archived` tucked into a filter toggle) for visual macro drag-and-drop. Cards strictly show `Company · Role`, `1 status/aging indicator`, and hover `[Peek]`/`[Dispatch]`—never 7 colorful tags!
3. **Dense Table (`[Table]`):** Spreadsheet mode with inline email editing and instant stage dropdowns for power users managing 30+ items.

### 5.2 Strict Pipeline Eligibility Enforcement
- Only **Recruiter Posts** and **Custom Extractions** (`recruiter_post`, `linkedin_posts`, `custom_post`, `description_paste`) can enter `/pipeline`.
- Pasting a standard LinkedIn/Wuzzuf board listing into `[+ Paste Recruiter Post]` expands a polite inline helper routing it cleanly to `/interest`: *"Standard LinkedIn/Wuzzuf postings are applied directly on their site — we added this to your **Interest List** so you can tailor your CV first. [Open in Interest List →]"*.

---

## 6. Interactivity, Adjustability & Keyboard Shortcuts

- **Resizable Focus Split:** `42% / 58%` default (`340px–500px` left queue), `8px` splitter, double-click reset, persisted in `localStorage`.
- **View & Archived Persistence:** Remembers chosen view (`Focus Split`, `Board`, or `Table`) and hides `Archived` clutter by default.
- **Keyboard:** `J`/`K` move selection, `Enter` open `/pipeline/:id`, `D` launch Dispatch Modal, `E` archive item (`5s` `[Undo]` toast), `V` cycle views.

---

## 7. State Matrix & Edge Cases

| State | Behavior |
| :--- | :--- |
| **Empty Pipeline** | *"Your pipeline tracks direct recruiter posts and outreach campaigns."* + `[+ Paste a Recruiter Post]` + `[Find Recruiter Posts in Radar →]`. |
| **Missing Recruiter Email on Dispatch** | Focuses inline email edit right inside Right Peek with hint: *"Add recruiter email to open Gmail, or copy pitch for LinkedIn DM."* |
| **Offline Persistence** | All stage changes, emails, and scratchpad notes save locally immediately and sync via `/pipeline/batch-import` upon reconnect. |

---

## 8. Frontend UI Implementation Contract

- **Suggested Components:** `PipelinePage`, `CalmPriorityHeader`, `ActionSortedFocusSplit`, `PipelineIsolatedPeek`, `PipelineKanbanBoard`, `PipelineDenseTable`, `InlineRecruiterPostIngestor`.
- **State:** `items: PipelineItem[]`, `viewMode: 'focus' | 'board' | 'table'`, `selectedId`, `stageFilter`, `showArchived: boolean`.
- **Backend Hooks:**
  - `GET /api/v1/pipeline`, `GET /api/v1/pipeline/metrics`, `POST /api/v1/pipeline`, `PATCH /api/v1/pipeline/{item_id}`, `DELETE /api/v1/pipeline/{item_id}` (`backend/app/api/routes/pipeline.py`)
  - `POST /api/v1/pipeline/{item_id}/tailor-cv`, `POST /api/v1/pipeline/{item_id}/cover-letter`, `POST /api/v1/pipeline/batch-import` (`backend/app/api/routes/pipeline.py`)
- **UX Acceptance Criteria:**
  1. Default `/pipeline` loads into the low-strain Action-Sorted Focus Split showing urgent follow-ups and ready dispatches first without colorful card noise.
  2. Header surfaces a single clear priority summary instead of 6 competing metric boxes.
  3. Switching to `[Board]` or `[Table]` retains filters and active selection cleanly.
