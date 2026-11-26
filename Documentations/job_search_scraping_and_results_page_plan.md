# Technical Specification & Plan: Automated Job Search, Multi-Source Scraping & Dedicated Radar Results Page

## 1. Executive Summary

This plan outlines the architecture, UX, backend APIs, and scraping integration to bring **Job Searching, Finding, and Scraping** to life in **Tailored**.

The core requirement is a cohesive, non-overwhelming user journey:
1. **Automatic Search Ingestion**: Upon profile completion in the Quiz Funnel (or upon changing the active persona), job search queries are automatically derived and dispatched to fetch relevant opportunities from **LinkedIn** and **Wuzzuf**.
2. **Dedicated Results Page (Job Radar View)**: Instead of cluttering the landing/home page, searching automatically transitions the user to a dedicated **Job Radar Page** (`view === 'radar'`), keeping the home page focused on branding and initiation.
3. **Restrained, High-Value Match Badges**: Avoid overwhelming the user with visual noise. High-fit listings (e.g. $\ge 85\%$) display a single tasteful badge (`✨ High Match (92%)`), while medium matches display a clean neutral alignment percentage.
4. **Interactive Right Slide-Out Details Pane**: Clicking any job card slides out a comprehensive right pane showing the full job description, matched requirements, an **Apply** button (direct external link), and a preview **Tailor your CV** action (staged for Phase 3).

---

## 2. End-to-End User Flow Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        USER PROFILE QUIZ FUNNEL                        │
│  Candidate completes Master Profile (or selects Active Persona)        │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ Trigger automatic job search
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   DEDICATED JOB RADAR RESULTS PAGE                     │
│                                                                        │
│  Top Context Bar:                                                      │
│  "Targeting: Data Scientist in Cairo, Riyadh & Remote"                 │
│  Filter Bar: [Keyword Search] [Location Hubs] [Min Match: 80%+]        │
│                                                                        │
│  ┌────────────────────────────────────┐ ┌───────────────────────────┐  │
│  │           JOB CARDS FEED           │ │  RIGHT SLIDE-OUT PANE     │  │
│  │                                    │ │  (Opens on Card Click)    │  │
│  │  [Card 1] Swvl - Lead Data Sci     │ │                           │  │
│  │  • Cairo (Hybrid) • 2h ago         │ │  • Full Job Description   │  │
│  │  • [ ✨ High Match 94% ]           │ │  • Matched Key Skills     │  │
│  │                                    │ │  • Requirements & Perks   │  │
│  │  [Card 2] Noon - Senior ML Eng     │ │  • [ Apply on LinkedIn ]  │  │
│  │  • Riyadh (On-site) • 5h ago       │ │  • [ Tailor your CV (⏳) ]│  │
│  │  • [ ✨ High Match 89% ]           │ │                           │  │
│  │                                    │ │                           │  │
│  │  [Card 3] Datadog - Platform Eng   │ │                           │  │
│  │  • Remote • 1d ago                 │ │                           │  │
│  │  • [ 76% Match ]                   │ │                           │  │
│  └────────────────────────────────────┘ └───────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Dedicated Page Architecture vs. Home Page

The application will maintain two distinct top-level views:
1. **Home View (`view === 'home'`)**:
   - Editorial Hero Search bar with instant demo chips.
   - Active Persona Bar (displays candidate identity and regional routing).
   - Bento Grid showcase highlighting the 4 core pillars (Job Radar, Fit Matrix, CV Studio, Cover Letters).
   - Trigger to open the Quiz Funnel.
2. **Job Radar Results View (`view === 'radar'`)**:
   - Accessible via Header navigation ("Job Radar"), Hero search submit ("Match & Tailor"), or completion of the Quiz Funnel.
   - Dedicated clean toolbar with live active persona context, search keyword refinement, location filters (Cairo, Riyadh, Dubai, Remote), and match score threshold.
   - Dual-pane layout: responsive job list on the left, slide-out sticky detail pane on the right.

---

## 4. Backend Scraper Ingestion Engine & Endpoints

### 4.1. Ingestion Dispatcher (`backend/app/pipeline/job_search_service.py`)
- Integrates both **Wuzzuf** (direct HTTP scraping via `WuzzufScraperSource`) and **LinkedIn** (`ApifyLinkedInSource` with automatic fallback to structured mock fixtures if APIFY tokens are absent or rate-limited).
- Evaluates raw listings against the candidate's active persona using `JobEvaluator` (skill overlap, seniority alignment, location match).
- De-duplicates jobs using `canonical_hash` (company + title + location).
- Persists valid jobs to the `jobs` table in PostgreSQL / SQLite.

