# 21 — System Error, Offline, Maintenance & Legal Pages (`/404`, `/500`, `/maintenance`, `/offline`, `/privacy`, `/terms`)

**Routes:** `/404` (fallback wildcard), `/500`, `/maintenance`, `/offline` (banner + fallback page), `/privacy`, `/terms`  
**Implementation Status:** **Never Implemented** (Currently invalid paths silently redirect to `/` in `App.tsx`, masking errors; no Privacy/Terms routes exist despite links on Auth/Checkout)  
**Primary User Goal:** Recover calmly and honestly from broken routes, server outages, or offline disconnects without ever losing unsaved CV/profile edits—and read plain-English privacy/terms guarantees clearly without dense legal walls.  
**Entry Points:** Mistyped URLs, expired deep links, runtime error boundaries, network drop detection, Auth/Footer `[Privacy]` and `[Terms]` links.  
**Exit Destinations:** `/dashboard` (authenticated), `/` (guest), `[Retry Action]`, `Cmd/Ctrl + K` Command Palette.  
**Credit Model Impact:** System outages (`500` / compile failures) explicitly reassure users that **no credits are deducted on failed operations** (or are automatically refunded).

---

## 1. UX Reference Benchmarks & Ergonomic Rationale

| Reference | Pattern Adopted | Ergonomic Benefit for Tailored |
| :--- | :--- | :--- |
| **Tailored Brand Book (`06.10`) & Linear Errors** | Candid **first-person-plural voice** (*"We couldn't find..." / "This is on us — not you"*) + 1 clear recovery CTA + `Cmd+K` escape | Eliminates cold technical error codes (`ERR_404`) and reduces panic when an application deadline is near. |
| **Notion / Google Docs Offline Resilience** | Non-blocking **Persistent Offline Status Strip** preserving local editing & queuing server sync automatically | Candidates polishing CV bullets on unstable Wi-Fi never lose keystrokes or get trapped on an offline error wall. |
| **Stripe Docs & Legal Readability** | Sticky Left Table of Contents (`240px`) + `68ch` reading measure + top **Plain-English Candidate Guarantee Box** | Ensures users actually verify Tailored's *"Zero Recruiter Sharing / Zero Hallucination"* privacy promise before uploading sensitive CVs. |

---

## 2. Desktop Layout Architecture & ASCII Wireframes (`1440px`)

### Group A: System Recovery Pages (`/404`, `/500`, `/maintenance`)
```
+---------------------------------------------------------------------------------------------------+
| MINIMAL HEADER: [Tailored Mark]                                    [⌘K Jump Anywhere] [Dashboard] |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|                          +---------------------------------------------+                          |
|                          |  STATUS CODE / BADGE: 404 · Page Not Found  |                          |
|                          |                                             |                          |
|                          |  "We couldn't find that page."              |                          |
|                          |  The link may have moved or expired, but    |                          |
|                          |  your profile and saved drafts are safe.    |                          |
|                          |                                             |                          |
|                          |  QUICK RECOVERY:                            |                          |
|                          |  [ Return to Dashboard -> ]  (or Home '/')  |                          |
|                          |  [ Open Job Radar ]   [ Press ⌘K to Search ]|                          |
|                          +---------------------------------------------+                          |
|                                                                                                   |
|  500 SERVER ERROR VARIANT:                                                                        |
|                          +---------------------------------------------+                          |
|                          |  500 · Unexpected Error                     |                          |
|                          |  "Something broke on our end — not yours."  |                          |
|                          |  Any unsaved CV or profile edits are        |                          |
|                          |  preserved locally in your browser. Zero    |                          |
|                          |  credits were charged for this attempt.     |                          |
|                          |                                             |                          |
|                          |  [ Try Again ↻ ]   [ Export Local Backup ]  |                          |
|                          |  Reference ID: err_9f38a (Copy for support) |                          |
|                          +---------------------------------------------+                          |
+---------------------------------------------------------------------------------------------------+
```

### Group B: Offline Resilience Mode (Global Non-Blocking Banner + Fallback Route)
```
+---------------------------------------------------------------------------------------------------+
| TOP NON-BLOCKING OFFLINE STRIP (Appears smoothly without shifting/wiping active work)              |
| ● You're offline — CV edits, Pipeline & Profile changes are saving locally and will sync on       |
|   reconnect. (AI Coach & Live Scrapers paused until connection returns)   [Retry Connection ↻]    |
+---------------------------------------------------------------------------------------------------+
```

### Group C: Legal & Privacy Pages (`/privacy`, `/terms`)
```
+---------------------------------------------------------------------------------------------------+
| HEADER: [Tailored Mark]                                                 [← Back to Workspace / /] |
+---------------------------------------------------------------------------------------------------+
| 2-COLUMN READABLE DOCUMENTATION LAYOUT (Centered, max-width: 1080px)                              |
|                                                                                                   |
| STICKY LEFT TABLE OF CONTENTS (240px) | READING COLUMN (flex-1, max-width: 68ch)                  |
|---------------------------------------|-----------------------------------------------------------|
| PRIVACY POLICY                        | Privacy Policy · Last Updated: November 2026 [↓ Print/PDF]|
| 1. Plain-English Guarantee            |                                                           |
| 2. What CV & Profile Data We Collect  | +-------------------------------------------------------+ |
| 3. How AI Models Process Your CV      | | PLAIN-ENGLISH CANDIDATE GUARANTEE                     | |
| 4. Zero Recruiter Sharing Pledge      | | • We NEVER sell your CV or score you for recruiters.  | |
| 5. Credit & Payment Processing        | | • Your data is never used to train public AI models.  | |
| 6. Export & Deletion Rights           | | • Export or permanently delete all records in 1 click.| |
|                                       | +-------------------------------------------------------+ |
| Switch to: [Terms of Service ->]      |                                                           |
|                                       | 1. What CV & Profile Data We Collect                      |
|                                       | (Clean scannable sections with clear headings, lists,     |
|                                       |  and direct link to /account Data Export & Delete)        |
+---------------------------------------+-----------------------------------------------------------+
```

