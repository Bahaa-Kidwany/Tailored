# 08 — Job Radar & Opportunity Scanner (`/radar`)

**Route:** `/radar`  
**Implementation Status:** Implemented (`AtelierRadarPage.tsx`) — **Redesigned to Otta / Wellfound / Linear Calm Master-Detail Discovery** (replaces multi-dropdown clutter and busy cards with 3-item filter bar, 2-line quiet cards, plain-English "Why You Matched" line, and `X` negative triage)  
**Primary User Goal:** Rapidly scan ranked jobs across LinkedIn, Wuzzuf, and Recruiter Posts, immediately see *why* a role matches across active personas, hide noise in 1 keystroke, and launch CV Studio or Outreach in `1` click.  
**Entry Points:** Global Sidebar (`G` then `R`), Dashboard, Landing search (`/radar?q=...`), `← Back` from Studio/Job Detail.  
**Exit Destinations:** `/studio`, `/jobs/:id`, `/interest`, `/pipeline` + `DispatchApplicationModal` (eligible Recruiter Posts).  
**Credit Model Impact:** Discovery, Sweeping, Filtering, and 5-D Fit Scoring are **100% Free**; `[Tailor CV · 1 cr]` stamps cost upfront (or shows `[Open Draft]` `0 cr` if already tailored).

---

## 1. UX Reference Benchmarks & Ergonomic Rationale

| Reference | Pattern Adopted | Why It Beats Busy Job Boards |
| :--- | :--- | :--- |
| **Otta / Welcome to the Jungle** | **1-Line "Why You Matched"** narrative at top of Detail Pane + `[Hide / Not Interested]` (`X` key) negative triage | Explains fit in plain human language rather than raw numbers alone, and lets users clear irrelevant noise cleanly. |
| **Linear & Superhuman** | Minimal 3-control top bar (advanced filters inside `[Filters (N) ▾]` popover), ultra-quiet 2-line cards, `J`/`K` traversal | Removes visual fatigue so scanning 30 opportunities feels effortless. |
| **Tailored Zero-Drop Copilot** | Continuous ranking across all personas + constructive *Tailoring Opportunities* | Never deletes lower-scoring roles silently; every hidden job stays recoverable under `Filters -> Hidden`. |

---

## 2. Desktop Layout Architecture & ASCII Wireframe (`1440px`)

```
+---------------------------------------------------------------------------------------------------+
| GLOBAL SHELL (Left Nav 212px) | JOB RADAR WORKSPACE (/radar, flex-1, height: 100vh)               |
|-------------------------------|-------------------------------------------------------------------|
|                               | CALM TOP TOOLBAR (Height: 54px, Sticky — Strictly 4 Elements)     |
|                               | [🔍 Search title, company, skill...]  [Persona: Best Fit ▾]     |
|                               | [Filters (2) ▾]                       [↻ Live Sweep (Free)]       |
|                               |-------------------------------------------------------------------|
|                               | RESIZABLE MASTER-DETAIL SPLIT (38% / 62% · 8px Splitter)          |
|                               |                                                                   |
|                               | LEFT MASTER FEED (38%, 320-500px) | RIGHT STICKY INSPECTOR (62%)  |
|                               |-----------------------------------|-------------------------------|
|                               | 24 Ranked Jobs (0 dropped)        | STICKY INSPECTOR HEADER       |
|                               |                                   | Lead Data Scientist · Swvl    |
|                               | +-------------------------------+ | Cairo (Hybrid) · LinkedIn · 2h|
|                               | | [●] Swvl · Lead Data Sci  94% | |-------------------------------|
|                               | |     Cairo (Hybrid) · AI Track | | [⚡ Tailor CV · 1 cr]         |
|                               | +-------------------------------+ | [📌 Save]  [Apply LinkedIn ↗] |
|                               | |     Noon · Senior ML Eng  89% | | [Full 5-D Fit Report ↗]       |
|                               | |     Riyadh · AI Track · 5h    | |-------------------------------|
|                               | +-------------------------------+ | WHY YOU MATCHED (1-Line Note) |
|                               | |     Fawry · Data Analyst  82% | | ★ 94% on AI Engineer Track:   |
|                               | |     Cairo · Data Track · 1d   | | Matched Python, PyTorch, SQL, |
|                               | +-------------------------------+ | FastAPI; bridge AWS w/ Docker.|
|                               | |     TechStart · Backend   78% | |-------------------------------|
|                               | |     Remote · Recruiter ✉      | | SKILLS & TAILORING BRIDGES    |
|                               | +-------------------------------+ | ✓ Python  ✓ PyTorch  ✓ SQL    |
|                               |                                   | ✓ FastAPI   ⚠ AWS ECS (Bridge)|
|                               | Hover row reveals quiet:          |                               |
|                               | [📌 Save]  [✕ Hide (X)]           | RESPONSIBILITIES & FULL JD    |
+-------------------------------+-----------------------------------+-------------------------------+
```

---

## 3. Eye-Scan Path & Anti-Saccade Map