### 4.2. API Endpoints Contract (`backend/app/api/routes/jobs.py`)

| Method | Route | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/jobs/auto-search` | Automatically derives query from user profile ID & persona ID, fetches/scrapes jobs, computes fit scores, and saves to database |
| `GET` | `/api/v1/jobs` | Queries saved jobs with filters (`query`, `location`, `min_score`, `source`, `limit`, `skip`) |
| `GET` | `/api/v1/jobs/{job_id}` | Retrieves full job details, parsed skills, responsibilities, and evaluation breakdown |
| `POST` | `/api/v1/jobs/bookmark/{job_id}` | Toggles bookmark status for a job listing |

---

## 5. UI Design & UX Details (Non-Overwhelming Curation)

### 5.1. Restrained Badge & Match Labeling Logic
To avoid visual fatigue:
- **Score $\ge 85\%$**: Displays a single subtle emerald/gold pill: `✨ High Match (92%)`.
- **Score $70\% - 84\%$**: Displays a minimalist neutral score badge: `78% Fit`.
- **Score $< 70\%$**: No badge or subtle grey indicator.
- Never stack more than 1 primary label per job card. Badges for work mode (`Remote`, `Hybrid`) use low-contrast neutral pills.

### 5.2. Right Slide-Out Details Pane (`JobDetailPane.tsx`)
- Triggered by clicking any job card in the list.
- Features:
  - Header: Job title, Company name, Location, Source tag (LinkedIn / Wuzzuf), Date posted.
  - Alignment Summary: Candidate fit score percentage, matched candidate skills (highlighted in soft sage green), and skills mentioned in the job description.
  - Job Content: Clean formatted job description text, key responsibilities, and qualifications.
  - Sticky Action Bar:
    - **"Apply on Source"** (primary solid button): Opens external job link in a new tab.
    - **"Tailor your CV"** (secondary pill button): Interactive preview with a subtle *"Phase 3: CV Studio Preview"* tooltip explaining how surgical LaTeX tailoring will work.

---

## 6. Implementation Phasing

### Phase 1: Backend Auto-Search Pipeline & API
- [x] Implement `POST /api/v1/jobs/auto-search` in [jobs.py](file:///d:/Tailored/backend/app/api/routes/jobs.py) accepting `profile_id` and optional `persona_id`.
- [x] Connect `UserProfile` to multi-source ingestion in [job_search_service.py](file:///d:/Tailored/backend/app/pipeline/job_search_service.py).
- [x] Compute `fit_score` and persist directly into `jobs` table.
- [x] Support query filtering in `GET /api/v1/jobs`.

### Phase 2: Dedicated Job Radar Page & Navigation
- [x] Add top-level page state in [App.tsx](file:///d:/Tailored/frontend/src/App.tsx) (`currentView: 'home' | 'radar'`).
- [x] Add routing triggers:
  - Quiz Funnel completion -> auto-redirects to `'radar'`.
  - Hero search submit -> auto-redirects to `'radar'`.
  - Header & Sidebar navigation item "Job Radar".
- [x] Create [JobRadarPage.tsx](file:///d:/Tailored/frontend/src/components/radar/JobRadarPage.tsx) container with search toolbar and candidate persona context banner.

### Phase 3: Job Card Feed & Curated Match Badges
- [x] Create [JobCard.tsx](file:///d:/Tailored/frontend/src/components/radar/JobCard.tsx) with clean editorial tech styling.
- [x] Implement restrained match logic (single `✨ High Match` pill for top candidates).
- [x] Handle loading and empty states with filter resets.

### Phase 4: Right Slide-Out Details Pane (`JobDetailPane.tsx`)
- [x] Create [JobDetailPane.tsx](file:///d:/Tailored/frontend/src/components/radar/JobDetailPane.tsx) slide-out drawer with backdrop blur.
- [x] Display full job description, parsed requirements, and matched skills.
- [x] Add direct external **"Apply on LinkedIn/Wuzzuf"** link and inactive **"Tailor your CV"** action button with Phase 3 badge.

### Phase 5: Verification & End-to-End Testing
- [x] Automated API tests for `POST /api/v1/jobs/auto-search` and `GET /api/v1/jobs` ([test_auto_search_api.py](file:///d:/Tailored/backend/tests/test_auto_search_api.py)).
- [x] Frontend build verification (`npm run build` passed in 94ms).
- [x] Browser subagent validation testing the complete search transition and right pane slide-out.

