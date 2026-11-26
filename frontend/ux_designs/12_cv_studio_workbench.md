# 12 — Flagship CV Studio Workbench + Calm AI Coach (`/studio`)

**Route:** `/studio` (supports `?job_id=...&doc_id=...&persona=...`)  
**Implementation Status:** Implemented (`CVStudioWorkbench.tsx`) — **Ground-Up Calm 2-Pane Sanctuary & AI Chat Shape Overhaul** (Replaces exhausting 3-column cockpit with ChatGPT Canvas / Claude Artifacts / FlowCV calm 2-pane editing)  
**Primary User Goal:** Edit and tailor a crisp, 1-page ATS LaTeX CV for a paired target job in total visual peace—comparing live paper edits against borderless AI suggestions and clickable 1-line-collapsible diffs with zero eye jumping or cockpit fatigue.  
**Entry Points:** Global Sidebar (`G` then `S`), Radar (`[Tailor CV]`), Job Detail (`/jobs/:id`), Interest List, Saved CVs, Pipeline, Dashboard.  
**Exit Destinations:** Exact previous route (`← Back`), `DispatchApplicationModal` (overlay), `/cover-letters?job_id=...`, `Cmd/Ctrl + K` jump anywhere.  
**Credit Model Impact:** Opening/editing an existing CV and **every iterative AI chat turn on that CV cost `0` additional credits**. Pairing & tailoring against a *brand-new* untailored job stamps `[Tailor New Job · 1 cr]` clearly before execution.

---

## 1. UX Reference Benchmarks & Ergonomic Rationale

| Reference | Pattern Adopted | How It Eliminates Studio Suffering |
| :--- | :--- | :--- |
| **ChatGPT Canvas & Claude Artifacts** | **2-Pane Sanctuary** (`62%` Living Paper / `38%` Spacious AI Chat, swappable `⇄`, collapsible to `0px` chat) + single `[‹ v3 ›]` version stepper | Removes the permanent Left Controls Column, separate Telemetry Bar, and Pending Diffs Bar—cutting permanent visual clutter by >60%. |
| **FlowCV & Lex.page** | Content-first paper stage with wide margins; formatting/section toggles tucked neatly inside one `[Customize ⚙]` popover + 1 quiet corner pill | Eliminates the "35-button toolbox trap" so eyes stay peacefully centered on the CV paper. |
| **2025–2026 AI Chat Shape (`Cursor`, `Claude`)** | Right-aligned User Capsule + **borderless AI prose** + collapsible Thinking Accordion + `Proceed/Skip/Refine` diff cards that shrink to `✓ Applied [Undo]` receipts | Keeps the conversation scannable and calm while maintaining strict Zero-Hallucination verification. |

---

## 2. Desktop Layout Architecture & ASCII Wireframe (`1440px`)

