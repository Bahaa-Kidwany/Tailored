# 10 — Interest List & External Job Ingestion Hub (`/interest`)

**Route:** `/interest`  
**Implementation Status:** Currently merged with Saved CVs in `AtelierInterestAndCvsPage.tsx` — **Now Dedicated Calm Triage & Ingestion Queue** (Saved CVs split to `/cvs` spec `11`)  
**Primary User Goal:** Capture external job links, screenshots (`Ctrl+V`), or raw job descriptions in one clean drop bar, review saved opportunities with zero button walls, and launch tailoring or outreach in `1` click.  
**Entry Points:** Global Sidebar (`G` then `I`), saving from `/radar` or `/jobs/:id`, Studio Dual-Write ingestion.  
**Exit Destinations:** `/studio`, `/cover-letters`, `/jobs/:id`, `/pipeline`, `DispatchApplicationModal`.  
**Credit Model Impact:** Ingesting & scoring fit is **100% Free**; tailoring triggers stamp `· 1 cr` (or `Open Draft · 0 cr` if unlocked).

---

## 1. UX Reference Benchmarks & Ergonomic Rationale

| Reference | Pattern Adopted | Ergonomic Benefit for Tailored |
| :--- | :--- | :--- |
| **Readwise Reader & Raindrop** | Top Multi-Modal Capture Bar + Calm 2-line Queue + Toggleable Quick-Peek (`Spacebar`) | Eliminates multi-button clutter on every saved card while keeping full JD preview 1 keystroke away. |
| **Linear Backlog** | Clean checkbox multi-select (`Shift+Click`) + Floating Batch Bar | Batch move eligible recruiter posts or archive stale jobs in seconds. |

---

## 2. Desktop Layout Architecture & ASCII Wireframe (`1440px`)

```
+---------------------------------------------------------------------------------------------------+
| GLOBAL SHELL (Left Nav 212px) | INTEREST LIST (/interest, flex-1)                                 |
|-------------------------------|-------------------------------------------------------------------|
|                               | TOP MULTI-MODAL INGESTION BAR (Sticky, 56px)                      |
|                               | [🔗 Paste URL, raw JD, or Ctrl+V screenshot to add & score... [Add]|
|                               |-------------------------------------------------------------------|
|                               | QUIET FILTER BAR (44px)                                           |
|                               | [All (7)] [Needs Tailor (4)] [CV Ready (2)] [Direct Email ✉ (3)]  |
|                               | [🔍 Search saved...]                                              |
|                               |-------------------------------------------------------------------|
|                               | RESIZABLE QUEUE + QUICK-PEEK SPLIT (62% / 38% when Peek open)     |
|                               |                                                                   |
|                               | SAVED QUEUE (62%, flex-1)           | QUICK-PEEK INSPECTOR (38%)  |
|                               |-------------------------------------|-----------------------------|
|                               | [ ] Swvl — Lead Data Scientist  94% | Swvl · Lead Data Scientist  |
|                               |     Cairo · studio_link · CV Ready  | Cairo (Hybrid) · Fit 94%    |
|                               |     Hover: [Open CV] [Cover Ltr] [×]|-----------------------------|
|                               |-------------------------------------| [Open in CV Studio (0 cr)]  |
|                               | [ ] TechStart — AI Engineer     88% | [Draft Cover Ltr · 1 cr]    |
|                               |     Remote · Recruiter ✉ · Untailor | [Full 5-D Breakdown ↗]      |
|                               |     Hover: [Tailor · 1cr] [✉] [×]   | [Apply on LinkedIn ↗]       |
|                               |-------------------------------------|-----------------------------|
|                               | [ ] Noon — Senior ML Engineer   89% | WHY IT MATCHES & SKILLS:    |
|                               |     Riyadh · studio_screenshot      | Matched: Python, PyTorch... |
|                               |                                     | Full Job Description...     |
+-------------------------------+-------------------------------------+-----------------------------+
```

---

## 3. Eye-Scan Path & Anti-Saccade Map