---

## 3. Eye-Scan Path & Anti-Saccade Map

1. **Error Pages (`/404`, `/500`):** Tight single-column vertical focus (`max-width: 520px`)—eyeline reads honest statement → safety reassurance (*"Drafts are safe, 0 credits charged"*) → primary recovery action.
2. **Legal Pages (`/privacy`, `/terms`):** Fixation 1 hits the top **Plain-English Candidate Guarantee** box; Fixation 2 uses the adjacent Sticky Left Table of Contents (`240px`) to jump directly to AI processing or deletion rights without hunting through legalese.

---

## 4. Proximity & Click-Depth Budget

| User Intent | Click / Keystroke Depth | Spatial Location |
| :--- | :--- | :--- |
| **Recover from mistyped URL (`/404`)** | `1` click (`[Return to Dashboard]`) or `Cmd+K` | Centered recovery card |
| **Retry failed operation or save local backup (`/500`)** | `1` click (`[Try Again ↻]` or `[Export Local Backup]`) | Centered error boundary card |
| **Jump to AI & Privacy section in `/privacy`** | `1` click on Sticky TOC link | Left column directly beside body copy |
| **Exercise export/deletion rights from `/privacy`** | `1` click deep link to `/account#privacy` | Embedded inside Section 6 of Privacy Policy |

---

## 5. Detailed Zone-by-Zone Component & Interaction Spec

### 5.1 Honest Error Boundary & Zero Data-Loss Guarantee (`/500`)
- React Error Boundary catches unexpected runtime crashes without turning the page blank.
- Automatically dumps unsaved Studio/Profile local drafts to `localStorage` and offers `[Export Local Backup JSON]` right inside the crash screen as an emergency escape hatch!

### 5.2 Offline & Maintenance Resilience
- Matches existing offline-resilient services (`jobsApi.ts`, `cvFitApi.ts`, `pipelineStorage.ts`):
  - **Working Offline:** Viewing cached Radar jobs, viewing saved CVs, editing Pipeline notes/stages, editing Master Profile drafts.
  - **Paused Until Online:** Live Apify/Wuzzuf scraping, AI Studio Coach streaming, PDF LaTeX server compilation, Payment checkouts (each button shows clear tooltip: *"Requires internet connection"* instead of failing mysteriously).
- **Scheduled Maintenance (`/maintenance`):** Displays clear expected duration + status updates link + safe read-only export trigger for local cached drafts.

### 5.3 Privacy & Terms Transparency (`/privacy`, `/terms`)
- Opens cleanly inside the current app shell (or modal/new tab from `/register` so registration inputs aren't wiped).
- Explicitly documents Tailored's core architectural rules: candidate-only focus, credit expiration (`never expire`), refund policy for failed compiles, and Paymob/Stripe payment tokenization (never storing raw card numbers on Tailored servers).

---

## 6. Interactivity, Adjustability & Keyboard Shortcuts

- **Legal Reading Comfort:** `68ch` optimal line width, clickable anchor headers, scroll-spy highlighting active section in Sticky TOC, `← Back` returns seamlessly to referring auth/checkout page.
- **Keyboard:** `Cmd/Ctrl + K` works even on `/404` so power users jump instantly anywhere; `R` retries on `/500` or `/maintenance`.

---

## 7. State Matrix & Edge Cases

| State | Behavior |
| :--- | :--- |
| **Unknown Route (Replacing silent `/` redirect in `App.tsx`)** | Renders `/404` page explicitly while preserving URL so user can spot and fix typos (e.g., `/studo` → smart suggestion: *"Did you mean `/studio`?"*). |
| **Connection Restored After Offline Edit** | Offline banner swaps cleanly for `3s` to `"Back online — syncing 2 queued changes..."` → `"✓ All changes synced"`. |
| **Local Storage Full or Blocked** | Graceful warning inside Offline Banner: *"Browser storage is restricted — export your draft before closing this tab."* |

---

## 8. Frontend UI Implementation Contract

- **Suggested Components:** `NotFoundPage`, `ServerErrorBoundary`, `MaintenancePage`, `OfflineStatusBanner`, `LegalDocumentLayout` (shared by `PrivacyPolicyPage` & `TermsOfServicePage`).
- **State:** `isOnline: boolean`, `pendingSyncQueueCount: number`, `errorBoundaryInfo: { message, refId }`, `activeTocSlug`.
- **Backend Hooks:**
  - `GET /api/v1/health` `[Optional Health/Maintenance Ping]`
  - Static versioned Markdown/JSON legal content bundle (`GET /api/v1/legal/{privacy|terms}` or client-bundled).
- **UX Acceptance Criteria:**
  1. Unknown routes render helpful `/404` with smart typo suggestions (`Did you mean /studio?`) instead of silently redirecting to `/`.
  2. Runtime errors (`/500`) reassure users that zero credits were lost and preserve local draft export.
  3. `/privacy` and `/terms` feature a plain-English summary, sticky TOC, and direct links from Auth and Checkout without wiping form inputs.
