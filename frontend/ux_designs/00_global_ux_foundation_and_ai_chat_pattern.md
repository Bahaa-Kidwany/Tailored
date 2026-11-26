# 00 — Global UX Foundation, Calm Shell, Credit System & AI Chat Shape Architecture

**Scope:** Shared Ergonomic Infrastructure Across All Authenticated & Studio Routes  
**Implementation Status:** Partially Implemented (`AtelierSidebar.tsx` covers basic nav & identity drawer; Command Palette `Cmd/Ctrl + K`, Calm Anti-Clutter Standards, Resizable Splitters, Credit Balance Pill, Notification Drawer, and Explicit AI Chat Shape Architecture are **New**)  
**Primary Goal:** Establish calm desktop muscle memory, eliminate eye-jumping and permanent panel bloat, keep high-frequency actions within `1–2` clicks, enforce honest credit transparency, and define the exact physical shape and lifecycle of Tailored's AI Coach Chat.

---

## 1. UX Reference Benchmarks & Ergonomic Rationale

| Reference Product | Pattern Adopted | Why It Replaces Cluttered Legacy Patterns |
| :--- | :--- | :--- |
| **ChatGPT Canvas & Claude Artifacts** | **Calm 2-Pane Sanctuary** (`62%` Document / `38%` AI Chat, swappable `⇄`), collapsible to `0px` chat, floating composer, collapsed version history | Eliminates exhausting 3-pane cockpits; keeps 100% of attention on writing/reviewing instead of fighting toolbars. |
| **2025–2026 AI Chat Standard (`Claude`, `Cursor`, `Perplexity`)** | Right-aligned compact User Capsule vs. **left-aligned borderless AI prose**, collapsible 1-line Thinking Accordion, and collapsed `✓ Applied` receipts | Eliminates heavy nested message boxes and visual walls of buttons inside conversation threads. |
| **Linear & Superhuman** | `Cmd/Ctrl + K` Command Palette, `J`/`K` list traversal, `Spacebar` Quick-Peek, progressive disclosure popovers, Action-Sorted Split over noisy Kanban | Removes redundant multi-button rows on cards and reduces saccades across wide monitors. |
| **FlowCV & Lex.page** | Calm content-first canvases; layout controls hidden behind `[Customize ⚙]` popovers rather than permanent sidebars | Stops "toolbox trap" cognitive fatigue while editing CVs and cover letters. |
| **ElevenLabs & Stripe Billing** | Low-profile credit balance pill + pre-action credit cost labels + non-destructive out-of-credits top-up modal | Prevents bill anxiety while keeping discovery, 5-D scoring, and iterative AI chat refinements frictionless. |

---

## 2. Calm Anti-Clutter Laws (Strictly Enforced Across Every Page)

To guarantee no screen feels busy, cramped, or visually exhausting:
1. **The Two-Pane Studio Ceiling:** Creation workspaces (`/studio`, `/cover-letters`) MUST NEVER mount 3 permanent vertical columns or stack more than 1 horizontal chrome bar (`≤ 48px` height, `≤ 4` top-bar clusters). Secondary controls live inside on-demand popovers (`[Customize ⚙]`) or 1 quiet corner pill (`[✦ Controls]`).
2. **No Multi-Widget Cockpit Rails:** Never pin permanent summary/preview/telemetry sidebars beside centered forms or feeds (no permanent 3rd column in `/profile`, no permanent side preview rail in `/onboarding`, no competing analytics rail in `/dashboard`).
3. **One Primary CTA Per List Card:** List/queue cards (`/radar`, `/interest`, `/cvs`, `/pipeline`) show clean title/context + max 1 status/fit indicator; secondary buttons appear gently on row hover, `Spacebar` Quick-Peek, or inside the adjacent inspector.
4. **Zero Eye-Jumping (Anti-Saccade Discipline):** Controls that mutate a document or item sit adjacent to that exact content (e.g., floating `[Ask AI]` micro-bar directly beside hovered CV bullets/paragraphs) rather than across opposite monitor edges.

---

## 3. Two-Tier Shell Architecture

