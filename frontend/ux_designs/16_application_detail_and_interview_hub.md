# 16 — Application Detail, Frozen Snapshot & Interview Hub (`/pipeline/:id`)

**Route:** `/pipeline/:id`  
**Implementation Status:** **Never Implemented**  
**Primary User Goal:** Review the exact immutable CV & Cover Letter snapshot sent for a specific application, manage chronological outreach/follow-up history, prepare structured interview notes tied to the role's fit gaps, and maintain recruiter contact details in one dedicated dossier.  
**Entry Points:** `/pipeline` (`Enter` on row/card or `[↗]` button), `/dashboard` (`[Open Interview Prep Notes]`), `/notifications` (7-day follow-up alert).  
**Exit Destinations:** `/pipeline` (`← Back to Pipeline`), `/studio` (`[Fork Dispatched CV into New Draft]`), `DispatchApplicationModal` (`[Send Follow-Up Email]`).  
**Credit Model Impact:** **100% Free** (viewing frozen assets, downloading sent PDF, adding interview notes, and sending follow-ups consume `0` credits).

---

## 1. UX Reference Benchmarks & Ergonomic Rationale

| Reference | Pattern Adopted | Ergonomic Benefit for Tailored |
| :--- | :--- | :--- |
| **Attio Record Page** | Top interactive Stage Rail + `62%` Left Chronological Activity & Prep Workspace + `38%` Right Sticky Metadata Inspector | Unifies documents, recruiter info, and interview notes so candidates never dig through downloads folders before a call. |
| **Linear Issue Detail** | `← Prev / Next ›` record stepper in top breadcrumb + optimistic stage updates | Lets candidates review 5 active applications consecutively with zero back-and-forth navigation. |
| **Notion Interview Workspace** | Structured interview prep blocks auto-seeded from the job's Match & Gap Breakdown | Converts "Tailoring Opportunities" (e.g., *"AWS scaling gap"*) directly into pre-interview talking points. |

---

## 2. Desktop Layout Architecture & ASCII Wireframe (`1440px`)

```
+---------------------------------------------------------------------------------------------------+
| GLOBAL SHELL (Left Nav 220px) | APPLICATION DOSSIER (/pipeline/42, max-w: 1280px)                 |
|-------------------------------|-------------------------------------------------------------------|
|                               | TOP BREADCRUMB & STAGE PROGRESS RAIL (Sticky, 88px)               |
|                               | [← Pipeline]  TechStart — Senior AI Engineer    [‹ Prev] [Next ›] |
|                               | Stage: [Saved ✓] ─ [In Process ✓] ─ [Applied ✓] ─ [● Interview] ─ [Archived]|
|                               |-------------------------------------------------------------------|
|                               | RESIZABLE 2-COLUMN RECORD SPLIT (62% Left / 38% Sticky Right)     |
|                               |                                                                   |
|                               | LEFT RECORD WORKSPACE (62%)        | RIGHT METADATA INSPECTOR(38%)|
|                               |------------------------------------|------------------------------|
|                               | TABS: [Overview & Assets]          | RECRUITER & OUTREACH CONTACT |
|                               |       [Interview Prep & Notes]     | Name:  [Sara Mansour    ✏ ]  |
|                               |       [Job Spec & 5-D Fit]         | Email: [hr@techstart.io ✏ ]  |
|                               |------------------------------------| Phone: [+20 10...       ✏ ]  |
|                               | 1. FROZEN DISPATCHED PACKAGE       | Source:[LinkedIn Post ↗]     |
|                               | (Immutable copy sent Nov 12, 14:20)|------------------------------|
|                               | +--------------------------------+ | SCHEDULE & REMINDERS         |
|                               | | 📄 Sent_CV_TechStart_v2.pdf    | | Applied: Nov 12, 2026        |
|                               | |    Phone used: +20 EG Mobile   | | Follow-Up: [Nov 21 (Due) ▾]  |
|                               | |    [👁 Preview] [↓ Download]   | | Interview: [Nov 24 · 11:00AM]|
|                               | |    [Fork into Studio (0 cr)]   | |------------------------------|
|                               | +--------------------------------+ | MATCH SNAPSHOT               |
|                               | | 📝 Sent Cover Letter / Pitch   | | 88% Match (AI Engineer Track)|
|                               | |    "Dear Sara, Having built..."| | Key Gap Watchout:            |
|                               | |    [View Full] [Copy]          | | • Kubernetes scaling (Prep!) |
|                               | +--------------------------------+ |------------------------------|
|                               |                                    | QUICK RECORD ACTIONS         |
|                               | 2. OUTREACH & FOLLOW-UP TIMELINE   | [✉ Send Follow-Up / Reply]   |
|                               | • Nov 12: Applied via Gmail Web    | [Archive Application]        |
|                               | • Nov 19: 7-day follow-up nudge    | [Delete from Pipeline]       |
|                               |   [✉ Draft 7-Day Follow-Up Email]  |                              |
|                               |                                    |                              |
|                               | 3. QUICK SCRATCHPAD & PREP NOTES   |                              |
|                               | (Auto-saves on blur)               |                              |
|                               | [ Round 1 screen: asked about... ] |                              |
+-------------------------------+------------------------------------+------------------------------+
```

