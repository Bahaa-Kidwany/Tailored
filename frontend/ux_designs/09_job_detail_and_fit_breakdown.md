# 09 — Job Detail & 5-Dimensional Fit Breakdown (`/jobs/:id`)

**Route:** `/jobs/:id`  
**Implementation Status:** **Never Implemented** (Currently only a basic breakdown modal stub exists inside `CVStudioWorkbench.tsx`)  
**Primary User Goal:** Deeply understand *how* and *why* a candidate scores against a specific role across all 5 dimensions and all career personas—and build an exact tailoring game plan—**before** spending 1 credit in CV Studio.  
**Entry Points:** `/radar` (`[Full 5-D Fit Report ↗]` or `Enter` on selected job), `/interest` card inspect, `/dashboard` match inspect, `/notifications` match alert link.  
**Exit Destinations:** `/studio?job_id=:id&persona=:p` (carrying selected tailoring focus), `/cover-letters?job_id=:id`, `/radar` (`← Back to Radar`), `/pipeline` (`Dispatch` if eligible).  
**Credit Model Impact:** **100% Free** deep analytical view (per business strategy: Fit-Gap analysis hooks trust before spending 1 credit on tailoring).

---

## 1. UX Reference Benchmarks & Ergonomic Rationale

| Reference | Pattern Adopted | Ergonomic Benefit for Tailored |
| :--- | :--- | :--- |
| **Jobscan Diagnostic Report** | Side-by-side requirement checklist + quantified dimension bars + concrete fix recommendations | Makes match scoring explainable rather than a mysterious black-box number. |
| **Linear Full Issue Page** | Left rich document context + Right sticky diagnostic/metadata/action sidebar (`60% / 40%`) | Separates reading the company spec from inspecting diagnostic telemetry and clicking next actions. |
| **Tailored Zero-Drop Copilot** | Multi-Persona Score Comparison Matrix + Continuous Experience Curve visual | Shows candidates which persona maximizes their chances and converts missing requirements into bridging strategies. |

---

## 2. Desktop Layout Architecture & ASCII Wireframe (`1440px`)

```
+---------------------------------------------------------------------------------------------------+
| GLOBAL SHELL (Left Nav 220px) | JOB DIAGNOSTIC PAGE (/jobs/101, max-w: 1280px)                    |
|-------------------------------|-------------------------------------------------------------------|
|                               | TOP BREADCRUMB & QUICK SWITCH BAR (52px, Sticky)                  |
|                               | [← Back to Radar]   Swvl / Lead Data Scientist   [‹ Prev] [Next ›]|
|                               |-------------------------------------------------------------------|
|                               | RESIZABLE 2-COLUMN SPLIT (58% Spec & Strategy / 42% Diagnostic)   |
|                               |                                                                   |
|                               | LEFT: ROLE SPEC & TAILORING PLAYBOOK (58%) | RIGHT: STICKY 5-D    |
|                               |--------------------------------------------| DIAGNOSTIC & CTA(42%)|
|                               | HEADER                                     |----------------------|
|                               | Lead Data Scientist (Dynamic Pricing)      | COMPOSITE SCORE      |
|                               | Swvl · Cairo, Egypt (Hybrid) · LinkedIn    | [ 94% ] Exceptional  |
|                               | Posted 2h ago · Recruiter: None (Board)    | Best Persona:        |
|                               |                                            | ★ Senior AI Engineer |
|                               | 1. CONSTRUCTIVE TAILORING OPPORTUNITIES    |----------------------|
|                               | (Every gap paired with Master Profile fix) | MULTI-PERSONA COMPARE|
|                               | +----------------------------------------+ | (Click to switch)    |
|                               | | Gap: "5 yrs AWS production scale"      | | • AI Engineer    94% |
|                               | | Bridge: Highlight Swvl Docker/ECS +    | | • Data Scientist 88% |
|                               | | 1,400 route throughput metrics.        | | • Backend Arch   76% |
|                               | | [✓ Include in Studio Focus]            | |----------------------|
|                               | +----------------------------------------+ | 5-DIMENSION WEIGHTS  |
|                               |                                            | 1. Skills (35%)  92% |
|                               | 2. REQUIREMENT-BY-REQUIREMENT SKILL MATRIX | 2. Title  (20%)  95% |
|                               | Mandatory: [✓ Python] [✓ PyTorch] [✓ SQL]  | 3. Exp    (20%)  88% |
|                               |            [✓ FastAPI] [⚠ AWS ECS]         | 4. Proj   (15%)  96% |
|                               | Nice-to-Have: [✓ Docker] [○ Kubernetes]    | 5. Loc    (10%) 100% |
|                               |                                            |----------------------|
|                               | 3. CORE RESPONSIBILITIES & EXTRACTED FACTS | EXISTING ARTIFACTS   |
|                               | • Architect dynamic route pricing...       | Draft v2 exists (0cr)|
|                               | • Deploy low-latency FastAPI endpoints...  |----------------------|
|                               |                                            | PRIMARY ACTIONS      |
|                               | 4. FULL ORIGINAL JOB DESCRIPTION           | [⚡ Tailor CV · 1 cr]|
|                               | (Collapsible/Searchable raw source text)   | [✉ Cover Letter ·1cr]|
|                               |                                            | [📌 Save to Interest]|
|                               |                                            | [Apply on LinkedIn ↗]|
|                               |                                            | [💬 Ask AI About Fit]|
+-------------------------------+--------------------------------------------+----------------------+
```