### Mode A: Standard Workspace Shell (Discovery, Lists, CRM, Identity, Settings)
```
+---------------------------------------------------------------------------------------------------+
| [LEFT NAV RAIL: 212px expanded / 56px icon rail] | [FLUID WORKSPACE VIEWPORT: flex-1]             |
|                                                  |                                                |
| [Brand Mark: Tailored]         [Collapse Rail [] | [Calm Route Viewport — Max 2 Primary Zones]    |
|                                                  |                                                |
| +----------------------------------------------+ |                                                |
| | IDENTITY CAPSULE (1-Click Drawer Trigger)    | |                                                |
| | Mostafa Ibrahim                              | |                                                |
| | Senior AI Engineer  ·  +20                   | |                                                |
| +----------------------------------------------+ |                                                |
|                                                  |                                                |
| > Dashboard                              [G D]   |                                                |
| > Job Radar                              [G R]   |                                                |
| > Interest List               (5)        [G I]   |                                                |
| > CV Studio                              [G S]   |                                                |
| > Cover Letters                          [G L]   |                                                |
| > Saved CVs                              [G V]   |                                                |
| > Pipeline                    (3)        [G P]   |                                                |
|                                                  |                                                |
| ------------------------------------------------ |                                                |
| > Master Profile                                 |                                                |
| > Plans & Credits                                |                                                |
| > Account & Security                             |                                                |
|                                                  |                                                |
| +----------------------------------------------+ |                                                |
| | [⚡ 14 Credits]   [🔔 (2)]   [⌘K]            | |                                                |
| +----------------------------------------------+ |                                                |
+---------------------------------------------------------------------------------------------------+
```

### Mode B: Focused Studio Isolation Shell (`/studio` and `/cover-letters`)
- Cross-site left rail is **hidden** completely so 100% of screen width belongs to the **2-Pane Sanctuary** (Document `62%` + AI Chat `38%`).
- Replaced by a quiet `[← Back]` pill at the left edge of the single `48px` top bar (plus `Cmd/Ctrl + K` to jump anywhere instantly).

---

## 4. Global Ergonomic Primitives & Credit UX Grammar

### 4.1 Left-Anchored Identity & Phone Switcher Drawer
- Clicking the **Identity Capsule** (or `Cmd/Ctrl + Shift + P`) opens a clean `340px` slide-over drawer adjacent to the rail:
  1. Active Career Persona radio cards (`Senior AI Engineer`, `Data Scientist`, etc.).
  2. Dynamic Regional Phone selector (`+20 EG`, `+966 KSA`, `+971 UAE`, or `Hide Phone`).
  3. `[Manage Personas in /profile →]`.

### 4.2 Universal Command Palette (`Cmd/Ctrl + K` or `/`)
- Single centered search/execution bar (`max-width: 580px`) available on every page—even `/studio` and `/404`.
- Supports instant route jumps (`Go to Radar`), context switching (`Switch Phone +966`), **Smart Paste Ingestion** (pasting a job URL or JD anywhere saves to Interest & scores fit), and workspace actions (`Buy Credit Pack`, `Reset Pane Widths`).

### 4.3 Standardized Resizable Splitters & Quick-Peek
- `1px` visual hairline inside an `8px` hover/drag hit zone (`col-resize`); strict min/max clamping; **double-click resets** to default ratio; widths persist per route in `localStorage`.
- `Spacebar` opens an adjacent Quick-Peek drawer on list views (`/dashboard`, `/interest`, `/cvs`, `/pipeline`) so scanning never forces route hops.
- Optimistic mutations show a `4.5s` `[Undo]` toast; empty states always provide 1 helpful CTA; errors speak in honest first-person plural (*"We couldn't reach LinkedIn — your draft is safe locally."*).

### 4.4 Pay-As-You-Go Credit UX Grammar
- **Persistent Balance Pill:** Shows `⚡ {balance} Credits` (`≤ 2 cr` low-balance alert; clicking opens quick breakdown + `[Top Up]`).
- **Pre-Action Cost Stamps:** Only net-new generation triggers stamp `· 1 cr` (`[Tailor CV · 1 cr]`, `[Draft Cover Letter · 1 cr]`). Discovery, 5-D scoring, downloading existing PDFs, and **all iterative AI chat refinements on an already-unlocked CV/Cover Letter cost `0` extra credits**.
- **Already-Unlocked Protection:** Existing `(job_id, persona_id)` drafts automatically display `[Open Existing Draft]` (`0 cr`) above `[Re-Tailor Fresh · 1 cr]`.
- **Non-Destructive Insufficient Credits Modal:** Never clears unsaved edits or chat threads if balance hits `0`; saves state locally and resumes queued action seamlessly after pack checkout.

