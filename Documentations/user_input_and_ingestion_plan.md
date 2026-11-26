# Technical Plan: User Input Architecture & API Ingestion Execution

This document specifies the technical design for **User Profile Input**, **Regional Contact & Multi-Location Flexibility**, and **API-Driven Job Ingestion** for **Tailored**.

> [!IMPORTANT]
> **Strict Scope Boundaries:**
> - ✅ **IN SCOPE:** User Master Profile data schema, regional contact mapping, multi-location handling, search query translation, and direct API/scraper execution (Apify LinkedIn, Wuzzuf).
> - ❌ **OUT OF SCOPE:** No UI implementation, no AI reasoning/LLM extraction, no CV fit scoring yet. This phase is purely data modeling and deterministic data fetching.

---

## 1. User Master Identity & Multi-Persona Architecture

A candidate's profile is separated into:
1. **Core Identity:** Name, primary email, portfolio/GitHub/LinkedIn links, university degrees, and languages.
2. **Regional Contact Registry:** Multiple phone numbers and regional emails (e.g., an Egyptian number for local roles, a Saudi or UAE number for Gulf roles).
3. **Dynamic Location Preferences:** Multiple target locations (e.g., Cairo, Riyadh, Dubai, Remote) with independent work modes.
4. **Career Personas (Tracks):** Multiple target job titles (e.g., *Data Scientist* vs. *Data Analyst*), each holding its own specific skills, tools, bullet points, projects, and certifications.

```
                              ┌───────────────────────────────────────────────┐
                              │            USER MASTER IDENTITY               │
                              │  • Name, Primary Email, Social Links          │
                              │  • Degrees & Spoken Languages                 │
                              └───────────────────────┬───────────────────────┘
                                                      │
         ┌────────────────────────────────────────────┼────────────────────────────────────────────┐
         ▼                                            ▼                                            ▼
┌─────────────────────────────────┐        ┌──────────────────────────────────┐        ┌─────────────────────────────────┐
│    Regional Contact Registry    │        │    Target Locations Registry     │        │     Career Personas (Tracks)    │
│  • Egypt Phone (+20...)         │        │  • Primary: Cairo, Egypt         │        │  • Persona 1: Data Scientist    │
│  • Saudi Phone (+966...)        │        │  • Target: Riyadh, Saudi Arabia  │        │  • Persona 2: Data Analyst      │
│  • UAE Phone (+971...)          │        │  • Target: Global / Remote       │        │  (Each with own skills/projects)│
└─────────────────────────────────┘        └──────────────────────────────────┘        └─────────────────────────────────┘
```

---

## 2. Regional Contacts & Multi-Location Strategy

### 2.1. Regional Contact Registry
Job seekers applying across borders often maintain local SIM cards or roaming virtual numbers to maximize callback rates. HR managers in Saudi Arabia or the UAE strongly prefer calling local numbers.

```json
"contact_numbers": [
  {
    "country_code": "EG",
    "dial_code": "+20",
    "phone_number": "1001234567",
    "is_primary": true,
    "label": "Egypt Mobile"
  },
  {
    "country_code": "SA",
    "dial_code": "+966",
    "phone_number": "501234567",
    "is_primary": false,
    "label": "Saudi Mobile (Zain/STC)"
  }
]
```

**Auto-Select Rule:**
When the system eventually pairs a tailored CV with a job in Saudi Arabia, it automatically selects the Saudi phone number. For Egypt or general remote roles, it falls back to the primary number.

---

### 2.2. Multi-Location Targeting & Search Flexibility
Users do not look for jobs in only one place. They want to search across **multiple geographies** simultaneously or change their focus at will:

```json
"target_locations": [
  {
    "location_id": "loc_cairo",
    "city": "Cairo",
    "country": "Egypt",
    "work_modes": ["Hybrid", "On-site", "Remote"],
    "is_active_for_search": true
  },
  {
    "location_id": "loc_riyadh",
    "city": "Riyadh",
    "country": "Saudi Arabia",
    "work_modes": ["On-site", "Hybrid", "Remote"],
    "is_active_for_search": true
  },
  {
    "location_id": "loc_global_remote",
    "city": "Worldwide",
    "country": "Remote",
    "work_modes": ["Remote"],
    "is_active_for_search": true
  }
]
```