```
+---------------------------------------------------------------------------------------------------+
| 1. ULTRA-QUIET SINGLE TOP BAR (Height: 48px, Sticky — Strictly 4 Clusters, Cross-Site Rail Hidden)|
|                                                                                                   |
| [← Back]   Mostafa · AI (+20)  ×  Swvl · Lead DS (94%) ▾   |   [Paper | Diffs | .tex]  [‹ v3 ›]   |
|                                                            |   [Customize ⚙]    [Export PDF ▾]    |
+---------------------------------------------------------------------------------------------------+
| 2. CALM 2-PANE SANCTUARY (Height: 100vh - 48px · Single 8px Splitter · Double-Click Reset · `⇄`)  |
|                                                                                                   |
| PRIMARY PANE (62%, min 520px): LIVING ATS PAPER STAGE     | COLLABORATIVE PANE (38%, ~500px,      |
| (Pure calm desk margins surrounding floating CV paper)    |  min 360px / max 580px, `]` collapses)|
|                                                           |---------------------------------------|
|                                                           | Coach · Grounded: Profile + Swvl ✓  |
|               +-------------------------------+           |                [⇄] [History ▾] [✕]   |
|               | MOSTAFA IBRAHIM               |           |---------------------------------------|
|               | Senior AI Eng · +20 · Cairo   |           |                       +-------------+ |
|               |                               |           |                       | Emphasize   | |
|               | PROFILE                       |           |                       | FastAPI <50ms| |
|               | Lead ML Practitioner with...  |           |                       | on Swvl #2  | |
|               |                               |           |                       +-------------+ |
|               | EXPERIENCE                    |           | ▸ Verified Swvl role in Profile (1.2s)|
|               | Swvl · Lead Data Scientist    |           |                                       |
|               | • Dynamic Route Pricing:      |<----------+ Your Master Profile logs 42% lower  |
|               |   [Hover: Ask AI · Shorten · Edit]        | latency on Swvl. Tightened Bullet 2   |
|               |   Architected FastAPI & PyTorch|          | with zero unverified claims:          |
|               |   endpoints cutting latency...|           |                                       |
|               |   ◦ Stack: Python, FastAPI... |           | +-----------------------------------+ |
|               |                               |           | | Swvl · Bullet 2        [Locate ↗] | |
|               | PROJECTS / SKILLS / EDUCATION |           | | - Built backend APIs in Python    | |
|               |                               |           | | + Architected FastAPI & PyTorch   | |
|               +-------------------------------+           | |   pricing endpoints (-42% latency)| |
|                                                           | | [✓ Apply ↵] [Skip Esc] [Refine R] | |
|                                                           | +-----------------------------------+ |
|                                                           |                                       |
|                                                           | ✓ Applied Profile Summary      [Undo] |
|                                                           |                                       |
|                                                           | +-----------------------------------+ |
|                                                           | | ↳ Focused: Swvl · Bullet 2    [×] | |
| Quiet Corner Whisper (Bottom-Left):                       | |-----------------------------------| |
| Page 1 of 1 · 92% · Zoom 100% ▾                           | | Ask to edit, quantify, or @...    | |
|                                                           | | [@] [Surgical ▾]     [0 cr] [Send]| |
| Quiet Corner Pill (Bottom-Right):      [✦ Quick Controls] | +-----------------------------------+ |
+-----------------------------------------------------------+---------------------------------------+
```

---

## 3. Eye-Scan Path & Anti-Saccade Map

1. **Fixation 1 (Left 62% Pane — Centered Floating Paper Sheet):** Calm vertical reading of the real formatted ATS resume. Zero persistent side menus stealing gaze from the left margin.
2. **Fixation 2 (Right 38% Pane — Adjacent Borderless AI Stream):** Moving eyes smoothly right reveals borderless explanations and compact diff cards; hovering any diff card highlights the exact bullet directly across the single splitter.
3. **Fixation 3 (On-Demand Top Popovers Only When Needed):** Clicking `[Mostafa · AI (+20)]`, `[Swvl · Lead DS (94%)]`, or `[Customize ⚙]` drops a clean temporary popover right under the user's cursor—and disappears the instant a choice is made.

---

## 4. Proximity & Click-Depth Budget

| User Intent | Click / Keystroke Depth | Spatial Location |
| :--- | :--- | :--- |
| **Ask AI about a specific bullet** | `1` click (`[Ask AI]` on bullet hover) | Floating 3-action micro-bar beside bullet → pins `↳ Swvl · Bullet 2` in Composer Rim |
| **Edit any bullet manually inline** | `1` click directly on text (`Enter` saves) | Directly on the Paper Canvas (no sidebar form!) |
| **Accept, Skip, or Refine an AI rewrite** | `1` key (`Enter`, `Esc`, `R`) or `1` click | Proposal Card bottom row (collapses to 1-line receipt on resolve) |
| **Swap Persona, Regional Phone (`+20`/`+966`), or Base CV** | `2` clicks (Click Identity Breadcrumb → pick) | Top-left Pairing Breadcrumb popover |
| **Swap Target Job or Drop New Screenshot (`Ctrl+V`)** | `Ctrl+V` anywhere OR `2` clicks on Target Breadcrumb | Anywhere in Studio (Dual-Write syncs `/interest`) or Target Job popover |
| **Toggle Sections (`Projects`, `Stack`) or Intensity** | `2` clicks (`[Customize ⚙]` → toggle) | Top-right utility popover |
| **Export PDF / `.tex` / Dispatch Email** | `1` click (`[Export PDF ▾]`) | Top-right primary split button (`[✉ Dispatch]` inside menu or direct shortcut) |

---

## 5. Detailed Zone-by-Zone Component & Interaction Spec

