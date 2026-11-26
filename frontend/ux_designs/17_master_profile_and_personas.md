# 17 — Master Profile & Career Personas Hub (`/profile`)

**Route:** `/profile`  
**Implementation Status:** Implemented (`AtelierProfilePage.tsx`) — **Calm 2-Column Redesign (Removed 3rd-Column Outline Clutter + Added Shared vs. Persona Scope Clarity & Safe CV Merge Preview)**  
**Primary User Goal:** Maintain the verified Master Profile ground truth cleanly—editing Career Personas, Regional Phones (`+20`/`+966`/`+971`), Skills, Experience, and Education inside a calm 2-column Linear-style layout, with on-demand CV preview and safe merge-diff imports.  
**Entry Points:** Global Sidebar (`Master Profile`), Identity Switcher Drawer (`[Edit Master Profile →]`), Dashboard setup prompt.  
**Exit Destinations:** `/studio`, `/radar`, `/cvs`.  
**Credit Model Impact:** **100% Free** (editing Master Profile, duplicating personas, parsing CV updates, and re-scoring Radar cost `0` credits).

---

## 1. UX Reference Benchmarks & Ergonomic Rationale

| Reference | Pattern Adopted | Why It Eliminates Profile Clutter |
| :--- | :--- | :--- |
| **Linear Settings** | Calm **2-Column Workspace** (`210px` Inner Section Nav + `740px` Focused Editor) + on-demand `[Preview Base CV]` slide-over | Removes the distracting permanent 3rd column preview rail so users focus peacefully on editing facts. |
| **Notion & Git Merge** | Inline click-to-edit cards, `[Duplicate Persona]`, and **Field-by-Field CV Merge Preview** | Lets candidates fork new career tracks in `1` click and re-upload updated resumes without overwriting hand-polished bullets. |

---

## 2. Desktop Layout Architecture & ASCII Wireframe (`1440px`)

```
+---------------------------------------------------------------------------------------------------+
| GLOBAL SHELL (Left Nav 212px) | MASTER PROFILE (/profile, flex-1)                                 |
|-------------------------------|-------------------------------------------------------------------|
|                               | CALM HEADER & SCOPE BAR (56px, Sticky)                            |
|                               | Master Profile · Editing: [★ Senior AI Engineer (Primary) ▾]      |
|                               |                                         [👁 Preview Base CV]      |
|                               |-------------------------------------------------------------------|
|                               | CALM 2-COLUMN WORKSPACE (Zero Permanent 3rd Column)               |
|                               |                                                                   |
|                               | INNER SECTION NAV (210px) | FOCUSED EDITOR COLUMN (max-width: 740px)|
|                               |---------------------------|---------------------------------------|
|                               | PERSONA-SCOPED:           |                                       |
|                               | • Career Personas         | (Active Section: Career Personas)     |
|                               | • Skills Taxonomy         | +-----------------------------------+ |
|                               | • Work Experience         | | ★ Senior AI Engineer (Primary)    | |
|                               | • Featured Projects       | |   7 yrs · Senior · 14 bullets     | |
|                               | • Certifications          | |   [Set Active] [Duplicate] [Edit] | |
|                               |                           | +-----------------------------------+ |
|                               | GLOBAL (SHARED):          | |   Data Scientist Track            | |
|                               | • Identity & Links        | |   5 yrs · Senior · 11 bullets     | |
|                               | • Regional Phones         | |   [Make Primary] [Duplicate] [Del]| |
|                               | • Locations & Mode        | +-----------------------------------+ |
|                               | • Education & Langs       | | [+ Create New Career Persona]     | |
|                               | • Custom Sections         | +-----------------------------------+ |
|                               |                           |                                       |
|                               | IMPORT / SYNC:            | (When editing Experience / Skills:    |
|                               | • Upload / Merge CV       |  calm single-column blocks with drag  |
|                               |   (.tex / .pdf / .docx)   |  handles ↕ & inline [Role Summary] /  |
|                               |                           |  [Stack: ...] syntax helper chips)    |
+-------------------------------+---------------------------+---------------------------------------+
| FLOATING STICKY UNSAVED BAR (Appears ONLY when dirty):                                            |
| "Unsaved edits in Work Experience"                        [Discard]   [Save Profile (Cmd+S)]      |
+---------------------------------------------------------------------------------------------------+
```

