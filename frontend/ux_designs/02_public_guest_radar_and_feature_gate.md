# 02 — Public Guest Job Radar & Feature Gate (`/explore`)

**Route:** `/explore`  
**Implementation Status:** **Never Implemented** (Defined as Epic 1 in `ux_redesign_specification.md`; missing from `App.tsx`)  
**Primary User Goal:** Browse curated live LinkedIn and Wuzzuf roles with clear plain-English "Why It Matches" context and inspect a real surgical CV diff preview *before* creating an account.  
**Entry Points:** Landing `[Explore Live Jobs]`, Omni-Bar role search while unauthenticated (`/explore?q=...`), shared job preview links.  
**Exit Destinations:** `/register` (carrying exact `pendingIntent`), `/login`, `/`.  
**Credit Model Impact:** 100% Free guest exploration; Feature Gate explicitly informs guests they receive **2 Free Credits** upon signup (`0` card required).

---

## 1. UX Reference Benchmarks & Ergonomic Rationale

| Reference | Pattern Adopted | Ergonomic Benefit for Tailored |
| :--- | :--- | :--- |
| **Otta & Wellfound** | Calm uncluttered feed + **1-Line "Why You Matched"** narrative + clean `[Hide]` negative triage (`X` key) | Prevents filter fatigue and builds instant understanding without noisy badge walls. |
| **Linear & Figma Public Previews** | Value-first open master-detail explorer (`38% / 62%`) gating *only* personalized save/tailor triggers | Lets candidates verify real scraped jobs and read full JDs before committing an email. |

---

## 2. Desktop Layout Architecture & ASCII Wireframe (`1440px`)

```
+---------------------------------------------------------------------------------------------------+
| GUEST TOP HEADER (Height: 56px, Sticky)                                                           |
| [← Tailored]   Guest Preview · Sample AI Track   [Drop CV for Your Fit Score]  [Sign In] [Sign Up]|
+---------------------------------------------------------------------------------------------------+
| STREAMLINED FILTER BAR (Height: 48px — Strictly 3 Controls)                                       |
| [🔍 Search roles or skills...]          [Filters (Source, Mode, City) ▾]   Showing 24 Live Roles  |
+---------------------------------------------------------------------------------------------------+
| RESIZABLE MASTER-DETAIL SPLIT (Calc height: 100vh - 104px · 8px Splitter)                         |
|                                                                                                   |
| LEFT JOB FEED (38%, 320-500px, quiet cards)    | RIGHT STICKY INSPECTOR (62%, flex-1)             |
|------------------------------------------------|--------------------------------------------------|
| +--------------------------------------------+ | STICKY HEADER                                    |
| | [●] Swvl — Lead Data Scientist       94%*  | | Lead Data Scientist · Swvl                       |
| |     Cairo (Hybrid) · LinkedIn · 2h         | | Cairo, Egypt (Hybrid) · LinkedIn · 2h ago        |
| +--------------------------------------------+ | [⚡ Tailor CV (2 Free Cr)] [📌 Save] [Apply ↗] |
| |     Noon — Senior ML Engineer        89%*  | |--------------------------------------------------|
| |     Riyadh (On-site) · LinkedIn · 5h       | | WHY THIS BENCHMARK MATCHES:                      |
| +--------------------------------------------+ | "Strong Python, PyTorch & FastAPI overlap plus   |
| |     Fawry — Product Data Analyst     82%*  |  Cairo mobility; gap in AWS ECS offset by Docker."|
| |     Cairo (On-site) · Wuzzuf · 1d          | [Unlock Your Personalized 5-D Fit Score →]       |
| +--------------------------------------------+ |                                                  |
| |     TechStart — Backend Engineer     78%*  | SURGICAL CV PREVIEW (Read-Only Teaser)           |
| |     Remote · Recruiter Post                | - Built routing APIs in Python                   |
| +--------------------------------------------+ | + Architected FastAPI & PyTorch (-42% latency)   |
|                                                |                                                  |
| (* Sample AI Engineer Benchmark)               | REQUIRED SKILLS & FULL JOB DESCRIPTION           |
| Hover card: quiet [📌 Save] [✕ Hide] icons     | (Clean vertical reading column)                  |
+------------------------------------------------+--------------------------------------------------+
```

---

## 3. Eye-Scan Path & Anti-Saccade Map