### 5.1 Top Bar Pairing Breadcrumb & Popovers (Zero Permanent Cockpit)
- **Half 1 — Identity Popover (`Mostafa · AI (+20)`):** Pick Active Profile, Career Persona (`Senior AI Engineer` / `Data Scientist`), Regional Phone (`+20`, `+966`, `+971`, or `Hide`), Header City, and Base CV (`Canonical` vs `Forked`).
- **Half 2 — Target Job & Ingestion Popover (`Swvl · Lead DS (94%)`):** Search & pair any job from Interest List, view Matched vs. Missing Skills (click any missing skill to drop a prompt straight into AI Chat), paste URL/JD or drop Screenshot (Dual-Write rule saves to `/interest` + pairs here), or click `[Unselect Job]` to edit your Master Canonical CV cleanly.
- **Right Popover (`[Customize ⚙]`):** Holds Tailoring Intensity (`Surgical` / `Metrics+` / `Executive`), Section Visibility & Drag Order (`Profile`, `◦ Stack:` sub-lines, `Projects`, `Certificates`, `Languages` — mandatory sections locked), ATS Page Budget (`92% of 1 page`), and Compiler Audit log. **Zero permanent panel space wasted!**
- **Primary Split CTA (`[Export PDF ▾]`):** Primary click downloads compiled 1-page ATS PDF; caret opens `[Download .tex]`, `[Copy .tex Source]`, `[Draft Cover Letter ↗]`, and `[✉ Dispatch Application]`.

### 5.2 Living Paper Canvas & Whisper Controls (Pane 1 — `62%`)
- **Three View Modes:**
  1. **`Paper` (Default):** Crisp `cv(1)(1).tex` layout (Header, justified bold-lead Summary, multi-role Experience + `[Role Summary]` + `◦ Stack:` tags, Projects, categorized Skills, Education, Certificates, Languages).
  2. **`Diffs`:** Clean vertical before/after comparison of every tailored bullet with `[Revert]` per item.
  3. **`.tex`:** Clean editable LaTeX code view with overflow/syntax guards (`\text{}` single-line protection).
- **Minimal Bullet Hover Micro-Bar:** Hovering or selecting any bullet surfaces strictly **3 clean actions** beside it: `[Ask AI]` · `[Shorten]` · `[Edit]`. No sprawling icon grid.
- **Quiet Corner Whispers:**
  - Bottom-Left: `Page 1 of 1 · 92% · Zoom 100% ▾` (turns gently urgent with 1-click `[Fit to 1 Page]` only if `>100%` overflow).
  - Bottom-Right: Single floating pill **`[✦ Quick Controls]`** (expands cleanly into 4 shortcuts: `1 Missing Skill: AWS`, `Auto-Fit 1 Page`, `Drop Job / Screenshot`, `Draft Cover Letter`).

### 5.3 Explicit AI Chat Shape in CV Studio (`Pane 2 — 38%`)
Implements every geometric rule from `00_global_ux_foundation_and_ai_chat_pattern.md` §5:
- **Header (`44px`):** `Coach · Grounded: Profile + Swvl ✓` + `[⇄]` (swaps Chat Left ↔ Right), `[History ▾]`, `[New]`, `[✕ Collapse]`.
- **Asymmetric Rhythm:** User prompt in right-aligned compact capsule; AI advice & skill audits flow as **100% borderless editorial text**; working steps fold into a **1-line collapsible Thinking Accordion** (`▸ Verified Swvl role in Master Profile · 1.2s`).
- **Proposal Card Lifecycle:**
  1. *Active:* `Experience -> Swvl · Bullet 2 [Locate ↗]` + clean Red/Green word diff + `[✓ Apply ↵] [Skip Esc] [Refine... R]`.
  2. *In-Place Refine Morph:* Pressing `R` or clicking `Refine...` swaps the button row into `[Shorter] [More metrics] [Less jargon] | [Type tweak... ↵]`.
  3. *Resolved:* Collapses immediately into a calm **1-line receipt** (`✓ Applied to Swvl · Bullet 2  [Undo]`) so reading the thread stays soothing.
- **Floating Rounded Composer Dock:** `16px` margin inset; shows slim top rim (`↳ Focused: Swvl · Bullet 2 [×]`) *only* when user clicked `[Ask AI]` on a bullet or typed `@`; bottom controls strictly limited to `[@ Target]`, `[Mode: Surgical ▾]`, `[0 cr]`, `[Send ↑ / ■ Stop]`.

---

## 6. Interactivity, Adjustability & Keyboard Shortcuts

