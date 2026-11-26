# Tailored — Global Atelier UX & UI Workflow Specification
**Version:** 5.0.0  
**Design System:** Tactile Non-AI Atelier (Organic Grain + Deep Botanical/Espresso/Ink Contrast • Zero Neon/AI-Blue)  
**Routing Architecture:** Dedicated History API URL Paths (`/`, `/login`, `/register`, `/onboarding`, `/trial`, `/studio`, `/radar`, `/interest`, `/pipeline`, `/profile`, `/account`)  
**Target Scope:** End-to-End Frontend Architecture & Backend Wiring (`FastAPI` + `React` / `TypeScript`)

---

## 1. Global Visual Identity & Ergonomic Layout System

### 1.1 Escaping Generic AI Aesthetics
To ensure the interface looks crafted and alive rather than a default AI-generated template:
- **Zero Default Google Fonts / AI Blue**: Move away from generic pastel blue fills (`#f0f4f8`) and flat cream (`#f4f3ef`). Self-host distinct foundry typography (`Satoshi`, `General Sans`, `Switzer`, `Zodiak`, `IBM Plex Mono`) while keeping crisp serif (`Latin Modern Roman` / `Source Serif 4`) strictly on the `.tex` paper preview.
- **Atmospheric Depth & Organic Grain**: Replace flat cream canvas fills with layered radial ambient lighting + subtle fractal grain texture so foreground cards and the floating CV sheet sit on a tactile desk.
- **Soft Rounded Containers & Dynamic Life**: Modern soft corners (`16px–20px` outer panes, `12px–14px` cards), cubic-bezier collapse/expand transitions, subtle hover elevation, pulsing live assistant indicators, and ink-highlight flashes when edits commit to the CV.

### 1.2 Independent Pane Ergonomics
- **Cross-Site Navigation (`AtelierSidebar.tsx`)**: Used across workspace discovery/CRM pages (`/radar`, `/interest`, `/pipeline`, `/profile`, `/account`) with a left-anchored Persona Switcher.
- **Focused Studio Isolation (`/studio`)**: CV Studio hides cross-site clutter behind a single compact exit button (`←`) so the left rail manages **CV Studio options only** and the entire screen serves document editing.

---

## 2. Complete Dedicated-Path Page Architecture

### Page 1: Command Center Landing (`/`) — `LandingPage.tsx`
- **UX Purpose**: Immediate value proposition & frictionless omni-command ingestion for guests or returning candidates.
- **UI**: Obsidian Forest backdrop (`#0d1513`), `Newsreader` headline *"Invisible Discovery. Absolute Caliber."*, translucent Command Dock (`bg-[#131917]/95`), typewriter hints, `+` CV upload button (`ProfileAPI.parseLatex`), Nordic Slate-Blue secondary highlights, and interactive 3D Cover Flow.
- **Backend Wiring**: URL pastes trigger `JobsAPI.ingestJobFromUrl`; text pastes trigger `JobsAPI.extractJobFromDescription`; role queries navigate into `/radar` (`JobsAPI.listJobs`); file uploads trigger `ProfileAPI.parseLatex`.

### Page 2: Access Atelier Authentication (`/login` & `/register`) — `AuthPage.tsx`
- **UX Purpose**: Dedicated Sign In (`/login`) and Account Creation (`/register`) routes that stay synchronized with the browser path when toggled.
- **UI**: Obsidian Forest backdrop framing an Alabaster plinth card (`rounded-[2.25rem]`) with Slate-Blue mode tabs, OAuth triggers, and `#142e23` CTA.

### Page 3: Sequential Onboarding Wizard (`/onboarding`) — `AtelierOnboardingWizard.tsx`
- **UX Purpose**: 6-step progressive Master Profile builder culminating cleanly into `/trial`.
- **UI**: Standalone full-screen Obsidian Forest frame + Alabaster step plinth with 01–06 top step tabs.
- **Backend Wiring**: `.tex` dropzone parses via `ProfileAPI.parseLatex`; completion saves via `ProfileAPI.createProfile` / `ProfileAPI.updateProfile` and advances to `/trial`.

### Page 4: Pro Trial Pass (`/trial`) — `FreeTrialGateModal.tsx`
- **UX Purpose**: Transparent complimentary 30-day Pro trial overview with clear free baseline continuation path to `/studio`.
- **UI**: Crisp Alabaster card with Slate-Blue membership summary (`#f0f4f8` / `#243b53`), itemized Pro pass benefits in Soft Sage, and 0-commitment notice (zero gold).

