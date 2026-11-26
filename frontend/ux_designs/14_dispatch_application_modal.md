# 14 — Dispatch Application & Email Outreach Modal (Overlay Workflow)

**Route / Trigger:** Centered Overlay Modal triggered from `/studio`, `/cover-letters`, `/radar` (Recruiter Posts), `/interest`, or `/pipeline`  
**Implementation Status:** Implemented (`DispatchApplicationModal.tsx`) — **Redesigned from 2-Column Form Zigzag to Superhuman Single-Flow Native Email Composer**  
**Primary User Goal:** Review recipient, subject, outreach pitch, regional phone, and attached PDF inside one natural top-to-bottom reading flow and dispatch via Gmail Web, Mail App, or Clipboard in `1` click—automatically advancing Pipeline state.  
**Entry Points:** `[✉ Dispatch Application]` in Studio/Cover Letters, `[✉ Send Email Application]` on eligible Recruiter Posts in Radar/Interest/Pipeline.  
**Exit Destinations:** Closes back to originating page (`Esc` or `[✕]`) with confirmation + `[Undo]` / `[View in Pipeline ↗]` toast.  
**Credit Model Impact:** **0 Credits** (uses already-unlocked CV/Cover Letter; optional `[✨ Draft AI Pitch · 1 cr]` chip appears only if no cover letter exists yet).

---

## 1. UX Reference Benchmarks & Ergonomic Rationale

| Reference | Pattern Adopted | Why It Replaces the 2-Column Modal |
| :--- | :--- | :--- |
| **Superhuman Compose** | Natural **Single-Column Vertical Email Envelope (`max-w: 720px`)** (`To / CC / Subject` → `Airy Message Body` → `Attachments` → `Send`) | Eliminates left-to-right eye zigzagging between separated inputs and message prose; mirrors how humans actually review an email before hitting Send. |
| **Attio Outreach** | Inline click-to-edit recipient + single unified `[Open in Gmail Web ↗ ▾]` split send trigger + automatic CRM stage logging | Reduces footer button clutter and removes manual pipeline tracking work. |

---

## 2. Desktop Layout Architecture & ASCII Wireframe (`1440px`)

```
+-------------------------------------------------------------------------------+
| OVERLAY MODAL (Single-Column Native Email Flow · max-width: 720px)       [✕]  |
|-------------------------------------------------------------------------------|
| CONTEXT STRIP (Compact 1-Line Header):                                        |
| ● Swvl · Lead Data Scientist · Cairo (Hybrid)      Phone in CV: [+20 EG ▾]    |
|-------------------------------------------------------------------------------|
| 1. ENVELOPE HEADER (Clean Inline Rows — Zero Form Boxes Clutter)              |
| To:      careers@swvl.com   (✓ Extracted from Swvl Post)     [+ CC Myself ✓]  |
| Subject: Application: Lead Data Scientist — Mostafa Ibrahim                   |
|-------------------------------------------------------------------------------|
| 2. EDITABLE OUTREACH MESSAGE (Airy Prose Canvas · 64ch comfort measure)       |
|                                                                               |
|   Dear Swvl Talent Acquisition Team,                                          |
|                                                                               |
|   I am writing to apply for the Lead Data Scientist position. In my recent    |
|   work architecting PyTorch & FastAPI pricing engines, I cut route dispatch   |
|   latency by 42% across 1,400 daily rides...                                  |
|                                                                               |
|   Sincerely,                                                                  |
|   Mostafa Ibrahim · +20 100 482 9102 · linkedin.com/in/mostafa-ai             |
|                                                                               |
|   Quiet Polish Chips (Directly beneath body):                                 |
|   [Shorter]   [Sharper Metrics]   [Add Notice Period]   [↺ Reset]             |
|-------------------------------------------------------------------------------|
| 3. VERIFIED ATTACHMENT STRIP (Horizontal Compact Bar)                         |
| [ 📄 Mostafa_CV_Swvl.pdf · 1-Page ATS ✓  [👁 Preview] [↓] ]                   |
| [ 📝 Cover_Letter_Swvl.txt               [Open CL Studio] [↓] ]               |
|-------------------------------------------------------------------------------|
| 4. CLEAN MODAL FOOTER (Sticky)                                                |
| [✓] Mark as "Applied" & freeze CV snapshot in Pipeline                        |
|                                                                               |
| [Cancel]               [🚀 Open in Gmail Web ↗ (Downloads PDF)  ▾]            |
|                         └─ Dropdown: [Default Mail App] · [Copy Full Email]   |
+-------------------------------------------------------------------------------+
```

---

## 3. Eye-Scan Path & Anti-Saccade Map

1. **Fixation 1 (Compact Envelope Header):** Single vertical skim checks `To` (`careers@swvl.com`), `Subject`, and regional phone (`+20 EG ▾`).
2. **Fixation 2 (Airy Message Body + 4 Polish Chips):** Eyes drop straight down along the `64ch` reading axis to scan/edit the outreach message.
3. **Fixation 3 (Attachment Strip → Primary Send Split Button):** Confirms `1-Page ATS ✓` PDF right above the single primary CTA (`[Open in Gmail Web ↗]`).
- **Anti-Saccade Rule:** Zero 2-column form splitting! Users never jump horizontally back and forth between left metadata cards and right textboxes.