- **1 Single Splitter (`8px` target):** Drag between `50/50` and `72/28`; double-click resets to `62% / 38%`.
- **Swap Chat Side (`⇄`):** Moves AI Chat to Left (`38%`) or Right (`38%`) instantly.
- **Pure Focus Mode (`]`):** Collapses AI Chat completely (`100%` CV Paper) leaving only a subtle bottom-right `[✦ Ask AI Coach]` pill.

| Shortcut | Action |
| :--- | :--- |
| `]` | Collapse / Expand AI Chat Pane (`0px` ↔ `38%`) |
| `Alt + S` | Swap Document ↔ AI Chat sides (`⇄`) |
| `Alt + 1 / 2 / 3` | Switch `Paper` / `Diffs` / `.tex` |
| `Enter / Esc / R` (on Proposal Card) | `Apply` / `Skip` / In-Place `Refine` |
| `Cmd/Ctrl + Z` | Undo last bullet edit or AI apply |
| `Cmd/Ctrl + K` | Command Palette (jump or paste job anywhere) |
| `Ctrl/Cmd + V` (outside inputs) | Instant Screenshot / URL Dual-Write ingestion |

---

## 7. State Matrix & Edge Cases

| State | Behavior |
| :--- | :--- |
| **Opening Studio With Untailored Job** | Shows Canonical Base CV on Left + single calm prompt in Chat/Canvas: *"Ready to tailor for Noon — Senior ML Engineer (89% fit). [⚡ Tailor Now · 1 cr]"* (zero surprise credit charge!). |
| **AI Requests Missing Metric** | Never invents numbers; borderless AI text asks gently for the real number with an inline `[Insert metric ->]` reply helper. |
| **1-Page Overflow (`>100%`)** | Quiet bottom-left whisper gently warns `108% · Overflows to Page 2` with 1-click `[Ask AI to Condense]` right beside it. |
| **Zero Credits on New Job Swap** | Preserves current edits locally, opens `OutOfCreditsTopUpModal`, and immediately tailors new target job upon top-up. |
| **Offline / LaTeX Compiler Warning** | Keeps editing & `.tex` export working seamlessly via fallback PDF synthesis; flags any compiler warning neatly inside `[Customize ⚙]`. |

---

## 8. Frontend UI Implementation Contract

- **Suggested Components:** `CVStudioSanctuary`, `QuietStudioTopBar`, `PairingBreadcrumbPopover`, `CustomizeStudioPopover`, `LivingCvPaperStage`, `BulletMicroToolbar`, `CornerQuickControlsPill`, `CalmAiCoachSidecar` (shared primitive from `00` §5: `UserCapsule`, `ThinkingAccordion`, `BorderlessAiProse`, `CollapsibleProposalCard`, `InlineRefineBar`, `FloatingComposerDock`).
- **State (`StudioState`):**
  - `pairing: { profileId, personaId, regionalPhone, baseCvId, job: JobItem | null }`
  - `canvas: { docId, viewMode: 'paper' | 'diffs' | 'latex', versionIdx, versions[], hiddenSections[], intensity, pageBudgetPct, zoomPct, focusedBulletId }`
  - `chat: { threadId, mode, isStreaming, messages[], targetAnchor }`
  - `layout: { chatPosition: 'right' | 'left', splitRatio: 0.62, isChatCollapsed: boolean }`
- **Backend Hooks:**
  - `POST /api/v1/cv-fit`, `GET /api/v1/cv-fit/{doc_id}`, `GET /api/v1/cv-fit/{doc_id}/download/{kind}` (`backend/app/api/routes/cv_fit.py`)
  - `PATCH /api/v1/cv-fit/{doc_id}` `[New Endpoint Needed for saving inline edits & version snapshots]`
  - `POST /api/v1/cv-fit/{doc_id}/chat` (SSE streaming thinking steps + diff proposals) `[New Endpoint Needed]`
  - `POST /api/v1/jobs/ingest-screenshot` `[New Endpoint Needed]`
- **UX Acceptance Criteria:**
  1. Zero permanent 3rd column or multi-row toolbars; maximum 4 control clusters in the `48px` top bar.
  2. Regular AI explanations are 100% borderless; resolved diff cards collapse cleanly to 1-line `✓ Applied [Undo]` receipts.
  3. Clicking `Refine...` modifies the bottom row of that card in-place without forcing a new chat message.
  4. Clicking `⇄` cleanly swaps Document and AI Chat sides and persists user preference.
  5. Clicking `[Ask AI]` on any bullet pins its anchor directly into the Floating Composer Top Rim with zero eye jump.
