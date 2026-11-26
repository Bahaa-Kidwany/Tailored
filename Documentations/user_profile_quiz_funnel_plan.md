# Technical Specification & Plan: User Profile Quiz Funnel, FastAPI Backend & PostgreSQL Storage

## 1. Executive Summary

This plan outlines the architecture, UX design, backend APIs, and database schema to bring the **Tailored** UI to life starting with **User Profiles and Career Personas**.

A candidate's profile is the single source of truth that drives:
1. **Targeted Job Radar Search Queries** (Apify LinkedIn & Wuzzuf).
2. **Deterministic Candidate Alignment & Scoring** (Fit Matrix).
3. **Zero-Hallucination CV & Cover Letter Generation** (CV Studio).

To ensure high conversion and a delightful user onboarding experience, we introduce a **6-Step Interactive Quiz Funnel** with rich aesthetics, real-time feedback, and support for **Multi-Persona Profiles** (e.g. Data Scientist vs. Data Analyst) and **Regional Dual-SIM Contacts** (MENA & Gulf cross-border hiring).

All collected data is stored in a **dockerized PostgreSQL database** with transactional integrity, exposed via **FastAPI RESTful endpoints**, with automatic fallback to local SQLite for offline development resilience.

---

## 2. System Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                      FRONTEND: REACT 19 + VITE                         │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    INTERACTIVE QUIZ FUNNEL                       │  │
│  │  Step 1: Identity & Regional Contacts (Dual-SIM EG/SA/AE)        │  │
│  │  Step 2: Residence & Target Search Geographies (Cairo, Riyadh)   │  │
│  │  Step 3: Education & Spoken Languages                            │  │
│  │  Step 4: Primary Career Persona (Title, Bio, Seniority, Exp)     │  │
│  │  Step 5: Persona Skills, Verified Bullet Points & Projects       │  │
│  │  Step 6: Review, Add Secondary Persona & Instant Radar Readiness │  │
│  └─────────────────────────────────┬────────────────────────────────┘  │
│                                    │ JSON Payload                      │
└────────────────────────────────────┼───────────────────────────────────┘
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        BACKEND: FASTAPI ENGINE                         │
│                                                                        │
│  Routes:                                                               │
│  • POST   /api/v1/profiles               -> Create complete profile    │
│  • GET    /api/v1/profiles               -> List saved profiles        │
│  • GET    /api/v1/profiles/{id}          -> Get profile with personas  │
│  • PUT    /api/v1/profiles/{id}          -> Update master profile      │
│  • POST   /api/v1/profiles/{id}/personas -> Add career persona track   │
│  • GET    /api/v1/profiles/{id}/search-request/{persona_id}            │
│  • GET    /api/v1/system/db-status       -> Check PG connection & stats│
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ SQLModel ORM (Psycopg 3)
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    PERSISTENCE: DOCKERIZED POSTGRESQL                  │
│                                                                        │
│  Database: tailored_db (PostgreSQL 15 Alpine on port 5432)             │
│  • user_profiles (Master identity, relocation willingness)             │
│  • contact_numbers (Regional phone registry, dial codes, labels)       │
│  • target_locations (Cities, countries, work modes)                    │
│  • career_personas (Tracks: skills, achievements, projects)            │
│  • education_records (Degrees, institutions, graduation years)         │
│  • spoken_languages (Languages, proficiency levels)                    │
│                                                                        │
│  (Graceful fallback to SQLite tailored.db if Docker is offline)        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Database Schema Design (SQLModel & PostgreSQL)

The schema adheres strictly to the contracts defined in `backend/app/schemas/user_profile.py`:

### 3.1. Tables & Relationships

```
┌───────────────────────┐
│     user_profiles     │
├───────────────────────┤
│ id (PK, SERIAL)       │◄──┐
│ full_name (VARCHAR)   │   │
│ primary_email (INDEX) │   │
│ current_city          │   │
│ current_country       │   │
│ willing_to_relocate   │   │
│ links_json (JSON)     │   │
│ created_at, updated_at│   │
└───────────┬───────────┘   │
            │ 1:N           │
            ├───────────────┼──────────────────────────────┐
            ▼               ▼                              ▼
┌───────────────────────┐ ┌───────────────────────┐ ┌───────────────────────┐
│    contact_numbers    │ │   target_locations    │ │    career_personas    │
├───────────────────────┤ ├───────────────────────┤ ├───────────────────────┤
│ id (PK)               │ │ id (PK)               │ │ id (PK)               │
│ profile_id (FK)       │ │ profile_id (FK)       │ │ profile_id (FK)       │
│ country_code (EG, SA) │ │ city (Cairo, Riyadh)  │ │ persona_id (slug)     │
│ dial_code (+20, +966) │ │ country               │ │ target_title          │
│ phone_number          │ │ work_modes_json (LIST)│ │ alternative_titles    │
│ is_primary (BOOLEAN)  │ │ is_active_for_search  │ │ is_primary (BOOLEAN)  │
│ label (Mobile, Zain)  │ └───────────────────────┘ │ seniority_level       │
└───────────────────────┘                           │ years_of_experience   │
                                                    │ summary_bio           │
                                                    │ skills_json           │
                                                    │ achievements_json     │
                                                    │ projects_json         │
                                                    │ certifications_json   │
                                                    └───────────────────────┘
```