1. **Fixation 1 (Top Multi-Modal Ingestion Bar):** Single clear drop/paste box (`URL` / `JD` / `Ctrl+V Screenshot`).
2. **Fixation 2 (Left Queue — Calm 2-Line Rows):** Zero stacked 6-button rows per card; clean title/fit on Line 1, source/readiness status on Line 2, with hover/inspector actions nearby.
3. **Fixation 3 (Adjacent Quick-Peek Inspector):** Opens right beside the selected row via click or `Spacebar` to show full actions (`Tailor`, `Cover Letter`, `Dispatch`, `Apply Externally`).

---

## 4. Proximity & Click-Depth Budget

| User Intent | Click / Keystroke Depth | Spatial Location |
| :--- | :--- | :--- |
| **Ingest job via screenshot / URL** | `Ctrl+V` anywhere OR paste + `Enter` | Top Capture Bar (Dual-Write SHA-256 dedup) |
| **Inspect saved opportunity details** | `1` click OR `Spacebar` | Opens adjacent Right Quick-Peek |
| **Tailor CV or Open Existing Draft** | `1` click | Row hover primary action OR Quick-Peek header |
| **Batch archive or promote eligible posts** | `Shift+Click` checkboxes + `1` click | Bottom Floating Batch Bar |

---

## 5. Detailed Zone-by-Zone Component & Interaction Spec

- **Multi-Modal Capture + SHA-256 Dedup:** Detects URLs (`ingest-url`), JDs (`extract-description`), or clipboard screenshots (`ingest-screenshot`). Duplicate links jump smoothly to the existing row and refresh fit score instead of creating clones.
- **Strict Eligibility Enforcement:** Standard LinkedIn/Wuzzuf postings expose `[Apply on LinkedIn/Wuzzuf ↗]`; only Recruiter Posts & Custom Extractions expose `[Move to Pipeline]` or `[Dispatch ✉]`.
- **Collapsible Quick-Peek:** Users can close Quick-Peek (`Esc`) for a 100% wide queue, or leave it open while stepping with `J`/`K`.

---

## 6. Interactivity, Adjustability & Keyboard Shortcuts

- **Resizable Split:** `62% / 38%` (`340px–520px` Quick-Peek), double-click resets, persisted in `localStorage`.
- **Keyboard:** `J`/`K` step items, `Space` toggle Quick-Peek, `T` tailor CV, `Backspace/Delete` remove with `5s` `[Undo]` toast, `Ctrl+V` ingest anywhere.

---

## 7. State Matrix & Edge Cases

| State | Behavior |
| :--- | :--- |
| **Empty Interest List** | *"No saved opportunities yet. Paste any job link, description, or screenshot above to score your fit for free."* + `[Focus Capture Bar]` + `[Browse Job Radar →]`. |
| **Partial Screenshot OCR** | Saves extracted Title/Company with inline prompt inside Quick-Peek: `[Paste missing description text to refine score]`. |

---

## 8. Frontend UI Implementation Contract

- **Suggested Components:** `InterestListPage`, `MultiModalCaptureBar`, `QuietInterestRow`, `InterestQuickPeekDrawer`, `BatchTriageBar`.
- **State:** `interestItems: JobItem[]`, `selectedJobIds: Set<number>`, `activePeekId: number | null`, `filterTab`.
- **Backend Hooks:**
  - `POST /api/v1/jobs/ingest-url`, `POST /api/v1/jobs/extract-description` (`backend/app/api/routes/jobs.py`)
  - `POST /api/v1/jobs/ingest-screenshot` & `GET/POST/DELETE /api/v1/interest` `[New Endpoints Needed]`
- **UX Acceptance Criteria:**
  1. Cards keep strictly 2 clean text lines with hover/peek actions (zero button walls).
  2. `Ctrl+V` anywhere ingests URLs/screenshots cleanly with SHA-256 duplicate protection.
  3. Removing items provides instant optimistic `[Undo]` safety.