1. **Fixation 1 (Left Quiet Cards — Strictly 2 Lines Each):** Role & Match on Line 1, Location/Source/Age on Line 2. Zero badge clutter.
2. **Fixation 2 (Directly Right — Sticky Inspector Header & 1-Line Why Matched):** Cursor moves `40px` horizontally to read the plain-English match summary and trigger `[Tailor CV]`, `[Save]`, or `[Apply Externally ↗]`.
3. **Fixation 3 (Down the Right Inspector):** Calm reading of Surgical Teaser, Mandatory Skills, and Full Job Description.

---

## 4. Proximity & Click-Depth Budget

| User Intent | Click / Keystroke Depth | Spatial Location |
| :--- | :--- | :--- |
| **Inspect another job** | `1` click OR `J` / `K` | Left Job Feed |
| **Apply externally on LinkedIn/Wuzzuf** | `1` click (`[Apply ↗]` — 100% ungated!) | Sticky Right Inspector Header |
| **Hide irrelevant role during browse** | `X` key OR `1` click hover `[✕]` | Left card hover → hides quietly with `[Undo]` toast |
| **Trigger Tailor CV / Save / Real Fit Score** | `1` click (`[⚡ Tailor CV]` / `[📌 Save]`) | Sticky Right Inspector Header → Intent-Preserving Gate |
| **Fast-track with own CV** | Drag CV onto `[Drop CV for Your Fit Score]` | Top Header → parses CV + carries job to Sign-Up |

---

## 5. Detailed Zone-by-Zone Component & Interaction Spec

- **Streamlined `[Filters ▾]` Popover:** Houses Source (`All`, `LinkedIn`, `Wuzzuf`, `Recruiter Posts`), Work Mode (`Remote`, `Hybrid`, `On-site`), and Location Hubs inside a clean on-demand popover with a live `(N)` badge when active—keeping the top bar serene.
- **Honest Sample Benchmark Framing:** Every score carries an understated `*` note explaining it reflects a *Sample AI Engineer Benchmark* until the visitor uploads their own CV.
- **Intent-Preserving Feature Gate Modal:** Triggered only on `[Tailor CV]`, `[Save]`, or `[Unlock Your Score]`. Displays the exact selected job title/company, explains *"Includes 2 Free Credits — zero card required"*, and carries `pendingIntent` cleanly through `/register` → `/onboarding` → `/trial`.

---

## 6. Interactivity, Adjustability & Keyboard Shortcuts

- **Resizable Splitter:** `38% / 62%` default (`320px–500px`), double-click resets, persisted in `localStorage`.
- **Keyboard:** `J`/`K` traverse jobs, `X` hides job locally (with `[Undo]`), `/` focuses search, `Esc` closes Feature Gate Modal.

---

## 7. State Matrix & Edge Cases

| State | Behavior |
| :--- | :--- |
| **No Jobs Match Filters** | *"No public roles match these filters right now."* + `[Reset Filters]` + `[Paste a Job Link Instead]`. |
| **Loading Feed** | Quiet skeleton rows matching 2-line card height (zero layout jump). |
| **Expired Deep Link (`/explore?job=999`)** | Calm notice above inspector: *"This listing closed on the source board — showing similar active roles instead."* |
| **Signed-In User Lands on `/explore`** | Redirects automatically to `/radar` preserving `?q=...` and `?job=...`. |

---

## 8. Frontend UI Implementation Contract

- **Suggested Components:** `GuestExplorePage`, `GuestQuietHeader`, `CompactFilterPopover`, `QuietExploreCard`, `ExploreJobInspector`, `IntentGateModal`.
- **State:** `selectedJobId`, `hiddenJobIds: Set<number>`, `filters`, `gateTriggerIntent: PendingIntent | null`.
- **Backend Hooks:**
  - `GET /api/v1/jobs` (`backend/app/api/routes/jobs.py` — ensure unauthenticated public read guard returns benchmark scores safely `[Verify Public Guard]`).
- **UX Acceptance Criteria:**
  1. Left list cards stay strictly 2 clean lines (`Title/Fit` + `Meta`), with hover-only Save/Hide actions.
  2. External job links never trigger a login wall.
  3. Gated clicks preserve exact `jobId` inside `pendingIntent` through onboarding straight into Studio or Interest List.