---

## 5. Canonical AI Chat Shape & Visual Anatomy (Flagship UX Blueprint)

Used across **`/studio` (CV Studio)** and **`/cover-letters` (Cover Letter Studio)** inside a calm 2-Pane Sanctuary. Every visual boundary, spacing rule, and interaction state is explicit:

### 5.1 Three Adjustable Container Shapes (User-Controlled Ergonomics)
```
SHAPE 1 — DOCKED SPACIOUS SIDECAR (Default: 62% Document / 38% Chat, ~500px at 1440px, min 360px / max 580px)
+-----------------------------------------------------+----------------------------------+
|  LIVING DOCUMENT STAGE (62%)                        |  AI CHAT SIDECAR (38%)           |
|  Centered Paper / Prose with wide breathing desk    |  Quiet Header + Borderless Stream|
|                                                     |  + Floating Rounded Composer     |
+-----------------------------------------------------+----------------------------------+

SHAPE 2 — SWAPPED SIDES (1-Click `⇄` Button in Chat Header) OR EXPANDED 50/50 REVIEW SPLIT
+----------------------------------------+-----------------------------------------------+
|  AI CHAT (Left — Familiar ChatGPT Feel)|  LIVING DOCUMENT STAGE (Right — 50% to 62%)   |
+----------------------------------------+-----------------------------------------------+

SHAPE 3 — COLLAPSED SANCTUARY (Shortcut `]` or `[Collapse]` — 100% Pure Reading/Editing Stillness)
+----------------------------------------------------------------------------------------+
|  100% FULL-SCREEN DOCUMENT STAGE                                                       |
|                                                                                        |
|                                                         Corner Pill: [✦ Ask AI Coach ] |
+----------------------------------------------------------------------------------------+
```
- **Why Swappable Left ↔ Right (`⇄`):** Some writers prefer reading Left-to-Right (Document left, Coach right like Claude Artifacts); others feel at home with Chat left, Canvas right (ChatGPT Canvas). A single `⇄` button lets each user choose comfortably and remembers it in `localStorage`.