---

## 3. The Complete Input JSON Schemas

### 3.1. Master User Profile (`user_profile.json`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "version": "1.1.0",
  "personal_info": {
    "full_name": "Ahmed El-Sayed",
    "primary_email": "ahmed.elsayed@example.com",
    "contact_numbers": [
      {
        "country_code": "EG",
        "dial_code": "+20",
        "phone_number": "1001234567",
        "is_primary": true,
        "label": "Egypt Mobile"
      },
      {
        "country_code": "SA",
        "dial_code": "+966",
        "phone_number": "501234567",
        "is_primary": false,
        "label": "Saudi Mobile"
      }
    ],
    "links": {
      "linkedin": "https://linkedin.com/in/ahmed-elsayed",
      "github": "https://github.com/ahmed-elsayed",
      "portfolio": "https://ahmedelsayed.dev"
    }
  },
  "residence_and_mobility": {
    "current_residence": {
      "city": "Cairo",
      "country": "Egypt"
    },
    "willing_to_relocate": true,
    "target_locations": [
      {
        "location_id": "loc_cairo",
        "city": "Cairo",
        "country": "Egypt",
        "work_modes": ["Remote", "Hybrid"],
        "is_active_for_search": true
      },
      {
        "location_id": "loc_riyadh",
        "city": "Riyadh",
        "country": "Saudi Arabia",
        "work_modes": ["On-site", "Hybrid", "Remote"],
        "is_active_for_search": true
      },
      {
        "location_id": "loc_remote",
        "city": "Remote",
        "country": "Global",
        "work_modes": ["Remote"],
        "is_active_for_search": true
      }
    ]
  },
  "education": [
    {
      "institution": "Cairo University",
      "degree": "B.S. in Computer Science",
      "field_of_study": "Information Systems",
      "graduation_year": 2021
    }
  ],
  "languages": [
    {"language": "Arabic", "proficiency": "Native"},
    {"language": "English", "proficiency": "Professional"}
  ],
  "career_personas": [
    {
      "persona_id": "data_scientist_track",
      "target_title": "Data Scientist",
      "alternative_titles": ["Machine Learning Engineer", "AI Engineer"],
      "is_primary": true,
      "seniority_level": "Mid-Level",
      "years_of_experience": 3,
      "summary_bio": "Data Scientist with 3+ years building predictive ML models, NLP pipelines, and production inference APIs with Python, PyTorch, and Docker.",
      "skills_and_tools": {
        "core_skills": ["Machine Learning", "Deep Learning", "NLP", "Feature Engineering"],
        "programming_languages": ["Python", "SQL"],
        "frameworks_and_libraries": ["PyTorch", "Scikit-Learn", "Pandas", "FastAPI"],
        "tools_and_platforms": ["Docker", "MLflow", "PostgreSQL", "Git"]
      },
      "experience_highlights": [
        {
          "company": "Swvl",
          "role": "Data Scientist",
          "start_date": "2022-08",
          "end_date": "Present",
          "location": "Cairo, Egypt",
          "achievements": [
            "Built a dynamic route pricing regression model that improved ride margins by 7.4%.",
            "Deployed production sentiment analysis model processing 50k+ user reviews monthly."
          ]
        }
      ],
      "featured_projects": [
        {
          "name": "Customer Churn Early-Warning Predictor",
          "tech_stack": ["Python", "XGBoost", "FastAPI", "PostgreSQL"],
          "summary": "Trained and deployed an XGBoost pipeline predicting user churn with 88% ROC-AUC.",
          "link": "https://github.com/ahmed-elsayed/churn-predictor"
        }
      ],
      "certifications": [
        {
          "name": "Deep Learning Specialization",
          "issuer": "DeepLearning.AI",
          "issue_date": "2022-03"
        }
      ]
    },
    {
      "persona_id": "data_analyst_track",
      "target_title": "Data Analyst",
      "alternative_titles": ["Business Intelligence Analyst", "Product Analyst"],
      "is_primary": false,
      "seniority_level": "Mid-Level",
      "years_of_experience": 3,
      "summary_bio": "Analytical problem solver skilled in transforming complex relational databases into executive decision dashboards using SQL, Tableau, and Power BI.",
      "skills_and_tools": {
        "core_skills": ["Exploratory Data Analysis", "Cohort Analysis", "KPI Metric Formulation"],
        "programming_languages": ["SQL (PostgreSQL, BigQuery)", "Python"],
        "frameworks_and_libraries": ["Pandas", "Matplotlib", "Seaborn"],
        "tools_and_platforms": ["Power BI", "Tableau", "Excel", "Metabase"]
      },
      "experience_highlights": [
        {
          "company": "Swvl",
          "role": "Product Data Analyst (Cross-functional)",
          "start_date": "2022-08",
          "end_date": "Present",
          "location": "Cairo, Egypt",
          "achievements": [
            "Designed executive daily active rider dashboard in Metabase.",
            "Wrote optimized PostgreSQL queries reducing reporting ETL runtimes by 42%."
          ]
        }
      ],
      "featured_projects": [
        {
          "name": "E-Commerce Cohort Retention & LTV Dashboard",
          "tech_stack": ["SQL", "Power BI", "Python"],
          "summary": "Built end-to-end dashboard tracking customer lifetime value (LTV) and 30-day retention.",
          "link": "https://github.com/ahmed-elsayed/retention-bi-dashboard"
        }
      ],
      "certifications": [
        {
          "name": "Google Data Analytics Professional Certificate",
          "issuer": "Google",
          "issue_date": "2021-11"
        }
      ]
    }
  ]
}
```

---

### 3.2. Derived Search Query Request (`search_request.json`)

This payload is generated automatically from the active persona and active locations, but can be customized before triggering ingestion:

```json
{
  "persona_id": "data_scientist_track",
  "query_terms": ["Data Scientist", "Machine Learning Engineer"],
  "target_locations": [
    {"city": "Cairo", "country": "Egypt", "is_remote": false},
    {"city": "Riyadh", "country": "Saudi Arabia", "is_remote": false},
    {"city": "Remote", "country": "Worldwide", "is_remote": true}
  ],
  "date_posted_filter": "past-24h",
  "enabled_sources": {
    "linkedin_apify": true,
    "wuzzuf": true,
    "company_ats": true
  },
  "constraints": {
    "max_results_per_source_per_location": 20,
    "exclude_keywords": ["unpaid", "internship", "volunteer"]
  }
}
```

---

## 4. Ingestion Engine: Input Translation to API Execution

The ingestion engine takes the `search_request.json` and fans it out across configured source APIs.

```
                  ┌──────────────────────────────────────────────┐
                  │            Search Request Payload            │
                  │  Keywords: ["Data Scientist"]                │
                  │  Locations: ["Cairo, Egypt", "Riyadh, KSA"]  │
                  │  Window: "past-24h", Max: 20/location        │
                  └──────────────────────┬───────────────────────┘
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   ▼                                           ▼
┌──────────────────────────────────────┐    ┌──────────────────────────────────────┐
│  LinkedIn (Apify Actor API)          │    │  Wuzzuf (Direct HTTP Scraper)        │
│  • Calls Curious Coder Actor         │    │  • Searches Cairo & Riyadh jobs      │
│  • Feeds title, location, past-24h   │    │  • Pulls raw HTML & job links        │
└──────────────────┬───────────────────┘    └──────────────────┬───────────────────┘
                   │                                           │
                   └─────────────────────┬─────────────────────┘
                                         │ Raw Data Streams
                                         ▼
                   ┌───────────────────────────────────────────┐
                   │  Standardizer & Canonical Deduplicator    │
                   │  • Normalize Company, Title, Location     │
                   │  • Generate canonical_hash                │
                   │  • Persist RawJob records into DB         │
                   └───────────────────────────────────────────┘