---

## 3. Eye-Scan Path & Anti-Saccade Map

1. **Fixation 1 (Top-Right Composite Score & Primary CTA):** Immediately answers *"Is this role worth my effort, and which persona should I use?"* right beside the button to act.
2. **Fixation 2 (Left Section 1 — Tailoring Opportunities):** Directly across the divider, candidate sees *how* to bridge any gaps using real Master Profile facts.
3. **Fixation 3 (Right Multi-Persona Matrix & 5-D Breakdown + Left Skill Matrix):** Smooth diagnostic verification before launching CV Studio.

---

## 4. Proximity & Click-Depth Budget

| User Intent | Click / Keystroke Depth | Spatial Location |
| :--- | :--- | :--- |
| **Switch evaluated persona for this job** | `1` click on persona row | Right Diagnostic Rail → recalculates all 5 dimensions & Tailoring Opportunities live |
| **Pre-select gap strategies for CV Studio** | `1` click checkbox on strategy card | Left Section 1 → passes selected strategies straight to Studio AI Coach |
| **Launch CV Studio with chosen persona** | `1` click (`[⚡ Tailor CV · 1 cr]` or `[Open Draft]`) | Right Sticky Action Dock |
| **Step to next Radar job without going back** | `1` click `[Next ›]` or `]` key | Top Breadcrumb Bar |
| **Ask quick fit question ("Should I apply?")** | `1` click (`[💬 Ask AI About Fit]`) | Bottom of Right Sticky Dock → opens compact inline Q&A drawer |

---

## 5. Detailed Zone-by-Zone Component & Interaction Spec

### 5.1 Multi-Persona Comparison Matrix (Right Rail)
- Evaluates the job against **every** active persona in `UserProfile.career_personas`.
- Highlights the winner (`★ Best Fit`) and lets the candidate click any alternative persona to preview how skills/title scores shift—eliminating guesswork when candidates straddle roles (e.g., *Data Scientist* vs. *ML Engineer*).

