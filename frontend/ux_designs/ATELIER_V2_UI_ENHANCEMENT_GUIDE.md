# Atelier V2 (Option C) — Studio UI/UX Enhancement Reference & Workspace Rollout Guide

**Reference Implementation Routes:** `/studio` ([CvStudioPage.tsx](file:///d:/Tailored/frontend/src/pages/CvStudioPage.tsx)), `/cover-letters` ([CoverLetterStudioPage.tsx](file:///d:/Tailored/frontend/src/pages/CoverLetterStudioPage.tsx)), `/dashboard` ([DashboardPage.tsx](file:///d:/Tailored/frontend/src/pages/DashboardPage.tsx)), `/radar` ([RadarPage.tsx](file:///d:/Tailored/frontend/src/pages/RadarPage.tsx)), & `/pipeline` ([PipelinePage.tsx](file:///d:/Tailored/frontend/src/pages/PipelinePage.tsx))  
**Status:** Phases A–D implemented & verified live in Chrome (`1440×900`, `0` JS errors, `0` failed requests; backend pytest `8/8` passing)  
**Remaining Rollout Target:** `SavedCvsPage.tsx`, `/jobs/:id`, `/pipeline/:id`, and Phase 3 account pages (`/profile`, `/plans`, `/account`, `/notifications`)  
**Brand Compliance:** 100% Tailored Brand Book v1.2 tokens (`--ink`, `--ink-elevated`, `--paper`, `--chalk`, `--thread`, `--kraft`, `--dye`, `--mist`, `--green`, `--amber`, `--alarm`, `--n700`, `--n500`, `--n300`, `--n100`), zero CSS gradients, zero raw hex literals outside `src/styles/brand.css`, zero banned fonts, zero emojis.

---

## Executive Summary

Previous screens relied on flat muddy chalk (`#E5E0DA`), `1px` rectangular outlines on every widget, all-caps monospace UI controls, rigid wall-to-wall docked split panes, and verbose helper copy—producing a static "Windows XP dialog" feel and wasted viewport height.

`/studio` establishes the **Atelier V2 (Option C)** visual language:
1. **Continuous dark espresso canvas (`--ink: #1A1412`)** behind both the living document and the AI sidecar.
2. **Detached floating warm-paper (`--paper: #F5F3EF`) surfaces** lifted by diffuse shadow depth rather than wireframe boxes.
3. **Subtle Brand craft wallpaper (`AtelierFrenchCurveBackdrop`)** visible strictly inside the workspace stage below the solid header—never inside top navigation or inside opaque reading/chat cards.
4. **Borderless tonal depth, sentence-case `IBM Plex Sans` interactive controls, and crisp micro-motion** that eliminates static snapshots and unnecessary scrolling.

---

## The 7 Core Enhancements Implemented on `/studio`

### 1. Continuous Dark Canvas + Detached Floating Light Surfaces (Option C)
- **Stage Ground:** Unified `.t-cv-studio-v2.t-studio-shell` and `.t-atelier-stage` on solid `var(--ink)` (`#1A1412`).
- **Solid Pattern-Free Header (`54px`):** `header.t-studio-bar` renders flat `background: var(--ink); border-bottom: none; position: relative; z-index: 45` so no rigid horizontal seam splits the bar and zero backdrop lines bleed behind top controls.
- **Detached Floating Coach Card:** Wrapped the AI Coach in `.t-atelier-coach-float-wrap` (`padding: 4px 14px 14px 2px` on right, swapping to `4px 2px 14px 14px` when docked left) so the `--paper` `.t-chat-pane` floats `14px` inset from the viewport edges with the Brand top-right armhole curve (`border-radius: 6px 26px 6px 6px`) and elevation shadow (`0 28px 60px -16px rgba(0, 0, 0, 0.58)`).
- **Floating Drag Handle (No Edge-to-Edge Wall):** Replaced the full-height gray splitter hairline with a centered `3px × 44px` rounded vertical drag handle (`.t-splitter::before`, `opacity: 0.65`) that smoothly grows to `72px` in `var(--thread)` (`#E9453F`) on hover/drag.

### 2. Brand Book French-Curve & Craft Wallpaper Backdrop (`AtelierFrenchCurveBackdrop`)
Created in [BrandElements.tsx](file:///d:/Tailored/frontend/src/brand/BrandElements.tsx) and mounted strictly inside `.t-atelier-stage` (`z-index: 0`, `pointer-events: none`), staying strictly beneath the workbench (`z-index: 1`) and the opaque floating Coach window (`z-index: 2`):
- **Layer 1 — Tiled Craft Wallpaper (`460×460` `<pattern id="tailoredAtelierTile">`):**
  - WhatsApp dark-wallpaper aesthetic rendered with clean flat vector strokes (`stroke="var(--chalk)"`, `strokeOpacity: 0.08–0.095`) and delicate red stitch/notch accents (`var(--thread)`, `0.13–0.17` opacity):
    - Two **French-curve templates** (with eyelets, spine ticks, and dashed inner seam).
    - **Garment pattern silhouettes:** Front bodice with armhole cutout + grainline arrow, pointed pocket pentagon, and collar arc.
    - **Tailor tools:** Scissors (`48px` Brand icon geometry), graduated measuring tape, threaded needle with flowing dashed thread, plus scattered notches and `×` basting stitches.
- **Layer 2 — Sweeping Crossing Lines (`1440×860` viewBox):**
  - **Primary bottom-left to upper-right sweep:** 3 parallel Brand armhole curves (`var(--thread)` `2.1px` at `0.22` opacity, paired with solid & dashed `var(--chalk)` companion strokes at `0.10–0.11` opacity).
  - **Secondary counter-crossing sweep:** Soft dashed `var(--kraft)` curve (`0.15` opacity) and fine `var(--chalk)` echo (`0.075` opacity) intersecting gently across open desk margins.

### 3. Borderless Tonal Depth (Zero `1px` Wireframe Cages)
Removed rectangular `1px` borders across interactive surfaces, separating hierarchy cleanly via tonal background steps and soft shadows:
- **Header Controls & Pairing Triggers:** Borderless `.t-atelier-topbar-ghost` (transparent -> `--ink-elevated` hover) and `.t-atelier-pair-btn` (`--ink-elevated` fill + subtle `inset 0 1px 0 rgba(229, 224, 218, 0.06)`).
- **Header Popovers & Menus:** Pure `white` `.t-popover` (`border: none`, `border-radius: 4px 20px 4px 4px`, deep studio shadow) using borderless `.t-atelier-menu-row`, `.t-atelier-popover-chip`, and borderless recessed `.t-atelier-inline-input` (`--paper` -> `--chalk` + focus ring on active focus).
- **Coach Header Context Badge:** Borderless warm Kraft wash (`.t-atelier-context-pill`, `background: rgba(205, 174, 136, 0.28)`).
- **Seamless White Proposal Card (No 3-Box GroupBox):** `.t-proposal-card` uses `background: white; border: none; border-radius: 4px 20px 4px 4px; box-shadow: 0 12px 32px -12px rgba(26, 20, 18, 0.14)` with zero internal divider rules. Old and new diff lines stand out cleanly using soft semantic tint washes (`rgba(143, 29, 44, 0.055)` + left `--alarm` bar, and `rgba(30, 138, 90, 0.065)` + left `--green` bar).
- **Borderless Card & Prompt Actions:** `Apply` uses `.t-atelier-btn-primary` (`var(--thread)` + diagonal curve); `Skip` uses `.t-atelier-btn-tonal` (`--paper` -> `--chalk` hover); `Refine` uses `.t-atelier-btn-ghost`. Applied/skipped receipts collapse into borderless `white` left-accented 1-line cards.
- **Soft Starter Pills & Floating Composer:** Starter prompts (`.t-atelier-starter-btn`) use soft `rgba(26, 20, 18, 0.055)` tonal pills with a tiny `--thread` notch; composer (`.t-composer-dock`) sits on borderless `white` with a crisp `1.5px var(--ink)` focus ring on `:focus-within`; disabled Send button stays solid neutral (`--chalk` / `--n500`, `opacity: 1`) instead of washed-out pink.

### 4. Typography Hierarchy & Custom Controls
- **`Fraunces` Editorial Voice:** Used for panel titles (`.t-atelier-coach-title`: `Tailor Coach`, `18px`, `font-weight: 540`) and CV candidate header.
- **Sentence-Case `IBM Plex Sans` (`500`/`600`) for All Controls:** Replaced uppercase monospace labels across top-bar buttons (`Back`, `Customize`, `Export PDF`, `Paper`, `Diff`, `.tex`, `Fit`), proposal actions (`Apply`, `Skip`, `Refine`, `Locate`, `Undo`), starter chips (`Quantify Bullet 1`, `Shorten Summary`, `Audit JD Gaps`), and popover rows.
- **`IBM Plex Mono` Reserved Strictly for Data & Source:** Tabular figures (`98%`, `v1`/`v2`, `Page 1/1`, `100%`, `0 cr`, phone codes, `.tex` source).
- **Zero OS `<select>` Dropdowns:** Replaced the native composer mode `<select>` in `atelier` mode with a custom borderless `.t-atelier-mode-btn` trigger and animated upward `.t-atelier-mode-menu` (`role="listbox"` / `role="option"` with a red notch indicator on the active option).

### 5. Dynamic Micro-Interactions & Keyboard Ergonomics
- **Sliding Segmented Track (`.t-atelier-seg` + `.t-atelier-seg-thumb`):** Smooth spring-eased (`cubic-bezier(0.22, 1, 0.36, 1)`) pill translation between `Paper`, `Diff`, and `.tex`.
- **Smooth Bullet Micro-Bar (`.t-atelier-microbar`):** Kept mounted in the DOM and transitioned via `opacity` + `translateY(4px -> 0)` on bullet hover/focus rather than abrupt `display: none` toggling.
- **Cross-Pane Visual Feedback:**
  - `Locate` switches to `Paper`, calls `scrollIntoView({ behavior: 'smooth', block: 'center' })` via `anchorRefs`, and runs `atelierHighlightPulse`.
  - `Apply` triggers a green confirmation fade (`atelierAppliedFlash`) on the updated bullet/summary and pulses the top-bar Fit badge (`atelierFitPulse`).
  - Streaming turns show `.t-atelier-thinking-live` with a pulsing Brand triangle notch (`atelierPulse`).
  - Popovers, menus, sheets, and chat messages animate cleanly via `atelierPopoverIn`, `atelierMenuUpIn`, `atelierSheetIn`, and `atelierMsgIn`.
- **Keyboard & Click-Outside Ergonomics:** Click-outside handlers close open header and mode popovers cleanly; `Escape` closes all popovers and exits inline edits; `]` toggles Coach collapse/open; `Alt + S` swaps workbench and Coach panes.

### 6. Zero Filler Copy & Zero Unnecessary Scrolling
- **Removed Clutter:** Deleted the boxed `TARGET ALIGNMENT` strip above the chat stream, removed the static opening thinking-accordion line on initial load, shortened Coach opening prompt to one clear actionable line, simplified starter chips to 3 concise prompts, and replaced awkward appended `"— explicitly structured for..."` diffs with clean editorial tightening via `buildCleanLeadRewrite`.
- **Zero Vertical Scrollbar on 1-Page CV (`1440×900`):** Tuned `.t-atelier-desk-scroll` padding (`10px 26px 20px`) and 1-page CV spacing (`padding: 26px 34px` cozy / `20px 28px` compact) so the full CV (`Summary`, 4-line `Core Technical Competencies`, `Work Experience`, `Featured Projects`, and `Education, Certs & Languages`) sits centered with breathing room top and bottom and `0` scrollbar.
- **Floating Zero-Height Corners:** Status/zoom controls (`.t-atelier-status-pill`: `Page 1/1 | - 100% +`) and collapsed trigger (`.t-atelier-coach-reopen`: `Open Coach`) float cleanly in bottom desk margins without extending scroll flow.

### 7. Semantic Directional Arrows (`▲` Green Advantage vs. `▼` Red Downside Only)
Because downward red triangles visually read as a drop, downside, or warning, all decorative/neutral uses of downward red arrows were purged on `/studio` and replaced with a strict semantic directional rule:
- **Red Downward Arrow (`.t-signal-down`, `var(--thread)`, `clip-path: polygon(0 0, 100% 0, 50% 100%)`):** Strictly reserved for **downsides, disadvantages, skill gaps, removed/weaker diff lines, and low-fit warnings (`< 50%`)**. Used on Proposal/Diff old baseline lines, `Missing Stack Tokens` gap pills, and `< 50%` fit states.
- **Green Upward Arrow (`.t-signal-up`, `var(--green)`, `clip-path: polygon(50% 0, 100% 100%, 0 100%)`):** Same triangle geometry inverted upward; used strictly for **advantages, strong-fit highlights (`>= 75%`), improved/added diff lines, and applied wins**. Used on the top-bar `% Fit` badge (`>= 75%`), Proposal/Diff improved lines, and 1-line `Applied` receipts.
- **Neutral & Active UI States Never Use Red Downward Arrows:**
  - Removed red `▼` from `.t-atelier-starter-btn` prompt pills (`Quantify Bullet 1`, `Shorten Summary`, `Audit JD Gaps`).
  - Replaced active red `▼` inside `.t-atelier-mode-menu` with a crisp `TailoredIcon name="check"`.
  - Replaced `.t-eyebrow::before` red `▼` inside Studio (`Semantic Diff vs Base`) with a clean `12px × 2px` horizontal stitch dash.
  - Removed `withNotch` from the neutral Coach header icon, replaced the pulsing `.t-atelier-thinking-notch` triangle with a subtle pulsing dot, and replaced decorative red `▼` accents in `AtelierFrenchCurveBackdrop` with subtle `var(--chalk)` cross-stitches and pivot circle.

> **Resolved in Final Atelier Update:** `.tex` mode was upgraded into an Overleaf-style side-by-side **`.tex Split`** (`.t-tex-split-wrap` with `54px` bottom margin so the floating `‹ v1 › | Page 1/1 | - 100% +` pill and `Open Coach` chip never overlap code lines), auto-collapsing Coach when editing code beside the live rendered CV preview.

---

## Implemented Files & Reusable Primitive Map

| File | Scope | Key Primitives Added / Used |
| :--- | :--- | :--- |
| [BrandElements.tsx](file:///d:/Tailored/frontend/src/brand/BrandElements.tsx) | Shared Brand SVG primitive | `AtelierFrenchCurveBackdrop` |
| [app.css](file:///d:/Tailored/frontend/src/styles/app.css) | Strictly scoped Atelier V2 + `.t-signal-*` primitives | `.t-atelier-stage`, `.t-atelier-seg--studio`, `.t-cl-history-rail*`, `.t-cl-blank-dropcard*`, `.t-cl-drop-well*`, `.t-tex-split-wrap` / `.t-tex-editor-card` / `.t-tex-gutter*` / `.t-tex-textarea`, `.t-outreach-*`, `.t-atelier-coach-float-wrap`, `.t-signal-up`, `.t-signal-down` |
| [CalmAiCoachSidecar.tsx](file:///d:/Tailored/frontend/src/components/common/CalmAiCoachSidecar.tsx) | Additive `variant?: 'default' \| 'atelier'` prop | Stacked header (`Atelier Coach` + full-width context pill directly beneath), crisp `Fraunces` title, semantic `.t-signal-up`/`.t-signal-down` diff & receipt indicators, checkmarked upward mode listbox, and sentence-case tonal actions |
| [CvStudioPage.tsx](file:///d:/Tailored/frontend/src/pages/CvStudioPage.tsx) | `/studio` + `/cvs` Merged Library, Blank Drop Canvas & Overleaf `.tex Split` | Collapsible left `Saved CVs` rail (`+ New CV`), `.pdf`/`.tex`/URL/JD/screenshot drop canvas with animated `TypewriterDropPlaceholder` & `SavedRoleDropdown`, `Paper \| Diff \| .tex Split` + live preview + `Write Cover Letter` handoff |
| [CoverLetterStudioPage.tsx](file:///d:/Tailored/frontend/src/pages/CoverLetterStudioPage.tsx) | `/cover-letters` History + Blank Canvas + Composer ([coverLetterTargetParser.ts](file:///d:/Tailored/frontend/src/utils/coverLetterTargetParser.ts)) | Collapsible dark `.t-cl-history-rail` (single `+ New Letter`, non-destructive switching & Undo delete), `.t-cl-blank-dropcard` with `TypewriterDropPlaceholder` & `SavedRoleDropdown`, always-editable `To:` + direct `Send Email + CV` / `Send Email`, full formatted `<CvPaperPreview>` drawer |
| [DashboardPage.tsx](file:///d:/Tailored/frontend/src/pages/DashboardPage.tsx) | `/dashboard` command hub | Full-width `.t-dash-shell` + `.t-dash-stage` (`AtelierFrenchCurveBackdrop`), solid top bar with single-line KPI pills, 3-stop ranked match rows (1 active CTA), Selected Fit footer strip, `Continue Drafting`, and `Needs Your Action` queue |
| [RadarPage.tsx](file:///d:/Tailored/frontend/src/pages/RadarPage.tsx) | `/radar` (& `/interest` redirect) Discovery Hub | Consolidated Option A queue (`All Matches \| Saved Shortlist \| Direct Email`), integrated Multi-Modal Capture Bar, custom persona & filter popovers (0 `<select>`), clean `ul.t-bullets` horizontal dashes, and unblocked `Track in Pipeline` |
| [PipelinePage.tsx](file:///d:/Tailored/frontend/src/pages/PipelinePage.tsx) | `/pipeline` Multi-Channel CRM | Unified Direct Email + External Portal tracking (paired with backend [pipeline_service.py](file:///d:/Tailored/backend/app/pipeline/pipeline_service.py)), Atelier V2 Split/Board/Table views, borderless Stage Pills, and Connected Application Package card |
| [AtelierSidebar.tsx](file:///d:/Tailored/frontend/src/components/shell/AtelierSidebar.tsx) | Workspace left rail & account dock (`App.tsx`) | `.t-workspace-frame`, `.t-atelier-sidebar` (`244px` <-> `68px` persistent collapse), `.t-sidebar-item--active` vertical `THREAD` accent, streamlined 5-item Workspace nav (Option A + Saved CVs merged into CV Studio), bottom `Account` links, and borderless profile card |

---

## Global Workspace Navigation Shell: Collapsible Left Atelier Panel (`AtelierSidebar`)

Every authenticated workspace page (`/dashboard`, `/radar`, `/jobs/:id`, `/interest`, `/studio`, `/cover-letters`, `/cvs`, `/pipeline`, `/pipeline/:id`, `/profile`, `/plans`, `/account`, `/notifications`) shares the **Collapsible Left Atelier Panel** so navigation and account actions remain 1 click away from anywhere in the product:

- **Continuous Dark Espresso Surface (`--ink`) + Signature Top-Right Curve:** Sticky full-height sidebar (`244px` expanded <-> `68px` icon rail, persisted via `tailored_sidebar_collapsed` and toggled with the header icon, `[`, or `Ctrl/Cmd + B`) carrying the Brand Book `26px` top-right armhole curve (`border-radius: 0 var(--arc) 0 0`; mirrored on `[dir='rtl']`). On dark-canvas `/studio`, `.t-workspace-frame--dark` steps the panel surface onto `--ink-elevated` with a subtle hairline highlight so the curved top-right shoulder stays cleanly separated against `#1A1412`. Zero `1px` outer wireframe boxes — active route uses a soft elevated fill plus a crisp `3px` vertical `--thread` bar; hover fills gently with `rgba(229, 224, 218, 0.06)`.
- **Sentence-Case Controls & Numeric Mono Discipline:** Top search trigger opens the Command Palette (`⌘K`), primary links hold 5 streamlined routes (`Dashboard`, `Job Radar`, `CV Studio`, `Cover Letters`, `Pipeline`) with tabular mono counters.
- **Bottom Account Management Dock:** Houses `Master Profile`, `Plans & Credits` (showing live credit count, plus `.t-signal-down` only when credits reach `0`), `Account & Security`, `Notifications` (with `--thread` unread badge), and an elevated profile trigger opening a borderless `white` quick-menu (`Switch Persona & Phone`, `English/RTL Toggle`, `Keyboard Shortcuts`, `Sign out`) cleanly above or beside the collapsed rail.

---

## Prioritized Rollout Playbook for Upcoming Pages

When upgrading the rest of the workspace, promote the `.t-atelier-*` visual classes out of `.t-cv-studio-v2` scoping in [app.css](file:///d:/Tailored/frontend/src/styles/app.css) so all pages share one unified visual system instead of duplicating rules.

### Phase 1 — Cover Letter Studio (`/cover-letters` · `CoverLetterStudioPage.tsx`) — **Implemented**
*Direct separate sibling of `/studio`:*
- Switched root wrapper to `.t-studio-shell.t-cv-studio-v2` + `.t-atelier-stage` + `<AtelierFrenchCurveBackdrop />` below a clean solid dark `54px` top bar, and enabled `.t-workspace-frame--dark` on `/cover-letters` in [App.tsx](file:///d:/Tailored/frontend/src/App.tsx) so `AtelierSidebar`'s `26px` top-right curve separates cleanly on `--ink-elevated`.
- Added collapsible left **Tailored Cover Letters History Rail** (`.t-cl-history-rail`) + **`+ New Letter`** workflow leading to a full **Big Blank Drop Canvas** (`.t-cl-blank-dropcard` / `.t-cl-drop-well`) accepting URLs, JDs, `Ctrl+V` screenshots, or freeform briefs so saved cover letters are never overwritten and existing letters render cleanly without a top drop strip.
- Replaced native `<select>` dropdowns with borderless `.t-atelier-pair-btn` + custom `.t-popover`, made `To:` always editable with primary direct-send **`Send Email + CV`** / **`Send Email`** CTA, and equipped the bottom CV Attachment Tray with **`Choose CV ▾`**, quick **`Preview`** drawer, **`Edit in CV Studio`** handoff, and **`×`** detach.
- Removed header/switcher clutter (zero Twin Switcher), kept `Atelier Coach` (`variant="atelier"`) mounted with `@ Context` picker and structured resource cards, and preserved `Escape` / `]` / `Alt+S` keyboard shortcuts.

### Phase 2 — Split-Pane Intelligence & CRM Views (`/radar` **Implemented**, `/pipeline` **Implemented**, `/cvs`, `/jobs/:id`, `/pipeline/:id`)
*Implemented on `/radar` and `/pipeline`:* Option A `Interest List` folded into [RadarPage.tsx](file:///d:/Tailored/frontend/src/pages/RadarPage.tsx) with Atelier V2 floating `--paper` panels and clean `ul.t-bullets` horizontal dashes; unified Direct Email + External Portal tracking enabled across [PipelinePage.tsx](file:///d:/Tailored/frontend/src/pages/PipelinePage.tsx), [pipelineStorage.ts](file:///d:/Tailored/frontend/src/services/pipelineStorage.ts), and backend [pipeline_service.py](file:///d:/Tailored/backend/app/pipeline/pipeline_service.py).
*Remaining targets in Phase 2 (`/cvs`, `/jobs/:id`, `/pipeline/:id`):*
- Move outer ground from muddy `--chalk` (`#E5E0DA`) onto clean `--paper` (`#F5F3EF`), elevating active cards, inspectors, and Kanban cards on borderless crisp `white` (`box-shadow` separation instead of `1px` gray boxes).
- Replace native `<select>` dropdowns, rectangular checkboxes, and `1px` outlined filter tags with sliding segmented switches (`.t-atelier-seg` light/dark variants), borderless tonal pills, and custom listbox popovers.
- Purge decorative red `▼` notches from `.t-eyebrow` section headers, neutral chips (`.t-chip--notch` like `ALL SAVED` or neutral skills), and icons; apply green `▲` (`.t-signal-up`) strictly on matched strengths / strong advantages and red `▼` (`.t-signal-down`) strictly on missing gaps / low-fit drawbacks.
- Convert UI labels and action buttons (`Tailor`, `Open Studio`, `Full Overlay`, `Save`, stage actions) from uppercase monospace to sentence-case `IBM Plex Sans`, keeping `IBM Plex Mono` strictly for fit scores, credit costs, dates, and counts.
- Add smooth row-switch cross-fades and animated `FitDial` / `MeasureRulerBar` transitions when changing active jobs or Kanban views; eliminate redundant multi-sentence bloat where a single crisp line + fit signal tells the story.
- For `/pipeline` Board lanes, `/jobs/:id`, and `/applications/:id`, consider using rich `--ink` / `--dye` header or summary anchor bands with subtle asymmetric curves so each hub has visual weight matching Brand Book Ch. 03 ratios.

### Phase 3 — Workspace Hubs & Account Management (`/dashboard` **Implemented**, `/profile`, `/plans`, `/account`, `/notifications`)
- **`/dashboard` ([DashboardPage.tsx](file:///d:/Tailored/frontend/src/pages/DashboardPage.tsx)) — Implemented:** Replaced the constrained `.t-page-fluid` multi-box grid with full-width `.t-dash-shell` + `.t-dash-stage` (`<AtelierFrenchCurveBackdrop />`) over continuous `--ink`, `.t-workspace-frame--dark` curved sidebar separation, single-line pattern-free `.t-dash-bar` KPI strip, two full-height floating `--paper` surfaces (`Today's Top Matches` with integrated `.t-dash-ingest`, single-CTA 3-stop rows & live `Selected Fit:` strip; `Continue Drafting` & `Needs Your Action` with aligned CRM baseline), `ArrowUp`/`ArrowDown`/`Space` row navigation, and semantic `▲` green / `▼` red arrows only.
- On `/profile`: keep the 3-column Master Vault ergonomics while stripping inner wireframe boxes and upgrading section switches/inputs to `.t-atelier-inline-input` tonal styling.
- On `/account` & `/plans`: replace all native `<select>` controls (`Default Home Route`, `Tailor Intensity`, `Digest Cadence`) with custom borderless listboxes, widen the Danger Zone `"DELETE"` confirmation input so placeholder text never clips, and keep RTL/Cozy-Compact toggles borderless and sentence-case.

### Phase 4 — Public, Onboarding & System Flows (`/`, `/explore`, `/login`, `/register`, `/onboarding`, `/credits-gate`)
- Standardize forms, plan comparison packs, onboarding steppers, and modal gates on borderless tonal inputs, sentence-case `IBM Plex Sans` buttons (keeping Brand diagonal armhole `0 12px 0 12px` CTAs), and shadow-lifted cards.
- Reserve `AtelierFrenchCurveBackdrop` for hero / studio / empty-state focal canvases (`opacity` kept restrained so legibility stays dominant), keeping decorative red downward notches off neutral UI chrome.

---

## Per-Page Definition of Done (Checklist Before Sign-Off)

For every page upgraded next, verify all 8 gates:
1. **Zero Windows XP Chrome:** No unnecessary `1px` wireframe borders around panels, cards, receipts, chips, or composer boxes; zero native OS `<select>` menus.
2. **Layer Separation:** Solid opaque navigation chrome (no wallpaper inside nav bars), clear tonal hierarchy (`--ink` canvas vs `--paper` / `white` elevated cards), and clean margins around detached sidecars.
3. **Typography Discipline:** `Fraunces` for headings/editorial titles, sentence-case `IBM Plex Sans` for interactive UI controls, and `IBM Plex Mono` strictly for numeric readouts, dates, codes, and credits.
4. **Semantic Directional Arrows (`▲` / `▼`):** Red `▼` (`.t-signal-down`) appears ONLY on downsides, gaps, or low-fit warnings; green `▲` (`.t-signal-up`) appears on advantages, matched wins, and strong-fit highlights; zero decorative red `▼` on neutral buttons, chips, eyebrows, or headers.
5. **Motion & Responsiveness:** Smooth transitions on segmented tabs, popovers, hover actions, and selection changes (`cubic-bezier(0.22, 1, 0.36, 1)`).
6. **Tight Copy & Zero Pointless Scroll:** Remove redundant label strips and boilerplate explanations; verify `1440×900` initial viewport fits primary content cleanly without forced page scroll.
7. **Strict Brand Token Integrity:** `0` CSS gradients, `0` raw hex literals outside [brand.css](file:///d:/Tailored/frontend/src/styles/brand.css), `0` banned fonts, `0` emojis.
8. **Build, Lint & Chrome Verification:** `npm run build` (`tsc -b && vite build`) and `npm run lint` (`oxlint`) exit `0` with `0` errors, plus live Chrome inspection (`1440×900`, `0` JS console errors, `0` failed network requests) confirmed visually via screenshot review.