---

## 3. Eye-Scan Path & Anti-Saccade Map

1. **Fixation 1 (Top Scope Pill):** Confirms which Persona is active and whether the current section is `Persona-Scoped` or `Global (Shared)`.
2. **Fixation 2 (Left Inner Nav → Single-Column `740px` Editor):** Natural vertical scan down one clean reading column with generous outer margin.
3. **Fixation 3 (On-Demand Preview Drawer):** Clicking `[👁 Preview Base CV]` slides in a clean ATS preview over the right edge only when explicitly requested.

---

## 4. Proximity & Click-Depth Budget

| User Intent | Click / Keystroke Depth | Spatial Location |
| :--- | :--- | :--- |
| **Duplicate a persona into a new career track** | `1` click (`[Duplicate]`) | Directly on persona card |
| **Switch between Persona-Scoped & Shared sections** | `1` click | Sticky Inner Section Nav (`210px`) |
| **Verify how facts look as an ATS CV** | `1` click (`[👁 Preview Base CV]`) | Top-right header → calm slide-over drawer |
| **Add regional phone (`+20`, `+966`, `+971`)** | `1` click (`[+ Add Number]`) | `Regional Phones` section |
| **Save all changes from anywhere** | `Cmd/Ctrl + S` (`1` chord) or click Floating Save Bar | Sticky bottom bar (only appears when dirty) |

---

## 5. Detailed Zone-by-Zone Component & Interaction Spec

- **Shared vs. Persona-Scoped Clarity:** Inner nav separates `Persona-Scoped` sections (show subtle persona tag) from `Global (Shared)` sections (Name, Phones, Education, Locations).
- **Safe CV Re-Upload Merge Modal:** Dropping a `.tex`/`.pdf`/`.docx` CV opens a **Field-by-Field Diff Preview** (`Current Profile` vs. `Newly Parsed CV`) with checkboxes per skill/role so existing hand-crafted bullets are never wiped accidentally.
- **Inline LaTeX Helper Pills:** Inside Work Experience, subtle `[+ Role Summary]` and `[+ Stack: ...]` buttons format special directives cleanly without forcing users to write LaTeX syntax.

---

## 6. Interactivity, Adjustability & Keyboard Shortcuts

- **Keyboard:** `Cmd/Ctrl + S` saves changes; `ArrowUp`/`ArrowDown` in Inner Nav steps sections; unsaved changes navigation guard protects edits (`[Save & Leave]` / `[Discard]` / `[Stay]`).

---

## 7. State Matrix & Edge Cases

| State | Behavior |
| :--- | :--- |
| **Unsaved Changes** | Floating bottom bar specifies modified section(s) with `[Discard]` and `[Save Profile]`. |
| **Deleting a Persona** | Prompts cleanly if linked to tailored CVs (*"3 historical CVs in /cvs remain safe — delete this persona?"*). Blocks deleting sole remaining persona. |
| **Save Success** | Toast confirms save + offers 1-click `[Re-Score Radar Jobs →]`. |

---

## 8. Frontend UI Implementation Contract

- **Suggested Components:** `MasterProfilePage`, `ProfileScopeHeader`, `ProfileSectionNav`, `PersonaManagerSection`, `RegionalContactsSection`, `SkillsTaxonomyEditor`, `ExperienceEditorSection`, `CvMergePreviewModal`, `BaseCvPreviewDrawer`, `DirtySaveBar`.
- **State:** `draftProfile`, `savedSnapshot`, `activeSection`, `editingPersonaId`, `isDirty`, `isPreviewDrawerOpen`, `parsedMergeCandidate`.
- **Backend Hooks:**
  - `GET/PUT /api/v1/profiles/{id}`, `POST /api/v1/profiles/{id}/personas`, `PATCH .../primary`, `POST /api/v1/profiles/parse-latex` (`backend/app/api/routes/profiles.py`)
  - `POST /api/v1/profiles/upload-resume` `[New Endpoint Needed for PDF/DOCX]`
- **UX Acceptance Criteria:**
  1. Calm 2-column layout with zero permanent 3rd column outline rail.
  2. Re-uploading a CV always presents selective field merge preview before updating data.
  3. Shared vs. Persona-Scoped fields are clearly grouped.
