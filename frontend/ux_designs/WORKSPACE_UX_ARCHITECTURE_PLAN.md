# Tailored Workspace UX & Multi-Page Workflow Plan

**Status:** Phases A–D Implemented & Verified End-to-End (Frontend Build + Lint + Backend Pytest `8/8` + Live Chrome `1440×900`, `0` JS errors during flow)  
**Scope:** Core Workspace Triad (`CV Studio` ↔ `Cover Letters` ↔ `Pipeline`), **Option A** (`Interest List` folded into `Job Radar`), and the **Workspace-Aware `Atelier Coach`**  
**Design System:** Atelier V2 (Option C) · Brand Book v1.2 tokens + Semantic Directional Arrows (`▲` Advantage / `▼` Downside Only)

---

## 1. Locked Product Decisions

| Decision Area | Chosen Direction | Why It Matters |
| :--- | :--- | :--- |
| **Cover Letters Identity (`/cover-letters`)** | Redesign into a **Tailored Cover Letters History Rail + Non-Destructive Outreach Envelope Composer + Dedicated `+ New Letter` Big Blank Drop Canvas**. | Existing saved letters stay immutable and clean (zero drop strip sitting over them); clicking **`+ New Letter`** opens a full dashed drop canvas (`Link`, `JD`, `Ctrl+V Screenshot`, `Brief`) that creates a brand-new letter cleanly in History. |
| **CV ↔ Cover Letter Connection** | Keep **two strictly separate standalone pages** (`/studio` and `/cover-letters`) linked via explicit, well-named handoff controls (**`Write Cover Letter`** in CV Studio top bar; **`Choose CV ▾`** + **`Edit in CV Studio`** in Cover Letters attachment tray). | Avoids cramped multi-purpose UI while giving users a 1-click path to pair any CV, inspect it in-place, or jump to edit it in CV Studio when needed. |
| **CV Studio & Saved CVs (`/studio`, `/cvs`)** | Merged standalone `Saved CVs` archive directly into **CV Studio** via a collapsible left **`Saved CVs` Rail** + **`+ New CV` Blank Drop Canvas** (`PDF`, `.tex`, `Job Link`, `Full JD`, `Ctrl+V Screenshot`, or `Saved Role Dropdown`) alongside **Overleaf-style Live `.tex Split`** (`Paper \| Diff \| .tex Split`). | Eliminates jumping between an archive table and the editor; lets users browse, import PDF/`.tex`, fork, delete, tailor new CVs, and live-edit LaTeX in one unified workbench. |
| **Workspace-Aware Agent (`Atelier Coach`)** | Upgraded [CalmAiCoachSidecar.tsx](file:///d:/Tailored/frontend/src/components/common/CalmAiCoachSidecar.tsx) into one continuous **Atelier Coach** across `CV Studio` and `Cover Letters` with **4 structured card types**, stacked context label underneath `Atelier Coach`, and **Full Formatted Sheet Preview Drawer** ([CvPaperPreview.tsx](file:///d:/Tailored/frontend/src/components/studio/CvPaperPreview.tsx)). | Users can ask *"Show my available CVs"*, inspect formatted 1-page CVs in-place, attach/switch them, and read full target context names without truncation. |
| **Interest List Fate (`Option A`)** | **Fold `Interest List` into `Job Radar` (`/radar`)** via top queue tabs + unified Multi-Modal Ingest Bar, and remove `Interest List` from `AtelierSidebar`. | Eliminates redundant 2-page overlap (`/radar` vs `/interest`); clarifies a clean 3-phase funnel: **Discover & Shortlist → Tailor & Compose → Send & Track**. |
| **Pipeline Eligibility (`/pipeline`)** | **Remove the Direct-Email-only rejection gate.** Pipeline tracks *every* committed application (`Direct Email` and `External Portal`), adapting buttons per channel. | Users who apply via LinkedIn/Wuzzuf need the exact same `Applied → Interview → Follow-Up` tracking as direct recruiter email threads. |

---

## 2. Simplified Workspace Information Architecture (`Option A`)

Collapsing `/interest` into `/radar` and merging `Saved CVs` (`/cvs`) into `CV Studio` (`/studio`) tightens the left navigation rail (`AtelierSidebar`) down to **5 distinct, zero-overlap stages**:

```
Before (7 Workspace Routes — Overlapping):
  Radar  ≈  Interest List (duplicate lists + ingest bars)
  CV Studio  ↔  Saved CVs (separate archive table vs editor)
  Cover Letters (disconnected email box)
  Pipeline (rejected non-email jobs back into Interest List)

After (5 Workspace Routes — Single Responsibility):
  1. Dashboard      (/dashboard)      Daily Command Center — top matches, resume draft, overdue actions
  2. Job Radar      (/radar)          Discover, Ingest (URL / JD / Screenshot OCR) & Shortlist (?tab=saved)
  3. CV Studio      (/studio, /cvs)   Saved CVs Left Rail + Blank Drop/Import Canvas + Overleaf .tex Split ──> [Write Cover Letter]
  4. Cover Letters  (/cover-letters)  History Rail + Blank Drop Canvas / Composer ──> [Edit in CV Studio]
  5. Pipeline       (/pipeline)       Track ALL committed applications (Direct Email & Portal)
```

> **Backward Compatibility:** Visiting `/interest` redirects cleanly to `/radar?tab=saved` and visiting `/cvs` renders unified `<CvStudioPage />` directly so bookmarks, notifications, and existing links never 404.

---

## 3. Separate Pages + Explicit Cross-Page Handoffs (`CV Studio` ↔ `Cover Letters`)

Keeping `/studio` and `/cover-letters` as clean, specialized routes keeps load weight focused while explicit handoff buttons eliminate dead ends:

1. **Inside Unified CV Studio (`/studio`):**
   - **Left Collapsible `Saved CVs` Rail (`.t-cl-history-rail`):** Lists every tailored, imported (`.tex` / `.pdf`), forked, or blank draft with Fit%, Dispatched/Import status badges, Undo deletion, and a single **`+ New CV`** action (moves cleanly to the top bar when collapsed; auto-collapses during `.tex Split`).
   - **`+ New CV` Blank Drop Canvas:** Supports dragging/dropping/uploading `.pdf` and `.tex` resumes, pasting job links, full JDs, or screenshots (`TypewriterDropPlaceholder` animating one prompt + icon at a time), `Start Blank LaTeX CV`, and a searchable/clean **`OR START FROM A SAVED ROLE`** custom dropdown.
   - **Centered sliding `Paper | Diff | .tex Split`** segmented switch + Top-bar **`Write Cover Letter`** action persisting `selectedCvByJob`.

2. **Inside Cover Letters (`/cover-letters`):**
   - **Left Collapsible Cover Letters History Rail (`.t-cl-history-rail`):** Displays every saved tailored cover letter, tabular date/recipient metadata, hover delete (`Undo` toast), and a single **`+ New Letter`** CTA (relocating to the top bar only when History is collapsed).
   - **Dedicated Big Blank Drop Canvas (`.t-cl-blank-dropcard` via `+ New Letter`):** Focused clean drop well with animated `TypewriterDropPlaceholder`, `Start Blank Email`, and custom **`SavedRoleDropdown`** — creating a brand-new `CoverLetterItem` cleanly at the top of History.
   - **Always-Editable `To:` & Primary Action = Direct Send (`Send Email + CV` / `Send Email`):** Attachment is completely optional (`×` detaches cleanly; `Listing ↗` stays secondary).
   - **Full Formatted CV Preview Drawer:** Clicking `Preview` opens `AtelierPreviewDrawer` rendering a complete 1-page `<CvPaperPreview>` sheet hydrated from backend `CvFitAPI.getCvFit` with **`Edit in CV Studio`** and **`Use This CV`** actions.

---

## 4. Cover Letters (`/cover-letters`) — Complete Outreach Composer Redesign

### Why today's page felt identical to CV Studio
Today [CoverLetterStudioPage.tsx](file:///d:/Tailored/frontend/src/pages/CoverLetterStudioPage.tsx) renders a **centered printed CV letterhead** (`Name · Title · City · Email · Phone` + dark top border rule) and forces sending through a distant top-right button (`Send in Dispatch`) that opens [DispatchModal.tsx](file:///d:/Tailored/frontend/src/components/studio/DispatchModal.tsx)—repeating the `To`, `Subject`, `Body`, and CV file controls a second time.

### Visual & Functional Separation: Printed CV vs. Outreach Envelope

| Dimension | `CV Studio` (`/studio`) | `Cover Letters` (`/cover-letters`) |
| :--- | :--- | :--- |
| **Visual Metaphor** | **Printed 1-Page ATS Manuscript** | **Outreach Envelope & Package Composer** |
| **Document Header** | Candidate Contact Centerpiece + City + Section Rules | **Channel Mode (`Email Pitch` \| `Portal Letter`)** + `To:` (`recruiter@...`) + `CC me` + `Subject:` |
| **Middle Canvas** | Strict CV blocks (`Summary`, `Skills`, `Experience`, `Projects`, `Education`) | Clean greeting → 2–3 crisp editable paragraphs → sign-off (`84 words · ~20s skim` inline) |
| **CV Pairing** | *Is* the CV document (`Export PDF / .tex`) | **Docked CV Attachment Tray** inside bottom of composer (`Preview` / `Change CV ▾` / `Tailor 1 cr`) |
| **Primary Action Position** | Top-right **`Export PDF`** | **Bottom-right of the Composer Card**, right where the eye finishes reading the letter |
| **Send Flow** | Export PDF/TeX or switch tab to `Cover Letter` to send | **Direct Send / Copy / Open Portal** in-place — **no double-composer `DispatchModal` jump** |

### Anatomy of the Redesigned Cover Letter Composer Card

```
+------------------------------------------------------------------------------+
|  OUTREACH COMPOSER CARD (var(--paper) · 6px 26px 6px 6px · borderless depth) |
|                                                                              |
|  [ Email Pitch | Formal Letter ]                   [Technical ▾] [~180w ▾]   |  ◄ Format + compact Tone inside card OR top bar
|  --------------------------------------------------------------------------  |
|  To        [ sara.mansour@techstart-mena.io               ]   [✓ CC me ]     |  ◄ Replaced with "Portal Mode · Copy & Paste" badge if no email
|  Subject   [ Application: Senior AI Engineer — Ahmed El-Sayed              ] |
|  ==========================================================================  |
|                                                                              |
|  Dear Sara,                                                                  |
|                                                                              |
|  Building low-latency Python and FastAPI inference services aligns directly  |  ◄ Hover shows smooth [Ask AI] [Shorten] [Edit] microbar
|  with TechStart MENA's Senior AI Engineer charter...                         |
|                                                                              |
|  Most recently at Swvl, I architected production ML pipelines cutting p95... |
|                                                                              |
|  Sincerely,                                                                  |
|  Ahmed El-Sayed · +20 100 482 9102               84 words · ~20s skim        |  ◄ Whisper metric anchored at end of prose
|                                                                              |
|  +------------------------------------------------------------------------+  |
|  | ATTACHED CV · Ready to pair                                            |  |
|  | [📄 Ahmed_CV_TechStart_v2.pdf · ▲ 96% Fit]    [Preview]  [Change CV ▾] |  |  ◄ Or CTA: "Base CV attached · [Tailor for TechStart (1 cr) →]"
|  +------------------------------------------------------------------------+  |
|                                                                              |
|  [✓ Mark Applied in Pipeline]      [Copy All]  [✉ Send via Gmail ▾]          |  ◄ Primary CTA right beside eye's resting point!
+------------------------------------------------------------------------------+
```

> **What happens to `DispatchModal`?** `DispatchModal` stays solely as a **quick-dispatch overlay from `Dashboard` and `Pipeline`** (when clicking `Dispatch Now` without opening a studio). Clicking **`Send via Gmail`** inside `/cover-letters` downloads/attaches the chosen CV PDF, copies the pitch, opens Gmail compose with `to`, `subject`, `body`, `cc` pre-filled, freezes the CV + email snapshot, and logs `Applied` in Pipeline automatically.

### Smart CV Attachment Picker (`Change CV ▾`) Behavior
Clicking **`Change CV ▾`** opens a borderless white upward listbox listing:
1. **Best Match for Current Role:** e.g. `StartupX Tailored CV (v2)` · `▲ 98% Fit` *(highlighted)*
2. **Other Saved Tailored CVs:** e.g. `Swvl Lead Data Scientist CV` · `▲ 91% Fit` *(click `[Preview]` inline without changing selection)*
3. **Master Persona Baseline (`0 cr`):** `Data Scientist Base Profile PDF`
4. **Action Footer:** `+ Tailor New CV for {Company} (1 cr)` *(switches cleanly to `CV Sheet` tab)* · or `Send Pitch Only (No CV Attachment)`

---

## 5. Unified Workspace-Aware `Atelier Coach` — UI & UX Blueprint

To fulfill a general-purpose assistant that knows your CVs, Cover Letters, Jobs, Pipeline, and Master Profile **without producing walls of unstructured chat text**, [CalmAiCoachSidecar.tsx](file:///d:/Tailored/frontend/src/components/common/CalmAiCoachSidecar.tsx) adds 3 visual layers on top of its existing detached floating Option C container:

### 5.1 Live Scope Pill, Thread Continuity & `@` Context Menu
- **Header:** `Atelier Coach` (`Fraunces`) + clickable Context Scope Pill (`Focus: StartupX CV ▾`) + toggle (`This Role` vs `All Workspace`).
- **Composer `@` Picker:** Clicking **`@ Context`** (or typing `@`) opens a clean borderless upward menu letting users insert explicit scope tokens:
  - `@Saved CVs` · *"Compare or attach from 6 CVs"*
  - `@Cover Letters` · *"Reference past outreach hooks"*
  - `@Pipeline` · *"Check follow-ups & interview notes"*
  - `@Jobs` · *"Scan Radar & saved roles"*
  - `@Master Profile` · *"Pull unmentioned projects or metrics"*
- **Contextual Starter Prompts:**
  - In `CV Studio`: `Quantify Bullet 1`, `Compare with Saved CVs`, `Audit JD Gaps`
  - In `Cover Letters`: `Sharpen opening`, `Recommend CV to attach`, `Draft 7-day nudge`

### 5.2 Four Structured Interactive Card Types Inside the Chat Stream
Every assistant reply selects the cleanest card UI for the user's intent (using borderless `white` Atelier surfaces, `4px 20px 4px 4px` curvature, soft shadow elevation, and semantic `▲`/`▼` arrows):

#### Card Type 1 — `Proposal Diff Card` *(Existing, Kept)*
- Used for editing a specific CV bullet, summary, or letter paragraph.
- Semantic red `▼` baseline vs green `▲` proposed rewrite + `Locate` + `Apply` / `Skip` / `Refine`.

#### Card Type 2 — `Selectable Resource List Card` *(New)*
- Used whenever the user asks *"Show my available Python CVs"*, *"Which saved CV fits Instabug best?"*, or *"Find high-fit FastAPI jobs"*.
- Displays **2–5 compact scannable rows** directly inside the chat bubble:
  ```
  ┌────────────────────────────────────────────────────────┐
  │ Available Tailored CVs · Ranked for StartupX   3 found │
  │                                                        │
  │  Swvl · Lead Data Scientist           ▲ 94%            │
  │  Updated 2d ago · FastAPI, PyTorch   [Preview] [Use CV]│
  │  ────────────────────────────────────────────────────  │
  │  TechStart · Senior AI Systems        ▲ 91%            │
  │  Updated 4h ago · LLMs, Docker       [Preview] [Use CV]│
  │  ────────────────────────────────────────────────────  │
  │  Master Profile · Data Scientist      ▲ 86%            │
  │  Baseline PDF · 0 cr                 [Preview] [Use CV]│
  └────────────────────────────────────────────────────────┘
  ```
- **Context-Smart Primary Action on Each Row:**
  - On `/cover-letters`: **`Use CV`** attaches that exact PDF to the bottom **CV Attachment Tray** immediately (`▲ Attached Swvl CV` receipt).
  - On `/studio`: **`Load Draft`** / **`Import Bullets`** opens it or pulls verified bullets.
  - On Pipeline/Jobs queries: **`Open Role →`**.

#### Card Type 3 — `Cross-Page Confirm Action Card` *(New)*
- Used when an agent action modifies state outside the current document (e.g., *"Mark StartupX as Applied and draft a 7-day follow-up"*, *"Move Instabug to Interview"*).
- Never mutates Pipeline silently: renders a focused confirmation strip (`Pipeline · StartupX → Applied + Freeze CV`) with **`Confirm`** and **`Cancel`**, collapsing to a `▲ Done — View in Pipeline →` 1-line receipt on confirm.

#### Card Type 4 — `Workspace Audit Card` *(New)*
- Used for workspace-wide checks (*"What follow-ups are overdue?"*, *"What Master Profile projects prove Kafka?"*).
- Shows 1-line scannable findings marked cleanly with `▲` green advantages/matches or `▼` red gaps/overdue alerts plus 1-click **`Insert Metric`** or **`Open Follow-Up`**.

### 5.3 In-Place Left-Pane Slide-Over Preview Drawer (Zero Page Jumps)
When the user clicks **`Preview`** on **any resource card inside `Atelier Coach`** (or on the **CV Attachment Tray** in Cover Letters):
- A crisp **`white` Slide-Over Sheet Preview** opens neatly over the **left workbench pane** (`z-index: 20`) while the **`Atelier Coach` remains open and interactive on the right**.
- Top strip of the Preview Overlay has only 3 calm controls: **`Document Name + ▲ Fit %`**, primary contextual CTA (**`Attach to Cover Letter`** / **`Open in Full Studio →`**), and **`× Close Preview`** (`Esc`).
- Result: Users can ask *"Show my CVs"*, preview 2 candidates side-by-side with the AI Coach, pick the winner, and return straight to editing in zero page reloads.

---

## 6. Pipeline CRM (`/pipeline`) & `Interest List` Consolidation (`Option A`)

### 6.1 Folding `Interest List` (`/interest`) into `Job Radar` (`/radar`)
Retiring the standalone `Interest List` page keeps discovery, ingestion, and shortlisting in **one unified `/radar` hub**:
1. **Top Multi-Modal Ingest Bar inside `/radar`:** Supports pasting any URL, raw JD text, recruiter post with email, or `Ctrl+V` screenshot capture (`0 cr` free fit scoring, instant duplicate detection).
2. **Clean Segmented Tabs at top of `/radar`:**
   - **`All Matches`** (ranked market feed + ingested items)
   - **`Saved Shortlist (N)`** (replaces old `/interest` page—bookmark icon toggle adds/removes cleanly with Undo toast)
   - **`Direct Email`** (filter specifically for recruiter posts with verified direct email)
3. **Batch Selection Bar & Direct Promotion:** Selecting rows in `Saved Shortlist` lets users **`Tailor Selected`**, **`Add to Pipeline`**, or **`Remove`**.

### 6.2 Upgrading `Pipeline` (`/pipeline`) to Unified Application CRM
- **All Channels Supported (`Direct Email` + `External Portal`):**
  - Remove `isEligibleForPipeline` blocking in [WorkspaceContext.tsx](file:///d:/Tailored/frontend/src/context/WorkspaceContext.tsx) & [PipelinePage.tsx](file:///d:/Tailored/frontend/src/pages/PipelinePage.tsx).
  - Portal roles (LinkedIn, Wuzzuf, Careers pages) display a clean muted tag **`External Portal`** and link **`Open Listing ↗`** + **`Mark Applied`**. Direct recruiter threads display **`Direct Email`** + **`Recruiter @`** + **`Send Pitch` / `Follow-Up`**.
- **Connected Dossier Actions (Core Triad Link):**
  - Selecting any application in Pipeline shows its **Application Package Card** (`Attached CV snapshot v2`, `Cover Letter / Sent Email`, `Recruiter Email / Portal URL`, `Follow-Up Timer`).
  - **`Draft / Send 7-Day Follow-Up`** opens `/cover-letters?job_id=...&mode=followup` pre-loaded with the frozen submission context so the Coach drafts a concise context-aware nudge referencing the exact CV originally sent.

---

## 7. Multi-Page User Journeys Across the Core Triad

### Journey A — CV-Only *(FastATS Tailoring)*
1. On `Dashboard` or `Job Radar`, click **`Tailor · 1 cr`** → opens `/studio` (`CV Sheet`).
2. Edit bullets via inline hover or `Atelier Coach`, click **`Export PDF`**, optionally check **`Mark Applied → Add to Pipeline`** inside export menu. Done (`0` cover letter friction).

### Journey B — Cover-Letter-Only / Recruiter Email Post Fast-Track
1. Paste `"Urgent Senior AI Engineer · send CV to sara@techstart.io"` in Dashboard/Radar ingest bar → click **`Draft Outreach`** (or open `/cover-letters`).
2. `Atelier Coach` drafts a sharp `Email Pitch` citing `TechStart` goals; `To:` auto-fills `sara@techstart.io`.
3. User isn't sure which CV to attach → asks Coach: **`"Show my best CVs for AI systems"`** → Coach returns a **`Selectable Resource List Card`** (`Swvl CV ▲ 94%`, `TechStart Base ▲ 88%`).
4. User clicks **`Preview`** on `Swvl CV` (reads it in-place on left pane), clicks **`Use CV`** → Attachment Tray updates immediately.
5. User clicks **`Send via Gmail`** at the bottom-right of the card (with **`Mark Applied`** checked) → pitch opens in Gmail, PDF downloads, and `Pipeline` logs the frozen package in `Applied`. **Zero page jumps.**

### Journey C — Full Package (`CV Studio` → `Cover Letters` → `Pipeline`)
1. Open `StartupX` in `/studio`, tailor bullets or live-edit LaTeX in `.tex Split` (`v2`, Fit rises `92% → 98%`).
2. Click **`Write Cover Letter`** in the CV Studio top bar to carry the edited CV straight over to `/cover-letters`.
3. Compose or tweak via the Outreach Envelope Composer (or drop a new custom role into `.t-tailor-dropmat` above it), confirm recipient `To:` + optional CV (`Choose CV ▾`, `Preview`, or `Edit in CV Studio`), and click **`Send Email + CV`** at bottom right -> logged cleanly in `Pipeline`.

### Journey D — 7-Day Follow-Up & Interview Loop
1. `Dashboard` (`Needs Your Action` → `▼ Follow-up due`) or `Pipeline` highlights `Instabug` (`7d elapsed`).
2. Click **`Draft Follow-Up`** → opens Pipeline Dossier or transitions to `/cover-letters?mode=followup` showing the frozen CV + previous email context.
3. Send polite 3-sentence nudge → Pipeline stage advances smoothly (`Applied → Follow-up Sent → Interview`).

---

## 8. Phased Implementation Roadmap (UI First)

| Phase | Deliverables | Key Files Touched |
| :--- | :--- | :--- |
| **Phase A — Outreach Cover Letter Redesign + Overleaf `.tex Split` + Explicit Cross-Page Handoffs** | Separate `/studio` and `/cover-letters` routes connected cleanly via **`Write Cover Letter`** (CV Studio) and **`Choose CV ▾`** + **`Edit in CV Studio`** (Cover Letters). Added Tailored Target Drop Mat (`.t-tailor-dropmat` for link / JD / `Ctrl+V` screenshot / brief), always-editable `To:` + **`Send Email + CV`** primary CTA, and Overleaf-style side-by-side editable `.tex Split` + live CV preview + `Diff` line audit. | [CoverLetterStudioPage.tsx](file:///d:/Tailored/frontend/src/pages/CoverLetterStudioPage.tsx), [CvStudioPage.tsx](file:///d:/Tailored/frontend/src/pages/CvStudioPage.tsx), [latexLiveSync.ts](file:///d:/Tailored/frontend/src/utils/latexLiveSync.ts), [coverLetterTargetParser.ts](file:///d:/Tailored/frontend/src/utils/coverLetterTargetParser.ts), [app.css](file:///d:/Tailored/frontend/src/styles/app.css) |
| **Phase B — Workspace-Aware `Atelier Coach` Cards & `@` Picker** | Extend [CalmAiCoachSidecar.tsx](file:///d:/Tailored/frontend/src/components/common/CalmAiCoachSidecar.tsx) props/renderers for **Selectable Resource List Cards** (`Preview` / `Use CV` / `Open`), **Cross-Page Confirm Cards**, **Workspace Audit Cards**, unified `@ Context` composer menu, and **In-Place Slide-Over Preview**. Wire UI queries across CVs, Letters, Jobs, Pipeline, and Profile from `WorkspaceContext`. | [CalmAiCoachSidecar.tsx](file:///d:/Tailored/frontend/src/components/common/CalmAiCoachSidecar.tsx), [WorkspaceContext.tsx](file:///d:/Tailored/frontend/src/context/WorkspaceContext.tsx) |
| **Phase C — Option A Consolidation (`Interest List` → `Job Radar`)** | Add top Multi-Modal Capture Bar + `All Matches \| Saved Shortlist \| Direct Email` segmented tabs to [RadarPage.tsx](file:///d:/Tailored/frontend/src/pages/RadarPage.tsx) + Atelier V2 refresh; remove `Interest List` item from [AtelierSidebar.tsx](file:///d:/Tailored/frontend/src/components/shell/AtelierSidebar.tsx); redirect `/interest` → `/radar?tab=saved`. | [RadarPage.tsx](file:///d:/Tailored/frontend/src/pages/RadarPage.tsx), [AtelierSidebar.tsx](file:///d:/Tailored/frontend/src/components/shell/AtelierSidebar.tsx), [App.tsx](file:///d:/Tailored/frontend/src/App.tsx) |
| **Phase D — Unified `Pipeline` CRM (`Direct Email` + `Portal`) Atelier V2 Overhaul** | Remove the Direct-Email-only gate so Pipeline accepts & tracks all applied jobs (`External Portal` & `Direct Email` channels), upgrade `/pipeline` UI to Atelier V2 (`Focus Split \| Board \| Table` with zero OS `<select>` or wireframe cages), connect `Attached CV snapshot` & `Draft Follow-Up` cleanly to `/cover-letters`. | [PipelinePage.tsx](file:///d:/Tailored/frontend/src/pages/PipelinePage.tsx), [WorkspaceContext.tsx](file:///d:/Tailored/frontend/src/context/WorkspaceContext.tsx), [ApplicationDetailPage.tsx](file:///d:/Tailored/frontend/src/pages/ApplicationDetailPage.tsx) |

---

### Definition of Done for Each Phase
1. `npm run build` (`tsc -b && vite build`) and `npm run lint` (`oxlint`) exit `0` with zero new warnings or errors.
2. Strict Brand Book v1.2 tokens (no CSS gradients, no raw hex literals, no native `<select>`, no emojis, green `▲` vs red `▼` semantic arrows strictly).
3. Verified live in Chrome (`1440×900`, `0` console errors, `0` failed requests) across standalone CV Overleaf `.tex Split` + Diff audit, Cover Letters Drop Mat + optional CV direct email send, Coach Card `Preview`/`Attach`, Radar `Saved Shortlist`, and Pipeline channel flows.