---

## 3. Eye-Scan Path & Anti-Saccade Map

1. **Fixation 1 (Top Stage Progress Rail):** Immediately confirms where the application stands (`Applied` vs `Interview`) and enables 1-click progression.
2. **Fixation 2 (Left Section 1 — Frozen Dispatched Package):** Directly answers *"Which exact CV version did I send them?"*—crucial 5 minutes before a recruiter phone screen.
3. **Fixation 3 (Right Sticky Recruiter & Schedule Inspector):** Contact info, interview datetime, and `[✉ Send Follow-Up]` live beside the notes without scrolling past a long JD.

---

## 4. Proximity & Click-Depth Budget

| User Intent | Click / Keystroke Depth | Spatial Location |
| :--- | :--- | :--- |
| **Advance stage (e.g., Applied → Interview)** | `1` click on stage pill | Top Sticky Stage Progress Rail |
| **Download/preview exact CV sent to recruiter** | `1` click (`[👁 Preview]` / `[↓ Download]`) | Left Tab 1 (`Frozen Dispatched Package`) |
| **Send 7-day follow-up email** | `1` click (`[✉ Draft Follow-Up Email]`) | Timeline card OR Right Inspector CTA → opens Dispatch Modal pre-populated |
| **Seed interview prep from job gaps** | `1` click on `[Seed Gap Talking Points]` | Inside `Interview Prep & Notes` tab |
| **Edit recruiter name, email, or interview date** | `1` click inline on field | Right Sticky Metadata Inspector |

---

## 5. Detailed Zone-by-Zone Component & Interaction Spec

### 5.1 Frozen Dispatched Snapshot Protection
- Shows a clear **`Immutable Sent Copy`** badge on the CV PDF and Cover Letter attached when `status` transitioned to `applied`, preventing future edits in `/studio` from altering historical truth.
- Clicking `[Fork into Studio]` creates an independent `Draft` clone if the user needs an updated CV for a second round.

### 5.2 Structured Interview Prep & Notes Tab
- Auto-populates two collapsible prompt sections from the job's 5-D analysis:
  1. **Likely Gap Questions to Prepare For:** Derived from missing skills / continuous experience gap (*"They asked for Kubernetes; prepare your Docker/ECS scaling story from Swvl"*).
  2. **Round-by-Round Notes:** Timestamped structured blocks (`Recruiter Screen`, `Technical Round`, `System Design`, `Offer / Compensation`) with auto-save on blur.

### 5.3 Follow-Up Scheduling & Snooze
- Candidate sets a `Follow-Up Reminder Date` (defaults to `+7 days` from `applied_at` if unresponded); powers nudges in `/dashboard` and `/notifications`.

---

## 6. Interactivity, Adjustability & Keyboard Shortcuts

- **Resizable Split:** `62% / 38%` default (`min 320px` right inspector), double-click resets, persisted in `localStorage`.
- **Keyboard:** `[` / `]` cycles previous/next application in current Pipeline filter; `Esc` returns to `/pipeline`; `N` focuses Interview Notes editor.

---

## 7. State Matrix & Edge Cases

| State | Behavior |
| :--- | :--- |
| **Application Still in `Saved` / `In Process` (No Dispatched Assets Yet)** | Section 1 clearly shows readiness checklist (*"No CV tailored yet"*) with 1-click `[⚡ Tailor CV · 1 cr]` and `[Draft Cover Letter · 1 cr]` triggers right in place. |
| **Deleted / Missing Pipeline Item (`/pipeline/999`)** | Clean recovery message: *"We couldn't find that application record."* + `[Return to Pipeline]` + `[Cmd+K Search]`. |
| **Unsaved Notes on Navigation** | Auto-saves asynchronously on `500ms` debounce with visible `Saved` indicator; warns only if network request fails while retaining text in `localStorage`. |

---

## 8. Frontend UI Implementation Contract

- **Suggested Components:** `ApplicationDetailPage`, `StageProgressHeader`, `FrozenPackageSection`, `OutreachTimeline`, `InterviewPrepWorkspace`, `RecruiterInspectorRail`.
- **State:** `pipelineItem: PipelineItem`, `frozenCvDetail`, `interviewNotes`, `followUpDate`, `activeTab: 'overview' | 'interview' | 'job_spec'`.
- **Backend Hooks:**
  - `GET /api/v1/pipeline/{item_id}` & `PATCH /api/v1/pipeline/{item_id}` (`backend/app/api/routes/pipeline.py`)
  - `GET /api/v1/cv-fit/{doc_id}` (`backend/app/api/routes/cv_fit.py`)
  - `PATCH /api/v1/pipeline/{item_id}/interview-notes` `[Enhance PipelineItemUpdate schema for structured rounds, recruiter name/phone, and follow_up_date]`
- **UX Acceptance Criteria:**
  1. Sent CV PDF and Cover Letter remain locked as immutable historical snapshots once dispatched.
  2. Interview Prep seamlessly pulls constructive gap strategies from the job's 5-D fit profile.
  3. Inline recruiter edits and stage clicks persist optimistically with `[Undo]` toast.
