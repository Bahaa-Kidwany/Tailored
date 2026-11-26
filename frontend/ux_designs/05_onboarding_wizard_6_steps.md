# 05 — Calm Single-Focus 6-Step Onboarding Wizard (`/onboarding`)

**Route:** `/onboarding`  
**Implementation Status:** Partially Implemented (`AtelierOnboardingWizard.tsx` currently lacks Step 4 Work Experience and forces multi-column density)  
**Primary User Goal:** Capture the candidate's verified Master Profile cleanly—either in **30 seconds via CV Drop Fast-Track** or step-by-step via **calm single-column progressive profiling** (one clear decision per screen, zero competing sidebars).  
**Entry Points:** Post-registration / post-verification flow, Landing Omni-Bar CV upload, Global Sidebar `Guided Setup (1–6)`.  
**Exit Destinations:** `/trial` (2 Free Credits Welcome & Fulfillment Router), `/dashboard` (`Save & Exit` early escape).  
**Credit Model Impact:** 100% Free; completion unlocks **2 Free Credits** (`1` Full Application Package).

---

## 1. UX Reference Benchmarks & Ergonomic Rationale

| Reference | Pattern Adopted | Why It Replaces 2-Column Clutter |
| :--- | :--- | :--- |
| **Otta / Welcome to the Jungle** | Single-column centered flow (`max-w: 620px`) + progressive profiling + instant transition to live value | Eliminates eye ping-pong between a wide form and a permanent right preview rail. |
| **Linear & Notion Calm Setup** | One intent per screen, minimal visual noise, frictionless skip/exit paths, optional `[Preview ATS Header]` popover | Keeps user attention strictly on the current question without toolbox fatigue. |
| **Rezi / LinkedIn Smart Import** | **2-Track Fast-Forward:** Dropping a `.pdf`/`.tex`/`.docx` CV opens a single calm **Parsed Profile Verification Card** instead of marching blindly through 6 redundant empty forms | Converts a 5-minute manual setup into a 30-second verify-and-confirm experience. |

---

## 2. Desktop Layout Architecture & ASCII Wireframe (`1440px`)

```
+---------------------------------------------------------------------------------------------------+
| CALM ONBOARDING HEADER (Height: 56px, Sticky)                                                     |
| [Tailored]          Step 1 of 6 · Career Track & CV Import             [Auto-saved]  [Save & Exit]|
+---------------------------------------------------------------------------------------------------+
| SLIM CLICKABLE STEP BAR (Centered, max-width: 620px)                                              |
| [1. Track ✓] ── [2. Identity] ── [3. Skills] ── [4. Experience] ── [5. Projects] ── [6. Review]   |
+---------------------------------------------------------------------------------------------------+
| SINGLE-COLUMN CALM STAGE (Centered, max-width: 620px, Generous Outer Whitespace)                  |
|                                                                                                   |
|   (Track A — Step 1 Before CV Upload)                                                             |
|   +-------------------------------------------------------------------------------------------+   |
|   | ⚡ FAST-TRACK IN 30 SECONDS: DROP YOUR EXISTING CV                                        |   |
|   | Drag .pdf, .tex, or .docx here  [Browse File]                                             |   |
|   | Auto-fills roles, skills & education so you skip manual typing.                           |   |
|   +-------------------------------------------------------------------------------------------+   |
|                                                                                                   |
|   ------------------ or enter your career track manually ------------------                       |
|                                                                                                   |
|   1. What primary role are you targeting? *                                                       |
|      [ Senior Machine Learning Engineer                                                     ]     |
|      Quick picks: [AI Engineer]  [Data Scientist]  [Backend Systems]                              |
|                                                                                                   |
|   2. Seniority & Years of Experience *                                                            |
|      [Junior]  [Mid-Level]  [● Senior]  [Lead / Principal]     Experience: [ 7 years ▾ ]          |
|                                                                                                   |
|   3. Executive Summary / Bio *                                            [✨ AI Polish Draft]    |
|      +---------------------------------------------------------------------------------------+    |
|      | Lead ML Practitioner with 7+ years designing distributed deep learning pipelines...   |    |
|      +---------------------------------------------------------------------------------------+    |
|                                                                                                   |
|   (Optional On-Demand Inspection — Zero Permanent Side Rail Clutter!)                             |
|   [👁 Preview How This Looks on ATS Header]                                                       |
|                                                                                                   |
|---------------------------------------------------------------------------------------------------|
| CLEAN SINGLE-LINE FOOTER (Inside max-width: 620px)                                                |
| [← Back]                                           [Skip Step]   [Continue to Identity & Phones →]|
+---------------------------------------------------------------------------------------------------+

--- VARIANT B: FAST-TRACK VERIFICATION SCREEN (Shown Immediately After Dropping a CV!) -------------
|   ✓ Extracted from Mostafa_CV.tex (92% Complete — Review & Confirm)                               |
|   • Track:      Senior AI Engineer · 7 yrs                            [Edit Step 1]               |
|   • Identity:   Mostafa Ibrahim · Cairo, EG · +20 100...              [Add +966 KSA / Edit Step 2]|
|   • Skills:     14 categorized skills (Python, PyTorch, FastAPI...)   [Edit Step 3]               |
|   • Experience: 3 roles, 9 quantified bullets                         [Edit Step 4]               |
|   • Education:  B.Sc. Computer Science, Cairo University (2019)       [Edit Step 6]               |
|                                                                                                   |
|   [✓ Looks Great — Save & Claim 2 Free Credits →]      [Walk Through Steps 2–6 One by One]        |
+---------------------------------------------------------------------------------------------------+
```