### 3.2. Concrete SQLModel Definitions (`backend/app/models/profile.py`)

```python
class UserProfileDB(SQLModel, table=True):
    __tablename__ = "user_profiles"
    id: Optional[int] = DBField(default=None, primary_key=True)
    full_name: str = DBField(index=True)
    primary_email: str = DBField(index=True)
    current_city: str = DBField(default="Cairo")
    current_country: str = DBField(default="Egypt")
    willing_to_relocate: bool = DBField(default=True)
    links_json: Optional[str] = DBField(default="{}")  # {"linkedin": "...", "github": "..."}
    created_at: datetime = DBField(default_factory=utc_now)
    updated_at: datetime = DBField(default_factory=utc_now)

class ContactNumberDB(SQLModel, table=True):
    __tablename__ = "contact_numbers"
    id: Optional[int] = DBField(default=None, primary_key=True)
    profile_id: int = DBField(foreign_key="user_profiles.id", index=True)
    country_code: str = DBField(default="EG")
    dial_code: str = DBField(default="+20")
    phone_number: str
    is_primary: bool = DBField(default=False)
    label: str = DBField(default="Mobile")

class TargetLocationDB(SQLModel, table=True):
    __tablename__ = "target_locations"
    id: Optional[int] = DBField(default=None, primary_key=True)
    profile_id: int = DBField(foreign_key="user_profiles.id", index=True)
    location_id: str = DBField(default="loc_default")
    city: str
    country: str
    work_modes_json: str = DBField(default='["Remote", "Hybrid"]')
    is_active_for_search: bool = DBField(default=True)

class CareerPersonaDB(SQLModel, table=True):
    __tablename__ = "career_personas"
    id: Optional[int] = DBField(default=None, primary_key=True)
    profile_id: int = DBField(foreign_key="user_profiles.id", index=True)
    persona_id: str = DBField(index=True)
    target_title: str
    alternative_titles_json: str = DBField(default="[]")
    is_primary: bool = DBField(default=True)
    seniority_level: str = DBField(default="Mid-Level")
    years_of_experience: int = DBField(default=0)
    summary_bio: str = DBField(default="")
    skills_json: str = DBField(default="{}")
    experience_highlights_json: str = DBField(default="[]")
    featured_projects_json: str = DBField(default="[]")
    certifications_json: str = DBField(default="[]")

class EducationDB(SQLModel, table=True):
    __tablename__ = "education_records"
    id: Optional[int] = DBField(default=None, primary_key=True)
    profile_id: int = DBField(foreign_key="user_profiles.id", index=True)
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    graduation_year: Optional[int] = None
    grade_or_gpa: Optional[str] = None

class LanguageDB(SQLModel, table=True):
    __tablename__ = "spoken_languages"
    id: Optional[int] = DBField(default=None, primary_key=True)
    profile_id: int = DBField(foreign_key="user_profiles.id", index=True)
    language: str
    proficiency: str = DBField(default="Professional")
```

---

## 4. FastAPI RESTful Endpoints Specification

Prefix: `/api/v1/profiles`

| HTTP Method | Endpoint | Description | Request Body | Response Body |
| :--- | :--- | :--- | :--- | :--- |
| **POST** | `/` | Create a complete User Profile with contacts, locations, personas, education, & languages | `UserProfile` JSON | Full created record with IDs |
| **GET** | `/` | List all profiles with summary metadata | Query params: `skip`, `limit` | `List[ProfileSummary]` |
| **GET** | `/{id}` | Retrieve full Master Profile (converts relational models back to standard `UserProfile` schema) | None | `UserProfileResponse` |
| **PUT** | `/{id}` | Update existing profile and sync child collections | `UserProfile` JSON | Updated `UserProfileResponse` |
| **DELETE** | `/{id}` | Delete profile and cascade-delete child entities | None | `{"deleted": true, "id": id}` |
| **POST** | `/{id}/personas` | Append a new Career Persona to an existing profile | `CareerPersona` JSON | Created `CareerPersona` |
| **PATCH** | `/{id}/personas/{persona_id}/primary` | Switch the active primary persona | None | `{"active_persona_id": persona_id}` |
| **GET** | `/{id}/search-request/{persona_id}` | Generate Apify/Wuzzuf `SearchRequest` derived from this profile & persona | None | `SearchRequest` payload |
| **GET** | `/system/db-status` | Report database engine (Postgres vs SQLite fallback), status, and entity counts | None | `DBStatusResponse` |

---

## 5. Frontend Quiz Funnel UX & Visual Design

### 5.1. Design Philosophy
- **Aesthetic**: Tailored Luxury Dark Mode (deep obsidian `#090d16`, midnight blue `#0f172a`, electric cyan `#38bdf8`, and emerald accent `#34d399`).
- **Feel**: Fluid, gamified, non-intrusive, zero-clutter stepper with keyboard navigation (Enter / Esc).
- **Progressive Disclosure**: Show quick-pick presets for common tech skills, Gulf & Egyptian country codes, and popular job titles, while allowing custom free-form input.

