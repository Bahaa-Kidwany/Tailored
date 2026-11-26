# 01 — Command Center Landing (`/`)

**Route:** `/`  
**Implementation Status:** Implemented (`LandingPage.tsx`) — **Redesigned Away from Auto-Rotating Carousel Anti-Pattern to Interactive Product Proof Sandbox (`Linear` / `Cursor` / `Perplexity`)**  
**Primary User Goal:** Grasp Tailored's value immediately, execute an instant action inside one Universal Omni-Bar (search roles, paste a job URL/JD, or upload a CV), and test interactive live product previews without dizzying motion or banner blindness.  
**Entry Points:** Direct domain visit, Brand Mark from any route, optional Sign Out destination.  
**Exit Destinations:** `/explore` (guest search), `/radar` (authenticated search), `/register` (via preserved `pendingIntent`), `/login`, `/dashboard` (signed-in CTA).  
**Credit Model Impact:** 100% Free to interact; communicates *"Start with 2 Free Credits (1 full tailored application) — pay per pack from 49 EGP, zero monthly lock-in."*

---

## 1. UX Reference Benchmarks & Ergonomic Rationale

| Reference | Pattern Adopted | Why It Replaces the Legacy Carousel |
| :--- | :--- | :--- |
| **Perplexity & Raycast** | Centered **Universal 4-Mode Omni-Bar** as primary hero anchor | Single zero-tab entry point that auto-detects role search, AI query, pasted URL/JD, or dropped resume file. |
| **Linear & Cursor** | **Interactive Clickable Product Proof Sandbox** directly beneath hero | Baymard Institute research shows auto-rotating carousels fail due to banner blindness and lost control; interactive UI sandboxes achieve 43–60% engagement and build immediate technical trust. |
| **FlowCV** | Calm, honest Pay-As-You-Go value framing above and below the fold | Reassures skeptical job seekers that they won't spend 20 minutes building a CV only to hit a surprise subscription trap. |

---

## 2. Desktop Layout Architecture & ASCII Wireframe (`1440px`)

```
+---------------------------------------------------------------------------------------------------+
| QUIET TOP NAVIGATION BAR (Height: 60px, Sticky)                                                   |
| [Tailored Mark]        [Explore Live Jobs]   [How It Works]   [Credit Packs]   [Sign In] [Get Started] |
+---------------------------------------------------------------------------------------------------+
| ABOVE-THE-FOLD HERO ANCHOR (Centered Single Axis, max-width: 960px)                               |
|                                                                                                   |
|                          "Invisible Discovery. Absolute Caliber."                                 |
|        Discover MENA & global jobs, score your honest 5-D fit, tailor CVs line by line.           |
|                                                                                                   |
|   +-------------------------------------------------------------------------------------------+   |
|   | UNIVERSAL 4-MODE OMNI-BAR (Height: 64px, Drag-and-Drop File Enabled)                      |   |
|   | [📎 Drop/Upload CV] | Search roles, paste a LinkedIn/Wuzzuf URL, or drop a JD... [Go ↵]   |   |
|   +-------------------------------------------------------------------------------------------+   |
|   | Live Mode: [🔍 Search Roles]  |  Try: "AI Engineer Cairo" · "Paste LinkedIn URL" · ".tex CV"  |   |
|                                                                                                   |
|   +-------------------------------------------------------------------------------------------+   |
|   | CLICKABLE 3-TAB INTERACTIVE PRODUCT PROOF SANDBOX (Static Until Clicked — Zero Auto-Spin) |   |
|   |                                                                                           |   |
|   |  Tabs: [● 01. Calm CV Studio + AI Diff]  [ 02. 5-D Fit Scoring ]  [ 03. Multi-Source Radar]|   |
|   |-------------------------------------------------------------------------------------------|   |
|   |  AUTHENTIC MINI-WORKBENCH PREVIEW (Users Can Click & Test Directly on Landing!)           |   |
|   |                                                                                           |   |
|   |  LIVE PAPER PREVIEW (Left)           | BORDERLESS AI COACH (Right)                        |   |
|   |  Swvl · Lead Data Scientist          | ▸ Checked Swvl role in Profile ✓                   |   |
|   |  • Dynamic Route Pricing:            | "Tightened Bullet 2 for FastAPI latency:"          |   |
|   |    Architected FastAPI & PyTorch     | - Built Python routing APIs                        |   |
|   |    pricing endpoints (-42% latency)  | + Architected FastAPI endpoints (-42% latency)     |   |
|   |    ◦ Stack: Python, FastAPI, PyTorch | [Try Clicking: ✓ Apply]   [Try Clicking: Refine]   |   |
|   +-------------------------------------------------------------------------------------------+   |
+---------------------------------------------------------------------------------------------------+
| BELOW THE FOLD (Centered, max-width: 960px)                                                       |
|   1. Honest Pay-As-You-Go Strip: "2 Free Credits on signup · Discovery & Fit Free · Packs 49 EGP" |
|   2. Zero-Hallucination & Privacy Pledge: "Never sells your data to recruiters." [Privacy] [Terms]|
+---------------------------------------------------------------------------------------------------+
```

---

## 3. Eye-Scan Path & Anti-Saccade Map