### Page 5: CV Studio Workbench (`/studio`) — `CVStudioWorkbench.tsx`
- **UX Purpose**: Living, split-pane document editing studio separated into **3 drag-adjustable, independently scrollable soft-rounded panes** (`col-resize` dividers with min/max clamping so each pane stays ergonomic):
  1. **Collapsible Left Studio Options Panel (`235px–390px`, collapses to `0px` with floating reopen pill)**:
     - Handles **CV Studio controls only** (compact `←` exit icon replaces cross-site nav).
     - Left-anchored Persona & Regional Phone (`+20` / `+966` / `+971`) switcher, Target Job selector, Tailoring Intensity (`Surgical` / `Metrics+` / `Executive`), live `.tex` Section Visibility toggles (`Profile`, `Stack Sub-lines`, `Projects`, `Certificates`, `Languages`), and exports (`↓ .tex`, `↓ PDF`, `✉ Dispatch Application`).
  2. **Center Document Stage (`min-width: 420px`, Hero Physical CV Paper + Independent Scrollbar)**:
     - Elevates the **CV Preview as the Main Character** rather than blending into the UI frame: set on a recessed inspection stage with rich multi-layered ambient shadows behind the paper sheet (`box-shadow` depth + crisp paper rim), smooth vertical scrolling through complete `cv(1)(1).tex` sections (`Profile`, multi-role `Experience` + `[Role Summary]` + bold leads + `◦ Stack:` sub-bullets, `Projects`, `Technical Skills`, `Education` + Graduation Project, `Certificates`, `Languages`), interactive zoom control (`85%` / `100%` / `110%`), page telemetry pill (`Page 1 of 1 · ATS Ready`), view switch (`Standard .tex` / `Surgical Diffs` / `Raw .tex`), and subtle hover action (`Ask AI`) on bullets that links straight into the assistant chat.
  3. **Right Smart Assistant Chatbot Pane (`300px–480px`, Separate Scrollbar Chat Stream)**:
     - Styled dynamically as a conversational AI writing coach with a live status orb header, fixed bottom composer + quick-steer chips, and an independently scrollable chat history.
     - **Structured Edit Instruction Bubbles**: Instead of generic metric tiles, each coaching turn renders:
       1. **Context** (target section + JD requirement rationale),
       2. **Current Version** (quoted baseline line on the CV, clicking scrolls/pulses that line on the paper),
       3. **Suggested Rewrite** (highlighted replacement preview), and
       4. **Interactive 3-Choice Bar**: **`Proceed`** (applies edit live to the CV with a highlight sweep animation and steps forward), **`Decline`** (dismisses and preserves baseline), or **`Suggest something else`** (opens an inline steer prompt / focuses chat so the assistant generates an alternative rewrite in real time).
- **Backend Wiring**: `CvFitAPI.tailorCv`, `CvFitAPI.listCvFits`, `CvFitAPI.downloadArtifact`, `JobsAPI.ingestJobFromUrl`, `JobsAPI.extractJobFromDescription`.

### Page 6: Dispatch Application Modal (inside `/studio`, `/radar`, `/interest`, `/pipeline`) — `DispatchApplicationModal.tsx`
- **UX Purpose**: Final-mile email outreach to hiring managers/recruiters.
- **UI**: Alabaster modal with Nordic Slate-Blue protocol pill, auto-generated cover letter body (`CoverLetterAPI.generateCoverLetter`), `.txt` cover letter download, verified ATS PDF card, and `Gmail Web` / `mailto:` / `Clipboard` dispatch triggers.
- **Backend Wiring**: `CoverLetterAPI.generateCoverLetter`, `PipelineStorage.addOrUpdateJob`, `PipelineStorage.updateStatus(id, 'applied')`.

### Page 7: Radar Feed & Job Discovery (`/radar`) — `AtelierRadarPage.tsx`
- **UX Purpose**: Ranked opportunity scanner inside `<AtelierSidebar />` + Warm Stone canvas.
- **UI**: Filter toolbar (`All Sources`, `Work Mode`, `Min Fit %`, `[ Live Sweep ]`), 5/7 master-detail split, Nordic Slate-Blue matched requirement matrix + Soft Terracotta skill gaps.
- **Backend Wiring**: `JobsAPI.listJobs`, `JobsAPI.triggerAutoSearch`, `isEligibleForPipeline(job)` rule distinguishing standard external links vs direct Recruiter Posts.

### Page 8: Interest List & Saved CVs Archive (`/interest`) — `AtelierInterestAndCvsPage.tsx`
- **UX Purpose**: Manage pasted/saved opportunities and generated `.pdf`/`.tex` ATS document library.
- **UI**: `<AtelierSidebar />`, Warm Stone canvas, top URL/JD ingestion strip, sub-tabs (`Interest List` vs `Saved CVs`), Nordic Slate-Blue `.tex` download / telemetry tags and Soft Terracotta remove action.

### Page 9: Application Pipeline & Outreach Hub (`/pipeline`) — `AtelierPipelinePage.tsx`
- **UX Purpose**: Kanban/list CRM across `saved` → `in_process` → `applied` → `interview` → `archived`.
- **UI**: `<AtelierSidebar />`, alternating Slate-Blue & Sage summary counters, stage filter tabs, inline recruiter email editor, ATS readiness badges, and `[ Dispatch Outreach ]`.

### Page 10: Master Profile (`/profile`) & Plans/Account (`/account`) — `AtelierProfilePage.tsx`, `AtelierAccountAndPlansPage.tsx`
- **UX Purpose**: Edit multi-career personas, regional phone numbers (`+20` / `+966` / `+971`), mobility, skill categories, experience, `.tex` upload, subscription tiers, and security settings under unified URL paths.
