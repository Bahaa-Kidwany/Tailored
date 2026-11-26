# 11 — Saved CVs, Base Templates & Version Archive (`/cvs`)

**Route:** `/cvs`  
**Implementation Status:** Currently merged inside `AtelierInterestAndCvsPage.tsx` — **Now Dedicated Calm Document Library & Version Diff Inspector**  
**Primary User Goal:** Manage Canonical Master CVs per persona, browse/search tailored CV archives, inspect diffs against baseline or version history (`v1..vN`) inside an adjacent preview, and download ATS PDF / `.tex` files in `1` click without opening the Studio.  
**Entry Points:** Global Sidebar (`G` then `V`), Dashboard, Studio top menu.  
**Exit Destinations:** `/studio?doc_id=...`, `/profile`, `DispatchApplicationModal`.  
**Credit Model Impact:** Viewing, downloading, comparing versions, and opening/editing existing CVs are **0 Credits**; creating a brand-new tailored CV for an untailored job displays `· 1 cr`.

---

## 1. UX Reference Benchmarks & Ergonomic Rationale

| Reference | Pattern Adopted | Ergonomic Benefit for Tailored |
| :--- | :--- | :--- |
| **Figma Browser & Overleaf** | Clear separation of **Master Base Templates** vs **Tailored Snapshots** + `Table ↔ Grid` view parity | Prevents candidates from mixing up reusable persona templates with one-off job applications. |
| **Google Docs Version History** | Adjacent **Preview + Diff Inspector (`38%`)** with `[Paper | Diff vs. Base | .tex]` tabs | Inspecting what changed for Swvl vs. Noon takes `1` click without navigating to Studio. |

---

## 2. Desktop Layout Architecture & ASCII Wireframe (`1440px`)

```
+---------------------------------------------------------------------------------------------------+
| GLOBAL SHELL (Left Nav 212px) | SAVED CVS & ARCHIVE (/cvs, flex-1)                                |
|-------------------------------|-------------------------------------------------------------------|
|                               | LIBRARY TOOLBAR (56px, Sticky)                                    |
|                               | Saved CVs & Templates    [🔍 Search...]   [Persona: All ▾]        |
|                               | View: [● Table] [Grid]   [+ Upload .tex/.pdf Base]                |
|                               |-------------------------------------------------------------------|
|                               | CANONICAL BASE TEMPLATES (Slim Collapsible Top Strip — 0 Credits) |
|                               | [★ Senior AI Engineer Base · +20/+966 · [Open Studio] [↓ PDF]]    |
|                               | [  Data Scientist Base · +20 · [Open Studio] [↓ PDF]]            |
|                               |-------------------------------------------------------------------|
|                               | TAILORED ARCHIVE (Resizable Split: 62% List / 38% Preview)        |
|                               |                                                                   |
|                               | DOCUMENT LIST (62%, flex-1)        | RIGHT PREVIEW & DIFF (38%)   |
|                               |------------------------------------|------------------------------|
|                               | [●] Swvl · Lead Data Scientist     | Swvl — Lead Data Scientist   |
|                               |     AI Track (+20) · 94% · v3 · OK | Draft v3 · 1-Page PDF OK     |
|                               |     Hover: [Open] [↓ PDF]          |------------------------------|
|                               |------------------------------------| [Open in Studio (0 cr)]      |
|                               | [ ] Noon · Senior ML Engineer      | [↓ PDF]  [↓ .tex]  [Fork]    |
|                               |     AI Track (+966) · Dispatched 🔒|------------------------------|
|                               |------------------------------------| [Paper | Diff vs Base | .tex]|
|                               | [ ] Fawry · Product Data Analyst   | Version: [v3 Current ▾]      |
|                               |     Data Track (+20) · Page 2 ⚠    |                              |
|                               |                                    | Scrollable live preview or   |
|                               |                                    | surgical diff inspection...  |
+-------------------------------+------------------------------------+------------------------------+
```

---

## 3. Eye-Scan Path & Anti-Saccade Map

1. **Fixation 1 (Slim Base Templates Strip):** Clearly separates eternal Persona Templates (`0 cr`) from job-specific drafts below.
2. **Fixation 2 (Left Quiet Archive Rows):** Clean 2-line scannable telemetry (`Company · Role` + `Persona/Phone · Version/Status`), with `[↓ PDF]` and `[Open]` surfacing cleanly on hover without cluttering every row.
3. **Fixation 3 (Adjacent Right Inspector):** Click any document to toggle between `Live Paper`, `Diff vs. Base`, and `.tex` or download immediately.

---

## 4. Proximity & Click-Depth Budget

| User Intent | Click / Keystroke Depth | Spatial Location |
| :--- | :--- | :--- |
| **Download compiled PDF or `.tex`** | `1` click (`[↓ PDF]` / `[↓ .tex]`) | Row hover OR Right Inspector Header |
| **Compare tailored edits against Base CV** | `1` click (`[Diff vs Base]`) | Top tab inside Right Inspector |
| **Open CV in Studio (`0` credits)** | `1` click (`[Open in Studio]`) or `Enter` | Right Inspector Header |
| **Fork a dispatched immutable CV** | `1` click (`[Fork]`) | Right Inspector Header (clones safely for reuse) |

---

## 5. Detailed Zone-by-Zone Component & Interaction Spec

- **Immutable Dispatched Snapshot Protection (`🔒 Dispatched`):** Sent CVs locked by `DispatchApplicationModal` cannot be silently overwritten; `[Fork]` spins up an editable draft copy cleanly.
- **Page-Budget & Compile Alerts (`⚠ Page 2`):** Highlights overflows inline with 1-click `[Fix in Studio]` jump to auto-condense.

---

## 6. Interactivity, Adjustability & Keyboard Shortcuts

- **Resizable Split:** `62% / 38%` (`340px–540px`), double-click resets, persisted in `localStorage`.
- **View Switch:** `[Table]` (default calm scan) vs. `[Grid]` visual thumbnails.
- **Keyboard:** `J`/`K` step items, `Enter` open in Studio, `D` download PDF, `Space` toggle preview pane.

---

## 7. State Matrix & Edge Cases

| State | Behavior |
| :--- | :--- |
| **No Tailored CVs Yet** | Base Templates remain usable right above calm prompt: *"No tailored CVs yet — pair a base template with any job from Radar or Interest List."* + `[Explore Radar]`. |
| **Legacy `.tex` Without Compiled PDF** | On-demand PDF compile triggers cleanly on `[↓ PDF]` click without blocking user. |

---

## 8. Frontend UI Implementation Contract

- **Suggested Components:** `SavedCvsArchivePage`, `BaseTemplatesStrip`, `QuietCvArchiveList`, `CvPreviewAndDiffInspector`.
- **State:** `docs: CvFitSummary[]`, `selectedDocId`, `selectedDocDetail`, `viewMode: 'table' | 'grid'`, `previewTab: 'paper' | 'diff' | 'tex'`.
- **Backend Hooks:**
  - `GET /api/v1/cv-fit`, `GET /api/v1/cv-fit/{id}`, `GET /api/v1/cv-fit/{id}/download/{kind}` (`backend/app/api/routes/cv_fit.py`)
  - `POST /api/v1/cv-fit/{id}/fork` `[New Endpoint Needed]`
- **UX Acceptance Criteria:**
  1. Dispatched CVs stay immutable while offering 1-click `[Fork]`.
  2. List rows keep strictly 2 quiet lines; diff/version preview loads adjacently with zero page jumps.
