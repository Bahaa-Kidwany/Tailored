# 13 — Dedicated Cover Letter Studio (`/cover-letters`)

**Route:** `/cover-letters` (supports `?job_id=...&doc_id=...`)  
**Implementation Status:** **Never Implemented** (Backend `POST/GET /api/v1/cover-letter` exists in `cover_letter.py`, no dedicated studio UI exists yet)  
**Primary User Goal:** Draft and refine a crisp, human-sounding, sub-250-word cover letter grounded in real CV achievements in a serene, distraction-free writing sanctuary—sharing exact ergonomics with CV Studio.  
**Entry Points:** Global Sidebar (`G` then `L`), CV Studio (`[Draft Companion Cover Letter]`), Interest List, Job Detail (`/jobs/:id`), Pipeline.  
**Exit Destinations:** Exact previous route (`← Back`), `DispatchApplicationModal` (pre-loaded with letter + paired CV), `/studio`.  
**Credit Model Impact:** Generating a brand-new cover letter for a target job costs **`1 Credit`** (`[Generate Cover Letter · 1 cr]`); opening existing drafts and all AI Coach rewrites/tone adjustments cost **`0` additional credits**.

---

## 1. UX Reference Benchmarks & Ergonomic Rationale

| Reference | Pattern Adopted | How It Eliminates Busyness |
| :--- | :--- | :--- |
| **Lex.page & ChatGPT Canvas** | Centered distraction-free prose sheet (`65ch` comfortable reading width) + paragraph-level micro-toolbar + borderless AI Coach (`62% / 38%`) | Strips away all permanent left control rails so writing feels like quiet editorial drafting, not configuring an enterprise dashboard. |
| **Tailored CV Studio Parity** | Identical `48px` Top Bar, Pairing Breadcrumb, `[Brief & Tone ⚙]` popover, and **exact AI Chat Shape** (`00` §5) | Zero new cognitive friction when moving between CV tailoring and Cover Letter writing. |

---

## 2. Desktop Layout Architecture & ASCII Wireframe (`1440px`)

```
+---------------------------------------------------------------------------------------------------+
| 1. ULTRA-QUIET SINGLE TOP BAR (Height: 48px, Sticky — Strictly 4 Clusters, Cross-Site Rail Hidden)|
|                                                                                                   |
| [← Back]   Mostafa (+20)  ×  Swvl · Lead DS ▾     |   [Clean Letter | Keywords]    [‹ v2 ›]       |
|                                                   |   [Brief & Tone ⚙]  [Send in Dispatch ▾]      |
+---------------------------------------------------------------------------------------------------+
| 2. CALM 2-PANE SANCTUARY (100vh - 48px · Single 8px Splitter · Double-Click Reset · `⇄` Swappable)|
|                                                                                                   |
| PRIMARY PANE (62%, min 520px): PROSE CANVAS       | COLLABORATIVE PANE (38%, ~500px, `]` collapses)|
|                                                   |-----------------------------------------------|
|   (Optimal 65ch reading column centered in desk)  | Writing Coach · Grounded: Tailored CV + Swvl ✓|
|                                                   |                          [⇄] [History ▾] [✕] |
|   Subject: Application: Lead Data Scientist —     |-----------------------------------------------|
|            Mostafa Ibrahim                        |                                  +----------+ |
|                                                   |                                  | Cut AI   | |
|   Dear Swvl Hiring Team,                          |                                  | clichés  | |
|                                                   |                                  | in ¶2    | |
|   [¶1 — Direct Hook]                              |                                  +----------+ |
|   Having architected real-time route optimization | ▸ Checked Swvl Tailored CV · 2 metrics (1.1s) |
|   services for high-volume mobility fleets...     |                                               |
|                                                   | Removed the generic opener and anchored ¶2    |
|   [¶2 — Quantified Proof]  <----------------------+ directly in your 42% FastAPI latency win:     |
|     (Hover: [Ask AI] [Sharpen] [Shorten])         |                                               |
|   In my recent work, I led PyTorch and FastAPI... | +-------------------------------------------+ |
|                                                   | | Paragraph #2                     [Locate ↗]| |
|   [¶3 — Calm Close]                               | | - I am excited to leverage my skills...   | |
|   I would welcome a conversation on how...        | | + Across 1,400 Cairo routes, I cut pricing| |
|                                                   | |   endpoint latency by 42% using FastAPI.  | |
|   Sincerely,                                      | | [✓ Apply ↵]  [Skip Esc]  [Refine... R]    | |
|   Mostafa Ibrahim · +20 100 482 9102              | +-------------------------------------------+ |
|                                                   |                                               |
|                                                   | ✓ Applied to Paragraph #1              [Undo] |
|                                                   |                                               |
|                                                   | +-------------------------------------------+ |
|                                                   | | ↳ Focused: Paragraph #2               [×] | |
| Quiet Corner Whisper (Bottom-Left):               | |-------------------------------------------| |
| 214 words · ~45s recruiter skim · 4/5 JD keywords | | Ask to adjust tone, shorten, or @¶...     | |
|                                                   | | [@] [Tone: Direct ▾]       [0 cr] [Send]  | |
+---------------------------------------------------+-----------------------------------------------+
```