---

## 3. Eye-Scan Path & Anti-Saccade Map

1. **Fixation 1 (Slim Top Progress Line):** Tells candidate exactly where they are (`Step 1 of 6`) without multi-column visual distraction.
2. **Fixation 2 (Centered Single-Column Axis `620px`):** Eyes travel straight down a calm vertical path—never ping-ponging to a permanently open right-hand CV preview column.
3. **Fixation 3 (Single Primary Footer Action):** Directly below the last field sits `[Continue →]`.
- **Anti-Saccade Rule:** `[👁 Preview ATS Header]` opens an on-demand popover only if clicked; once inspected, it vanishes back into pure whitespace.

---

## 4. Proximity & Click-Depth Budget

| User Intent | Click / Keystroke Depth | Spatial Location |
| :--- | :--- | :--- |
| **Complete onboarding via existing CV** | `1` drag/drop + `1` click `[Looks Great — Save & Claim 2 Free Credits →]` | Fast-Track CV Drop → Verification Card |
| **Add regional Gulf/MENA phone (`+966`, `+971`)** | `1` click (`[Add +966 KSA]` or Step 2 `[+ Add Number]`) | Inline directly on Verification Card or Step 2 |
| **Walk step-by-step manually** | `1` click `[Continue →]` per single-focus step | Bottom footer aligned to `620px` column |
| **Jump back to fix an earlier step** | `1` click on completed step number | Slim top stepper |
| **Skip optional Projects or Certifications** | `1` click (`[Skip Step]`) | Footer next to Continue |

---

## 5. Step-by-Step Field Scope (All 6 Steps Clean & Complete)

1. **Step 1 — Track, Goal & CV Fast-Forward:** Drop `.pdf`/`.tex`/`.docx` (triggers Fast-Track Verification Card) OR enter Primary Target Title, Alternative Titles, Seniority/Years, and Executive Summary (`[✨ AI Polish Draft]`). Also offers subtle `[Load Demo Profile]` link for instant testing.
2. **Step 2 — Identity, Regional Phones & Mobility:** Full Name, Email, Dynamic Regional Contacts (`+20 EG`, `+966 KSA`, `+971 UAE` with Primary indicator), Clean LinkedIn/GitHub/Portfolio URLs (auto-strips protocol), Current City/Country, Relocation toggle, and Target Locations with per-city `Remote / Hybrid / On-site` chips.
3. **Step 3 — Categorized Skills Taxonomy:** Core Competencies (min 3), Languages, Frameworks, Cloud & Tools + 1-click suggested chips tailored to Step 1 role + drag-to-reorder priority.
4. **Step 4 — Work Experience & Measurable Achievements *(Restored Critical Step)*:** Chronological expandable role cards (Company, Title, Location, Dates / Present toggle), multi-bullet editor with inline coaching hint (`Action verb + context + metric`) and `[+ Role Summary]` / `[+ Stack: ...]` helper pills.
5. **Step 5 — Featured Projects *(Optional)*:** Project name, Repo/Demo URL, tech stack tags, 1–2 impact bullets, prominent `[Skip Projects]`.
6. **Step 6 — Education, Languages, Certifications & Final Review:** Degrees (+ optional GPA/Graduation Project), Spoken Languages + proficiency, Certifications, Custom Sections, and Readiness Summary (`[Save Master Profile & Claim 2 Free Credits →]`).

---

## 6. Interactivity, Adjustability & Keyboard Shortcuts

- **Continuous Draft Auto-Save:** Every field blur writes to local draft storage and backend profile draft automatically.
- **On-Demand Preview Popover:** `[👁 Preview ATS Header]` lets users inspect header formatting without cluttering the screen permanently.
- **Keyboard:** `Alt + ArrowRight` / `Alt + ArrowLeft` steps forward/back; `Enter` inside tag inputs appends tag without accidental form submission.

---

## 7. State Matrix & Edge Cases

| State | Behavior |
| :--- | :--- |
| **CV Fast-Track Partial Parse** | Highlights only incomplete areas gently inside the Verification Card (*"We extracted 3 roles & 14 skills — please confirm your Target Location before continuing"*). |
| **Resuming Interrupted Setup** | Returning user sees: *"Continue from Step 4 (Work Experience) or [Start Fresh]."* |
| **Missing Required Field on Continue** | Scrolls cleanly to field with honest inline helper text beneath it. |

---

## 8. Frontend UI Implementation Contract

- **Suggested Components:** `CalmOnboardingPage`, `OnboardingStepperLine`, `CvDropFastTrackCard`, `ParsedVerificationSummary`, `Step1..Step6` single-column components, `AtsHeaderPreviewPopover`.
- **State:** `currentStep (1..6)`, `fastTrackSummaryVisible: boolean`, `profileDraft: UserProfilePayload`, `parseTelemetry`, `isDirty`.
- **Backend Hooks:**
  - `POST /api/v1/profiles`, `PUT /api/v1/profiles/{id}`, `POST /api/v1/profiles/parse-latex` (`backend/app/api/routes/profiles.py`)
  - `POST /api/v1/profiles/upload-resume` `[New Endpoint Needed for PDF/DOCX]`
- **UX Acceptance Criteria:**
  1. Single-column `620px` calm focus with zero permanent competing side preview column.
  2. Dropping a valid CV offers a 2-click Fast-Track Verification completion path rather than forcing 6 tedious empty screens.
  3. All 6 steps—including Step 4 Work Experience—support full clean manual entry and editing.
