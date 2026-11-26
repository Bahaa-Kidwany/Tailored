# 07 — Authenticated Command Dashboard (`/dashboard`)

**Route:** `/dashboard`  
**Implementation Status:** **Never Implemented**  
**Primary User Goal:** Orient the returning candidate in `< 3 seconds` with one calm centered focus feed—showing today's top priority, active draft resume, top new matches, and overdue follow-ups with zero analytics clutter or competing right-side widgets.  
**Entry Points:** Default post-login home (`/login` → `/dashboard`), Global Sidebar (`G` then `D`), `/trial` completion when no specific job `pendingIntent` exists.  
**Exit Destinations:** `/studio`, `/cover-letters`, `/radar`, `/jobs/:id`, `/interest`, `/pipeline`, `/pipeline/:id`, `/plans`.  
**Credit Model Impact:** Free overview; displays live balance inside the single top priority strip and stamps `· 1 cr` on new generation triggers.

---

## 1. UX Reference Benchmarks & Ergonomic Rationale

| Reference | Pattern Adopted | Why It Beats Multi-Widget Dashboards |
| :--- | :--- | :--- |
| **Linear Home / Today** | **Calm Single-Column Action Feed (`max-w: 880px`)** + **Single Daily Priority Line** in header (*"2 follow-ups due · 1 active CV draft"*) | Eliminates two-column cockpit distractions and decorative KPI cards—every row on screen is a direct next step. |
| **Superhuman & Raycast** | Inline Quick-Ingest Box + `Spacebar` Quick-Peek Slide-Over Drawer | Lets user inspect a match or paste a URL without abandoning their home focus. |

---

## 2. Desktop Layout Architecture & ASCII Wireframe (`1440px`)

```
+---------------------------------------------------------------------------------------------------+
| GLOBAL SHELL (Left Nav 212px) | CALM CENTERED HOME FEED (/dashboard, max-width: 880px)            |
|-------------------------------|-------------------------------------------------------------------|
|                               | 1. SINGLE-LINE DAILY PRIORITY & QUICK INGEST                      |
|                               | Good morning, Mostafa · 2 follow-ups due · 1 draft · ⚡ 14 Credits|
|                               |                                                                   |
|                               | +---------------------------------------------------------------+ |
|                               | | Paste job URL, JD, or Ctrl+V screenshot to score (Free)   [Go]| |
|                               | +---------------------------------------------------------------+ |
|                               |                                                                   |
|                               | 2. RESUME WHERE YOU LEFT OFF (Max 1-2 Active Drafts)              |
|                               | +---------------------------------------------------------------+ |
|                               | | Swvl — Lead Data Scientist · CV Draft v3 (94% Fit · 10m ago)  | |
|                               | |                                   [Resume Studio (0cr)] [✉]   | |
|                               | +---------------------------------------------------------------+ |
|                               |                                                                   |
|                               | 3. TODAY'S TOP MATCHES (>=85% Fit · Free Discovery)               |
|                               | • Noon — Senior ML Engineer · Riyadh · 89% (AI Track)  [Tailor ·1cr]|
|                               | • Careem — AI Platform Lead · Dubai · 87% (AI Track)   [Peek Space]|
|                               | • Instabug — Data Scientist · Cairo · 86% (DS Track)   [Tailor ·1cr]|
|                               |                                    [Explore all 24 in Radar →]    |
|                               |                                                                   |
|                               | 4. NEEDS YOUR ATTENTION IN PIPELINE (Exceptions Only)             |
|                               | • Instabug — Applied 8 days ago (Follow-up due)   [Draft Follow-Up]|
|                               | • TechStart — CV & Cover Letter Ready             [Open Dispatch ✉]|
+-------------------------------+-------------------------------------------------------------------+
```

---

## 3. Eye-Scan Path & Anti-Saccade Map