### Pre-Generation State (Before Letter Exists — Zero Empty Left Sidebar Needed!)
When opening `/cover-letters` for a job without a draft yet, the center canvas (`62%`) gracefully displays a **single centered Pre-Flight Brief Card (`max-w: 560px`)**:
- Pick Tone (`Direct & Executive`, `Warm & Conversational`, `Technical Builder`), Target Length (`Concise ~180w` vs `Standard ~250w`), check `2–3` verified achievements from your CV, optionally paste Company About URL/note, and click `[✨ Generate Cover Letter · 1 cr]`.
- The instant generation finishes, that brief morphs out cleanly and lives inside `[Brief & Tone ⚙]` in the Top Bar—leaving pure calm prose!

---

## 3. Eye-Scan Path & Anti-Saccade Map

1. **Fixation 1 (Center `65ch` Prose Sheet):** Natural top-to-bottom letter reading (`Subject` → `Hook` → `Proof` → `Signature`), zero sidebars pulling eyes left.
2. **Fixation 2 (Right Borderless AI Writing Coach):** Directly beside the letter, prose suggestions explain tone adjustments clearly with compact 1-line-collapsible diff cards.
3. **Fixation 3 (Paragraph Micro-Bar on Hover):** Hovering any paragraph pops `[Ask AI] [Sharpen] [Shorten]` right next to the cursor, eliminating manual prompt copy-paste.

---

## 4. Proximity & Click-Depth Budget

| User Intent | Click / Keystroke Depth | Spatial Location |
| :--- | :--- | :--- |
| **Ask AI to rewrite/shorten a paragraph** | `1` click (`[Ask AI]` / `[Shorten]` on paragraph hover) | Floating 3-item micro-bar beside hovered paragraph |
| **Apply or steer an AI suggestion** | `1` key (`Enter` / `Esc` / `R`) | Inside Proposal Card in AI Chat |
| **Change Tone, Length, or Anchor Achievements** | `2` clicks (`[Brief & Tone ⚙]` → adjust & regenerate `0 cr`) | Top-right utility popover |
| **Check JD keyword coverage naturally** | `1` click (`[Keywords]` toggle) | Top-center view toggle highlights matched keywords inline |
| **Send immediately with paired CV PDF** | `1` click (`[✉ Send in Dispatch]`) | Top-right primary split CTA (`↓ .txt`, `↓ PDF`, `Copy Text` inside caret) |

---

## 5. Detailed Zone-by-Zone Component & Interaction Spec