1. **Fixation 1 (Left Quiet Cards — 2 Lines Max):** `Role · Company + Fit %` on Line 1, `Location · Best Persona · Age` on Line 2. Hover exposes only Save/Hide—zero multi-button row walls.
2. **Fixation 2 (Directly Across Splitter — Inspector Header & 1-Line Why Matched):** Immediately explains *why* Swvl ranks #1 right beside `[Tailor CV · 1 cr]`.
3. **Fixation 3 (Down the Right Inspector):** Quick visual scan of Matched vs. Bridgeable Skills before reading Responsibilities & Raw JD.

---

## 4. Proximity & Click-Depth Budget

| User Intent | Click / Keystroke Depth | Spatial Location |
| :--- | :--- | :--- |
| **Step cleanly through jobs** | `J` / `K` (`1` key) | Left Master Feed → instant Right Inspector load |
| **Dismiss irrelevant job from active feed** | `X` key OR `1` click hover `[✕]` | Left Card hover → hides quietly with `5s` `[Undo]` toast |
| **Bookmark to Interest List** | `B` key OR `1` click `[📌 Save]` | Left Card hover AND Right Inspector Header |
| **Tailor CV for selected job** | `T` key OR `1` click `[⚡ Tailor CV · 1 cr]` | Sticky Right Inspector Header |
| **Apply / Send Email per Eligibility Rule** | `1` click (`[Apply on LinkedIn ↗]` or `[✉ Send Email]`) | Sticky Right Inspector Header |
| **Inspect deep 5-D & Multi-Persona report** | `Enter` OR `1` click `[Full 5-D Fit Report ↗]` | Sticky Right Inspector Header → `/jobs/:id` |

---

## 5. Detailed Zone-by-Zone Component & Interaction Spec

### 5.1 Calm `[Filters (N) ▾]` Popover (Zero Toolbar Crowding)
- Keeps Source (`All`, `LinkedIn`, `Wuzzuf`, `Recruiter Posts`), Work Mode (`Remote`, `Hybrid`, `On-site`), City Hub, Minimum Fit % slider (`0%–90%`), Sort (`Highest Fit` / `Newest`), and `[Show Hidden Jobs]` inside one compact popover directly under the filter button, showing active count `(2)`.

### 5.2 Strict Pipeline Eligibility Rule (Right Inspector Header)
- **Standard LinkedIn & Wuzzuf Board Listings:** Never display `Add to Pipeline` or `Send Email`. Show `[⚡ Tailor CV · 1 cr]`, `[📌 Save to Interest]`, `[Apply on LinkedIn/Wuzzuf ↗]`.
- **Recruiter Posts & Custom Extractions:**
  - *Email extracted:* `[✉ Send Email Application]` (adds to pipeline + opens `DispatchApplicationModal`), `[⚡ Tailor CV · 1 cr]`, `[📌 Save]`, `[Open Original Post ↗]`.
  - *No email extracted:* `[+ Add to Pipeline]`, `[⚡ Tailor CV · 1 cr]`, `[📌 Save]`, `[Open Original Post ↗]`.

### 5.3 Already-Tailored Smart Button
- Automatically checks `cvFits` for `(job_id, activePersonaId)`: switches `[⚡ Tailor CV · 1 cr]` into `[Open Tailored CV (v2 · 0 cr)]` so candidates never waste credits accidentally.

---

## 6. Interactivity, Adjustability & Keyboard Shortcuts

- **Resizable Splitter:** `38% / 62%` default (`320px–500px`), double-click resets, persisted in `localStorage`.
- **Keyboard:** `J`/`K` next/prev, `X` hide job (reversible), `B` bookmark, `T` tailor, `Enter` open `/jobs/:id`, `/` focus search, `R` run Live Sweep.

---

## 7. State Matrix & Edge Cases

| State | Behavior |
| :--- | :--- |
| **No Jobs Match Active Filters** | *"No active jobs match your filters (18 roles filtered or hidden)."* + `[Reset Filters]` + `[Run Live Sweep]`. |
| **Empty Feed (First Visit)** | *"Your Radar hasn't run its first sweep yet."* + `[Run Initial Sweep for {Active Persona}]`. |
| **Partial Scraper Failure** | *"Fetched 14 roles from Wuzzuf; LinkedIn actor timed out — showing cached LinkedIn listings alongside fresh results. [Retry LinkedIn]"* |

---

## 8. Frontend UI Implementation Contract

- **Suggested Components:** `RadarPage`, `CalmRadarToolbar`, `RadarFiltersPopover`, `QuietRadarCard`, `RadarDetailInspector`, `WhyMatchedSummaryLine`, `EligibilityActionCluster`.
- **State:** `jobs: JobItem[]`, `hiddenJobIds: Set<number>`, `selectedJobId`, `filters`, `personaScope`, `isSweeping`, `splitWidthPx`.
- **Backend Hooks:**
  - `GET /api/v1/jobs`, `POST /api/v1/jobs/auto-search`, `GET /api/v1/jobs/{job_id}` (`backend/app/api/routes/jobs.py`)
- **UX Acceptance Criteria:**
  1. Top bar holds max 4 uncluttered controls (`Search`, `Persona`, `Filters (N)`, `Live Sweep`).
  2. List cards stay strictly 2 clean lines; secondary actions appear gently on hover or in the adjacent inspector.
  3. Every job surfaces a 1-line plain-English "Why You Matched" summary and supports `X`-key hide with Undo safety.