1. **Fixation 1 (Top Daily Priority Line + Quick Ingest):** Single horizontal scan tells user *exactly* what needs attention today (`2 follow-ups due`, `14 Credits`) and gives instant URL/screenshot drop.
2. **Fixation 2 (Vertical Center Stream `880px`):** Natural top-to-bottom scan (`Resume Draft` → `Top 3 Matches` → `Pipeline Exceptions`). Zero right-hand widget rail pulling eyes sideways!
3. **Fixation 3 (Adjacent Quick-Peek `Spacebar`):** Opens cleanly only when inspecting a job row, preserving calm baseline layout.

---

## 4. Proximity & Click-Depth Budget

| User Intent | Click / Keystroke Depth | Spatial Location |
| :--- | :--- | :--- |
| **Resume active CV Studio draft** | `1` click (`[Resume Studio]`) | Section 2 Card |
| **Paste a new job URL or screenshot** | `Ctrl+V` anywhere OR paste + `Enter` | Top Quick Ingest Strip |
| **Quick-peek any match without leaving Home** | `Spacebar` or `1` click `[Peek]` | Match row → slide-over Quick-Peek Drawer |
| **Send overdue follow-up email** | `1` click (`[Draft Follow-Up]`) | Section 4 Pipeline row → pre-filled Dispatch Modal |
| **Switch active persona or regional phone** | `1` click on Left Shell Identity Capsule | Persistent Shell (`00` §4.1) — zero duplicated dashboard widget! |

---

## 5. Detailed Zone-by-Zone Component & Interaction Spec

- **Eliminated Widget Duplication:** Persona switching and Credit Balance already live persistently in the Left Shell (`212px`), so Dashboard does NOT duplicate a noisy right-hand Persona Card + Credit Card + Pipeline Stats Card column.
- **Section 2 (Resume Draft):** Collapses cleanly when no active draft exists (zero empty box).
- **Section 3 (Top Matches):** Shows strictly `3` highest-scoring un-applied roles with `Spacebar` Quick-Peek + 1 primary CTA per row (`[Tailor · 1 cr]` or `[Open Draft]` if already unlocked).
- **Section 4 (Pipeline Exceptions Only):** Shows only overdue follow-ups (`≥7 days`), ready-to-dispatch drafts, and upcoming interviews.

---

## 6. Interactivity, Adjustability & Keyboard Shortcuts

- **Keyboard:** `J`/`K` step through Dashboard items, `Space` opens Quick-Peek preview drawer, `Enter` executes the row's primary action, `/` focuses Top Quick Ingest input.

---

## 7. State Matrix & Edge Cases

| State | Behavior |
| :--- | :--- |
| **Brand New User (Post-Onboarding)** | Section 2 collapses; Section 3 shows freshly swept Radar matches; subtle banner invites `[Open First Job in CV Studio (2 Free Credits Ready)]`. |
| **Incomplete Profile (`< 70%`)** | Single calm notice line at top: *"Finish Work Experience in Profile to boost Fit Scores → [Finish Setup]"*. |
| **Zero Credits Remaining** | Top priority line gently highlights `⚡ 0 Credits · [Top Up from 49 EGP]` while all free discovery/pipeline features work normally. |

---

## 8. Frontend UI Implementation Contract

- **Suggested Components:** `DashboardPage`, `DailyPriorityAndIngestBar`, `ResumeActiveDraftBanner`, `TopMatchesQuietList`, `PipelineAttentionList`, `QuickPeekJobDrawer`.
- **State:** `recentDrafts: CvFitSummary[]`, `topMatches: JobItem[]`, `attentionItems: PipelineItem[]`, `focusedRowId`, `peekJob: JobItem | null`.
- **Backend Hooks:**
  - `GET /api/v1/jobs?min_score=80&limit=5` (`backend/app/api/routes/jobs.py`)
  - `GET /api/v1/cv-fit?profile_id=...` (`backend/app/api/routes/cv_fit.py`)
  - `GET /api/v1/pipeline` (`backend/app/api/routes/pipeline.py`)
- **UX Acceptance Criteria:**
  1. Single calm centered vertical column (`max-width: 880px`) with zero competing multi-widget right sidebar.
  2. Every list item has at most 1 primary visible CTA plus `Spacebar` Quick-Peek.
  3. Resuming an existing draft explicitly shows `0 cr`.