- **Unified Top Bar (`48px`):**
  - Left: `[← Back]` + `Identity (+20) × Target Job` Breadcrumb (reuses exact popovers from CV Studio, plus Saved Letters switcher inside Job popover).
  - Center: `[Clean Letter | Keywords]` toggle + `[‹ v2 ›]` History Scrubber.
  - Right: `[Brief & Tone ⚙]` popover + `[Send in Dispatch ▾]` primary split button (`Copy Text`, `↓ .txt`, `↓ PDF` inside menu).
- **Signature & Regional Contact Auto-Sync:** Signature footer stays bound automatically to active Identity Persona & Regional Phone (`+20` EG / `+966` KSA / `+971` UAE).
- **AI Writing Coach Shape (`Pane 2 — 38%`):** Identical geometry to `00` §5 and `12` (User Capsule vs. Borderless Prose, Thinking Accordion, Collapsible `✓ Applied` receipts, In-place `Refine...` strip, Conditional Target Rim inside Floating Composer Dock). Dynamic empty-thread quick chips: `[Cut AI clichés]`, `[Sharpen opening hook]`, `[Add notice period]`.

---

## 6. Interactivity, Adjustability & Keyboard Shortcuts

- **1 Single Splitter (`8px` target):** Drag `50/50` to `72/28`, double-click resets to `62% / 38%`.
- **Swappable (`⇄`) & Collapsible (`]`):** Flip AI Coach Left ↔ Right or hide completely (`0px`) for 100% distraction-free writing.
- **Shortcuts:** `]` toggle AI Coach, `Alt + S` swap sides, `Cmd/Ctrl + Z` undo, `Enter / Esc / R` on active proposal, `Cmd/Ctrl + Shift + C` copy clean letter text.

---

## 7. State Matrix & Edge Cases

| State | Behavior |
| :--- | :--- |
| **No Letter Generated Yet** | Centered `Pre-Flight Brief Card` inside Prose Canvas (`max-w: 560px`)—zero blank empty canvas or permanent configuration rail. |
| **No Tailored CV Yet for This Job** | Anchors achievements seamlessly from active Persona's Master Profile (`"Tip: Tailoring your CV first improves alignment"`). |
| **Out of Credits (`0 cr`) on Generate** | Saves Brief settings locally, launches `OutOfCreditsTopUpModal`, and auto-generates cleanly on top-up. |
| **AI Cliché Detection** | Highlights generic phrases (*"passionate team player"*) softly when `[Keywords]` or AI Coach audit runs, proposing metric-backed swaps. |

---

## 8. Frontend UI Implementation Contract

- **Suggested Components:** `CoverLetterSanctuary`, `QuietStudioTopBar`, `PreFlightLetterBriefCard`, `CalmProseCanvas`, `ParagraphMicroToolbar`, `BriefAndTonePopover`, `CalmAiCoachSidecar` (shared primitive from `00` §5).
- **State:** `activeLetter`, `brief: { tone, lengthMode, selectedAnchors[], companyContext }`, `viewMode: 'clean' | 'keywords'`, `versions[]`, `chat`, `layout: { chatPosition, splitRatio, isChatCollapsed }`.
- **Backend Hooks:**
  - `POST /api/v1/cover-letter` & `GET /api/v1/cover-letter` (`backend/app/api/routes/cover_letter.py`)
  - `PATCH /api/v1/cover-letter/{doc_id}` & `POST /api/v1/cover-letter/{doc_id}/chat` `[New Endpoints Needed]`
  - `GET /api/v1/cover-letter/{doc_id}/download/{pdf|txt}` `[New Endpoint Needed]`
- **UX Acceptance Criteria:**
  1. Zero permanent 3rd configuration column; Tone/Anchors live in Pre-Flight Card before creation and `[Brief & Tone ⚙]` after.
  2. Identical calm AI Chat Shape (`User Capsule`, borderless prose, collapsible receipts, `Refine...` morph, floating composer) as CV Studio.
  3. Sending in Dispatch transfers edited subject + body cleanly in 1 click.