### 5.2 Transparent 5-Dimensional Breakdown (Right Rail)
- Clicking/expanding any of the 5 weighted dimensions shows exact deterministic math:
  1. **Technical Skills Overlap (35%):** Mandatory vs. Nice-to-Have coverage + alias matches (e.g., *"PyTorch satisfies Deep Learning requirement"*).
  2. **Role & Title Alignment (20%):** Semantic proximity to target & alternative titles.
  3. **Experience & Seniority Proximity (20%):** Continuous curve explanation (e.g., *"You have 4 yrs vs. 5 yrs stated -> 84% proximity, no disqualification"*).
  4. **Project & Domain Relevance (15%):** Matched past achievements/projects from Master Profile.
  5. **Location & Work Mode Fit (10%):** City, work mode, and relocation compatibility + auto-paired regional phone indicator (`+20` vs `+966`).

### 5.3 Constructive Tailoring Playbook (Left Section 1)
- Replaces negative rejection badges with toggleable **Strategy Cards** (`[✓ Focus CV Studio on this]`) linking specific job requirements to verified Master Profile achievements. Clicking `[⚡ Tailor CV · 1 cr]` passes checked strategies directly into the AI Studio prompt so tailoring targets what matters most to the user!

### 5.4 Existing Artifacts Protection Card
- Checks `GET /api/v1/cv-fit` and `/cover-letter` for `job_id`: if a tailored CV or cover letter already exists, surfaces `[Open Existing CV Draft (0 cr)]` prominently above `[Re-Tailor New Version · 1 cr]`.

### 5.5 Contextual "Ask AI About Fit" Mini-Drawer
- Lightweight slide-over Q&A scoped strictly to `@Master Profile` + `@This Job Spec` (free fit advice before spending credits; e.g., *"Which 2 projects should I prioritize for Swvl?"*).

---

## 6. Interactivity, Adjustability & Keyboard Shortcuts

- **Resizable Split:** `58% / 42%` default (`min 340px` right rail), double-click resets, persisted in `localStorage`.
- **Keyword Highlight Toggle:** Toggle inside Raw JD to highlight matched vs. missing required keywords directly in context.
- **Keyboard:** `Esc` / `[` returns to `/radar`; `J`/`K` or `[` `]` cycles adjacent jobs from the filtered Radar feed; `T` triggers Tailor CV.

---

## 7. State Matrix & Edge Cases

| State | Behavior |
| :--- | :--- |
| **Job Not Found (`/jobs/99999`)** | Clean recovery card: *"We couldn't find that job record — it may have been removed or expired."* + `[Return to Radar]` + `[Paste Job URL Instead]`. |
| **Sparse / Unparsed Job Description** | *"This posting has limited details (title + link only), so the score relies on title & location fit. [Paste Full JD Text to Re-Score]"* |
| **Standard Board vs. Recruiter Post** | Enforces identical Pipeline Eligibility rule as `/radar` (no pipeline actions on standard LinkedIn/Wuzzuf listings). |

---

## 8. Frontend UI Implementation Contract

- **Suggested Components:** `JobDetailAnalysisPage`, `MultiPersonaScoreMatrix`, `FiveDimensionBreakdownPanel`, `TailoringStrategyPlaybook`, `SkillMatchMatrix`, `ExistingArtifactsCard`, `FitAdvisorMiniDrawer`.
- **State:** `jobDetail: JobItem`, `evaluatedPersonaId`, `selectedStrategyIds: string[]`, `existingDocs: CvFitSummary[]`, `isFitChatOpen`.
- **Backend Hooks:**
  - `GET /api/v1/jobs/{job_id}` (`backend/app/api/routes/jobs.py`)
  - `GET /api/v1/jobs/{job_id}/fit-breakdown?profile_id=...` `[New Endpoint Needed for full 5-D multi-persona JSON]`
  - `GET /api/v1/cv-fit?profile_id=...` (`backend/app/api/routes/cv_fit.py`)
- **UX Acceptance Criteria:**
  1. Zero negative rejection labels anywhere; experience gaps always show continuous proximity + bridging tip.
  2. Clicking another persona recalculates the 5 dimensions and strategy cards instantaneously.
  3. Existing tailored documents for that job clearly unlock `0-credit` direct opening.