```

---

### 4.1. Apify LinkedIn Jobs Scraper Adapter

#### Target Actor: `curious_coder/linkedin-jobs-scraper`
We call Apify's run endpoint using the credentials stored in `.env`:
`POST https://api.apify.com/v2/acts/curious_coder~linkedin-jobs-scraper/runs?token={APIFY_API_TOKEN}`

#### How Input Maps to Apify Actor Payload:
For each active target location, we construct an individual actor run or a combined batch run:

```python
apify_payload = {
    # 1. Search Query
    "title": "Data Scientist",
    
    # 2. Location
    "location": "Cairo, Egypt",  # or "Riyadh, Saudi Arabia"
    
    # 3. Time Filter (Freshness)
    "datePosted": "past-24h",    # Maps from search_request.date_posted_filter
    
    # 4. Volume / Quota Safety
    "maxItems": 20,              # Maps from search_request.constraints.max_results
    
    # 5. Work Mode Filters
    "remote": True               # If work_modes includes "Remote"
}
```

#### Retrieving Dataset Items:
Once the run finishes, we fetch the dataset:
`GET https://api.apify.com/v2/datasets/{defaultDatasetId}/items?token={APIFY_API_TOKEN}`

#### Field Transformation to Standard `RawJob`:
| Apify Output Field | Standard `RawJob` Field |
| :--- | :--- |
| `id` / `jobId` | `source_id` (prefixed: `linkedin_{id}`) |
| `title` | `title` |
| `companyName` | `company_name` |
| `location` | `location` |
| `link` / `jobUrl` | `url` |
| `descriptionText` / `description` | `raw_description` |
| `publishedAt` / `postedAt` | `posted_at` |