---

## 4. Proximity & Click-Depth Budget

| User Intent | Click / Keystroke Depth | Spatial Location |
| :--- | :--- | :--- |
| **Send via Gmail Web (with PDF auto-downloaded)** | `1` click (`[🚀 Open in Gmail Web ↗]`) | Bottom-right primary split CTA |
| **Use Native Mail App or Copy Full Email** | `2` clicks (caret `▾` on split CTA) or `Cmd/Ctrl+Shift+C` | Directly attached to Send button |
| **Swap `+20` EG ↔ `+966` KSA phone in signature** | `1` click (`[+20 EG ▾]`) | Top context bar → updates signature text live |
| **Shorten or tighten pitch** | `1` click (`[Shorter]`) | Directly beneath message body |
| **Quick-preview attached PDF before sending** | `1` click (`[👁 Preview]`) | Inside compact attachment chip |

---

## 5. Detailed Zone-by-Zone Component & Interaction Spec

### 5.1 Inline Envelope & Regional Phone Swap
- Clicking `careers@swvl.com` or `Subject` lets user edit cleanly inline without switching modes.
- Switching `[+20 EG ▾]` to `[+966 KSA]` immediately updates the email signature phone and gently offers a 1-click `[Re-sync CV PDF with +966?]` pill if the attached CV used a different number.

### 5.2 Browser Bridge & Helpful Confirmation Toast
Clicking **`[🚀 Open in Gmail Web ↗]`** runs:
1. Auto-downloads `Mostafa_Ibrahim_CV_{Company}.pdf` into browser Downloads tray.
2. Copies full outreach body to clipboard as instant safety net.
3. Opens pre-populated Gmail Compose tab (`mail.google.com/mail/?view=cm&fs=1&to=...&su=...&body=...`).
4. Marks application `applied` in Pipeline (freezing CV/CL snapshot) and shows a clear confirmation toast: *"Gmail opened & marked Applied — drag the downloaded PDF from your browser downloads bar into Gmail."*

### 5.3 Pre-Send Guards
- **Missing Email Guard:** If `To` is empty, focuses inline `To` input cleanly with helper (*"Enter recruiter email to enable Gmail/Mail launch, or copy pitch for LinkedIn DM"*).
- **Unresolved Placeholder Guard:** Warns gently if `[Company]` or `{Role}` remains inside prose before launching external compose.

---

## 6. Interactivity, Adjustability & Keyboard Shortcuts

| Shortcut / Control | Behavior |
| :--- | :--- |
| `Esc` | Closes modal cleanly (prompts only if custom manual prose edits haven't been copied/sent). |
| `Cmd/Ctrl + Enter` | Executes Primary Dispatch (`Open in Gmail Web ↗`). |
| `Cmd/Ctrl + Shift + C` | Copies formatted `To + Subject + Body` to clipboard immediately. |

---

## 7. State Matrix & Edge Cases

| State | Behavior |
| :--- | :--- |
| **Standard Board Listing Opened from Studio** | Adapts gently for LinkedIn/Wuzzuf jobs: removes `To` email field, labels header *"External Board Application"*, and sets Primary CTA to `[Download PDF & Open LinkedIn Listing ↗]` + `[Copy Pitch for Application Form]`. |
| **No Cover Letter Drafted Yet** | Pre-fills a crisp 3-sentence executive pitch (`0 cr`) with one subtle `[✨ Generate Full AI Cover Letter · 1 cr]` chip beside `[Shorter]`. |
| **PDF Fetch Error** | Keeps email compose 100% functional; shows inline retry (`[Retry PDF Download]` or `[Copy .tex Source]`). |

---

## 8. Frontend UI Implementation Contract

- **Suggested Components:** `DispatchApplicationModal`, `SingleFlowEnvelopeHeader`, `OutreachProseCanvas`, `CompactAttachmentStrip`, `SplitDispatchFooter`.
- **State:** `toEmail`, `ccSelf`, `subject`, `bodyText`, `selectedPhoneCode`, `autoAdvancePipeline`, `isPdfPreviewOpen`.
- **Backend Hooks:**
  - `GET /api/v1/pipeline/{item_id}/outreach` & `PATCH /api/v1/pipeline/{item_id}` (`backend/app/api/routes/pipeline.py`)
  - `GET /api/v1/cv-fit/{doc_id}/download/pdf` (`backend/app/api/routes/cv_fit.py`)
  - `POST /api/v1/cover-letter` (`backend/app/api/routes/cover_letter.py`)
- **UX Acceptance Criteria:**
  1. Single-column `720px` reading flow top-to-bottom with zero horizontal form zigzagging.
  2. Swapping regional phone updates email signature immediately.
  3. Primary split button cleanly handles Gmail Web + Mailto + Copy All without footer clutter.