### 5.2. Funnel Step Breakdown

#### Step 1: Onboarding & Identity
- **Header**: "Welcome to Tailored. Let's build your verified Master Profile."
- **Inputs**: Full Name, Primary Email, LinkedIn URL, GitHub URL, Portfolio link.
- **Convenience Feature**: "Prefill with Ahmed El-Sayed sample profile" button for instant 1-click preview and testing!

#### Step 2: Regional Contacts (Dual-SIM / Gulf Mobility)
- **Concept**: Cross-border applicants need local presence to maximize recruiter callbacks.
- **Inputs**:
  - Primary Contact: Country selector (Egypt +20, Saudi Arabia +966, UAE +971, Qatar +974, etc.), Phone number, Label.
  - Secondary / Roaming Contact: Toggle to add a Gulf SIM or roaming number.
  - Visual Badge: "Recruiter Calling Ready".

#### Step 3: Relocation & Target Geographies
- **Inputs**: Current residence (City, Country), Relocation Willingness toggle.
- **Interactive Multi-Select Hubs**:
  - Cairo (Hybrid / On-site / Remote)
  - Riyadh (On-site / Hybrid)
  - Dubai (On-site / Hybrid)
  - Global Remote (Remote)
- Users can toggle work modes per location with one tap.

#### Step 4: Academic Background & Spoken Languages
- **Inputs**:
  - Highest Degree (e.g. B.S. in Computer Science), Institution (e.g. Cairo University), Field of Study, Graduation Year.
  - Languages with interactive badge tags (Arabic - Native, English - Professional Working, French, German).

#### Step 5: Career Personas & Tracks (Multi-Profile Engine)
- **Concept**: A modern software professional isn't a single monolithic title. They may apply as both a **Data Scientist** and a **Data Analyst** or **Machine Learning Engineer**.
- **Per Persona**:
  - Target Title & Alternative Titles (e.g. "Data Scientist" + ["ML Engineer", "AI Specialist"]).
  - Seniority Level (Junior, Mid-Level, Senior, Lead) & Years of Experience.
  - Professional Bio / Elevator Pitch.
  - Interactive Skill Tags: Core Competencies, Languages (Python, SQL), Frameworks (PyTorch, Scikit-Learn, FastAPI), Tools (Docker, MLflow).
  - Key Experience Highlights with quantified metrics (e.g. "Improved ride margins by 7.4%").
- **Persona Adder**: "+ Add Secondary Career Persona" tab to create dual or triple tracks!

#### Step 6: Live Readiness Review & One-Click DB Save
- **Visuals**:
  - Live Radar Fit Score preview (e.g. "96% Complete - ATS Optimized").
  - Review summary card with tabs for each persona.
  - Regional phone routing preview ("When applying in KSA -> Uses +966; when applying in EG -> Uses +20").
  - "Save to Tailored Database" button with loading micro-animation and celebratory confirmation badge.

---

## 6. Implementation Phasing & Milestones

### Phase 1: Backend Database & FastAPI Endpoints
- [x] Create `backend/app/models/profile.py` with SQLModel tables (`UserProfileDB`, `ContactNumberDB`, `TargetLocationDB`, `CareerPersonaDB`, `EducationDB`, `LanguageDB`).
- [x] Update `backend/app/core/database.py` to register the new models in `init_db()`.
- [x] Create `backend/app/api/routes/profiles.py` implementing all CRUD and persona management endpoints.
- [x] Mount the router in `backend/app/main.py`.
- [x] Automated verification script `backend/tests/test_profile_db.py` passing all 10 assertions.

### Phase 2: Frontend Quiz Funnel Component & Design System
- [x] Create `frontend/src/components/quiz/QuizWizard.tsx` multi-step container with progress bar and glassmorphic backdrop.
- [x] Implement 6-step flow (Identity, Regional Dual-SIM Contacts, Mobility & Locations, Academic Foundation, Career Personas, Review & Save).
- [x] Create `frontend/src/styles/quiz.css` with dark luxury styling, micro-animations, and responsive layout.
- [x] Create `frontend/src/services/profileApi.ts` for clean API communication with the FastAPI backend.

### Phase 3: Integration into Main App & Profile Hub View
- [x] Connect Header CTA ("Build Profile (Quiz Funnel)") and Sidebar ("Master Profile & Skills") to open the Quiz Funnel.
- [x] Add `ActivePersonaBar.tsx` inside the main page to display saved profiles and enable 1-click persona switching.
- [x] Verified live end-to-end data flow: Form -> API -> Database -> Retrieval.

### Phase 4: Docker Postgres Verification & Health Check
- [x] Prepared `docker-compose.yml` for `docker compose up -d db`.
- [x] Verified backend database resilience: connects automatically to Postgres when running, with seamless SQLite fallback when Docker Desktop is offline.
- [x] Validated zero lint/type errors across frontend (`npm run build` passed in 390ms, `npm run lint` 0 errors).