---

### 4.2. Wuzzuf HTTP Scraper Adapter

#### Execution:
Direct asynchronous HTTP request using `httpx` (no browser needed):

```python
# Construct URL for Egypt / Gulf searches
params = {
    "q": "Data Scientist",
    "a": "hpb",                       # Search type
    "filters[country][0]": "Egypt",   # or "Saudi Arabia"
    "filters[post_date][0]": "past_24_hours"
}
url = "https://wuzzuf.net/search/jobs/?"
```

#### Extraction:
- HTML cards parsed using `selectolax` (ultra-fast HTML parser).
- Extracted fields: `title`, `company`, `location`, `job_url`.
- For newly discovered URLs, fetch the job details page to extract the full description text.
- Map into standard `RawJob` format.

---

### 4.3. Standardized Output Contract: `RawJob`

Every adapter, regardless of whether it hits Apify, Wuzzuf, or a Company ATS, must output the exact same object:

```python
class RawJob(BaseModel):
    source_type: str             # "linkedin_apify", "wuzzuf", "company_ats"
    source_id: str               # e.g. "linkedin_38291823"
    title: str
    company_name: str
    location: str
    url: str
    raw_description: str
    posted_at: Optional[datetime] = None
    canonical_hash: str          # sha256(normalized_company:normalized_title:normalized_location)
```

---

## 5. Execution Steps (What We Implement Next)

1. **Update Pydantic Models (`backend/app/schemas/user_profile.py`):**
   - Implement `UserProfile`, `RegionalContact`, `TargetLocation`, and `CareerPersona`.
   - Add parser for loading and validating `user_profile.json`.
2. **Implement Query Generator (`backend/app/pipeline/query_generator.py`):**
   - Accepts `UserProfile` + `persona_id`.
   - Produces `SearchRequest` expanding titles $\times$ target locations.
3. **Implement Apify LinkedIn Client (`backend/app/scrapers/apify_linkedin.py`):**
   - Connects to Apify API using `.env` token (`APIFY_API_TOKEN`).
   - Runs `curious_coder/linkedin-jobs-scraper` for target queries.
   - Converts dataset items into `List[RawJob]`.
4. **Implement Wuzzuf Scraper Client (`backend/app/scrapers/wuzzuf_scraper.py`):**
   - Direct HTTP scraper for Wuzzuf results.
   - Emits `List[RawJob]`.
5. **Add Test Harness Script (`backend/tests/test_ingestion_api.py`):**
   - Loads [sample_user_profile.json](file:///d:/Tailored/backend/tests/fixtures/sample_user_profile.json).
   - Generates the search requests for each location (Cairo & Riyadh).
   - Executes live test fetches against Apify and Wuzzuf.
   - Saves raw results into a test JSON file (`backend/tests/fixtures/fetched_raw_jobs.json`) to inspect raw data without any AI/LLM intervention.