1. **Fixation 1 (Center Headline + Omni-Bar):** Crisp centered vertical axis directly inside the first screen—zero distracting side banners or moving cards pulling peripheral attention.
2. **Fixation 2 (Mode Pill + Starter Chips Directly Under Bar):** Instantly confirms auto-detected input type or offers 1-click query starters.
3. **Fixation 3 (Clickable 3-Tab Interactive Sandbox):** User actively chooses which pillar to inspect and clicks interactive controls (`Apply` diff, switch persona score, filter source) at their own pace without a timer sliding cards away mid-read.

---

## 4. Proximity & Click-Depth Budget

| User Intent | Click / Keystroke Depth | Spatial Location |
| :--- | :--- | :--- |
| **Search roles on public radar** | Type + `Enter` (`1` action) | Universal Omni-Bar → `/explore?q=...` (or `/radar`) |
| **Paste LinkedIn/Wuzzuf URL or JD** | `Ctrl+V` + `Enter` (`1` action) | Universal Omni-Bar → preserves `pendingIntent` |
| **Upload existing `.tex`/`.pdf`/`.docx` CV** | Drag onto bar OR click `[📎 Upload CV]` (`1` action) | Left inside Omni-Bar → fast-tracks Onboarding |
| **Test how CV Studio or Fit Scoring works** | `1` click inside Sandbox Tabs / `[Apply]` simulation | Interactive Proof Sandbox right below Omni-Bar |
| **Browse live jobs without typing** | `1` click (`[Explore Live Jobs]`) | Quiet Top Nav |

---

## 5. Detailed Zone-by-Zone Component & Interaction Spec

### 5.1 Universal 4-Mode Omni-Bar
- **Auto-Detection Grammar:** URL (`https://...`) → `Ingest & Score Link`; Long text (`>120 chars` or multi-line) → `Extract Job Description`; Natural query (`find...`) → `AI Career Query`; Short keywords → `Role Search`; File drop → `Parse CV` (`.pdf`/`.tex`/`.docx`) or `Vision Screenshot` (`.png`/`.jpg`).
- **Comfort Rule:** Placeholder hints remain steady once hovered or focused—zero distracting animation jitter while user types.

### 5.2 The 3 Interactive Proof Tabs (Zero Auto-Rotation)
1. **Tab 01 — Calm CV Studio + AI Coach (Default Open):** Lets visitor actually click `[✓ Apply]` on a live sample Swvl bullet diff and watch the CV paper update + card collapse into `✓ Applied [Undo]`.
2. **Tab 02 — Explainable 5-D Fit Engine:** Lets visitor toggle between two personas (`Senior AI Engineer: 94%` vs `Data Analyst: 78%`) and see constructive *Tailoring Opportunities* adapt live (zero knockout rejection).
3. **Tab 03 — Multi-Source Stealth Radar:** Interactive sample LinkedIn + Wuzzuf + Recruiter Post feed showing SHA-256 deduplication and direct-email detection.
- Includes a single calm CTA inside the sandbox footer: `[Try This With Your Own CV (2 Free Credits) →]`.

---

## 6. Interactivity, Adjustability & Keyboard Shortcuts

| Shortcut / Control | Behavior |
| :--- | :--- |
| `/` | Focuses Universal Omni-Bar immediately. |
| `Enter` | Executes detected Omni-Bar workflow. |
| `1` / `2` / `3` (when Sandbox focused) | Switches interactive proof tabs smoothly. |

---

## 7. State Matrix & Edge Cases

| State | Behavior |
| :--- | :--- |
| **Processing Omni-Bar Submission** | Button shows inline progress (*"Extracting Swvl requirements..."* / *"Reading CV..."*) while preserving visible input. |
| **Private/Blocked URL Paste** | Calm inline fallback right inside bar: *"We couldn't reach that private link directly — paste the description text here instead."* |
| **Authenticated Returning User** | Top bar swaps auth buttons cleanly for `[Open Dashboard →]`; Omni-Bar searches jump straight into `/radar` or `/interest`. |

---

## 8. Frontend UI Implementation Contract

- **Suggested Components:** `LandingPage`, `LandingQuietHeader`, `UniversalOmniBar`, `InteractiveProofSandbox` (3 sub-sandboxes: `StudioProofPreview`, `FitEngineProofPreview`, `RadarProofPreview`), `CreditFairnessStrip`.
- **State:** `commandInput`, `detectedMode`, `activeProofTab: 1 | 2 | 3`, `sandboxInteractiveState`, `isProcessing`, `pendingIntent`.
- **Backend Hooks:**
  - `POST /api/v1/jobs/ingest-url` & `POST /api/v1/jobs/extract-description` (`backend/app/api/routes/jobs.py`)
  - `POST /api/v1/profiles/parse-latex` (`backend/app/api/routes/profiles.py`)
  - `POST /api/v1/profiles/upload-resume` `[New Endpoint Needed for PDF/DOCX]`
- **UX Acceptance Criteria:**
  1. Zero auto-rotating carousel or moving slides; visitor controls all tabs manually.
  2. Interactive sandbox lets visitors test real product mechanics (`Apply` diff, switch persona) in `1` click before signing up.
  3. Unauthenticated Omni-Bar actions preserve `pendingIntent` seamlessly across `/register` → `/onboarding` → `/trial`.