### 5.2 Exact Vertical Shape & Message Rhythm Inside the AI Chat Panel
```
+-----------------------------------------------------------------------------------+
| 1. QUIET PANEL HEADER (44px, single slim bottom border)                           |
| Coach · Grounded: Profile + Swvl ✓               [⇄ Swap] [History ▾] [New] [✕]   |
|-----------------------------------------------------------------------------------|
| 2. CONVERSATION STREAM (Independent Scroll · Generous 24px side padding & air)    |
|                                                                                   |
|    USER MESSAGE SHAPE (Right-aligned compact capsule, max-width 82%, soft fill):  |
|                                            +-----------------------------------+  |
|                                            | Make my Swvl pricing bullet more  |  |
|                                            | specific to FastAPI latency       |  |
|                                            +-----------------------------------+  |
|                                                                                   |
|    THINKING ACCORDION SHAPE (Left-aligned, 1 quiet collapsible line):             |
|    ▸ Checked Swvl role in Master Profile · Verified 42% latency metric (1.4s)     |
|      (While streaming: pulses live steps -> collapses cleanly when answer starts) |
|                                                                                   |
|    AI RESPONSE SHAPE (Left-aligned, 100% BORDERLESS editorial prose — NO BOX!):   |
|    Your Master Profile already records a 42% latency reduction on Swvl's dynamic  |
|    pricing service. I tightened Bullet 2 to surface FastAPI upfront without       |
|    adding unverified claims:                                                      |
|                                                                                   |
|    PROPOSAL CARD SHAPE (Quiet bordered unit ONLY for concrete document edits):    |
|    +---------------------------------------------------------------------------+  |
|    | Experience -> Swvl · Bullet 2                               [Locate ↗]    |  |
|    | - Built backend routing services in Python for fleet tracking             |  |
|    | + Architected FastAPI & PyTorch pricing endpoints, cutting route latency  |  |
|    |   by 42% across 1,400 daily dispatches                                    |  |
|    |---------------------------------------------------------------------------|  |
|    | [✓ Apply  ↵]    [Skip  Esc]    [Refine...  R]                             |  |
|    +---------------------------------------------------------------------------+  |
|                                                                                   |
|    POST-APPLY COLLAPSED RECEIPT SHAPE (After clicking Apply — keeps thread calm): |
|    ✓ Applied to Swvl · Bullet 2                                          [Undo]   |
|                                                                                   |
|    ---------------------------------------------------------------------------    |
|    IN-PLACE `Refine...` MORPH (Same card bottom row transforms when [Refine] hit):|
|    | [Shorter]  [More metrics]  [Less formal]  | [Type tweak...        ↵] [✕] |  |
|-----------------------------------------------------------------------------------|
| 3. FLOATING ROUNDED COMPOSER DOCK (16px breathing inset from panel edges)         |
|    +---------------------------------------------------------------------------+  |
|    | ↳ Focused: Swvl · Bullet 2                                           [×]  |  |  <-- Appears ONLY when targeting a section/bullet!
|    |---------------------------------------------------------------------------|  |
|    | Ask to rewrite, quantify, check gaps, or type @ to target a section...    |  |
|    |                                                                           |  |
|    | [@ Target]  [Mode: Surgical ▾]                        [0 cr]  [Send ↑]    |  |
|    +---------------------------------------------------------------------------+  |
|    (When empty conversation: 3 quiet starter suggestions sit neatly above dock)   |
+-----------------------------------------------------------------------------------+
```

### 5.3 Crucial Behavioral Rules Defining This Chat Shape
1. **No Boxes Around AI Text:** Regular AI explanations, coaching feedback, and skill audits render as **borderless, well-spaced editorial prose** directly on the panel background—never wrapped inside bubbles or dark rectangular cards. Boxes are reserved *exclusively* for interactive **Proposal Diff Cards** and **User Prompts**.
2. **Cards Shrink When Resolved:** The moment a user clicks `[✓ Apply]` or `[Skip]`, the tall Proposal Card animates smoothly down into a **single quiet 1-line receipt** (`✓ Applied to Swvl · Bullet 2   [Undo]`). Old suggestions never clog the conversation with stale gray buttons!
3. **Zero-Hallucination Metric Interception:** If the user asks to *"add metrics"* where Master Profile holds no number, the AI does NOT guess `"35%"`; its borderless reply asks calmly inline (`"What real % or latency number did you hit on this project?"`) with a 1-click `[Insert my number ->]` chip.
4. **Bidirectional Canvas Coupling:**
   - Hovering any Proposal Card softly illuminates the exact bullet/paragraph on the Document Canvas (`62%` pane); clicking `[Locate ↗]` scrolls directly to it.
   - Hovering/selecting text on the Document Canvas shows a tiny **3-action micro-bar** (`[Ask AI]` · `[Shorten]` · `[Edit]`) right at the selection; clicking `[Ask AI]` lights up the slim **Conditional Top Rim** (`↳ Focused: Swvl · Bullet 2 [×]`) inside the Floating Composer Dock and focuses typing immediately.
5. **Conditional Starter Chips Only:** Starter chips (`[Address missing skill]`, `[Fit on 1 page]`, `[Fact audit]`) appear gently **above** the Composer Dock only on an empty thread or when a clear trigger exists (e.g., page overflow `>100%`)—never as a permanent cluttered toolbar row.
6. **Smart Scroll Unlock & Turn Branching:** Auto-scrolls during streaming only while anchored near the bottom; scrolling up immediately unlocks scroll and drops a discrete `[↓ Latest]` pill. Hovering any past user capsule exposes `[Edit & Branch from here]`.
7. **Full History & Undo Integration:** `[History ▾]` reveals a quiet drawer of past threads (`Swvl Draft Thread`, `Audit Pass`) without adding permanent chrome; `[Undo]` inside any 1-line receipt or `Cmd/Ctrl + Z` reverses edits cleanly.
