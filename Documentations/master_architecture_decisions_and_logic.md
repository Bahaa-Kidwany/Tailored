# Tailored: Master Architecture, Decisions, Ideas, & Business Logic
## Complete Technical Reference & Evolution Record

**Document Version:** 1.0.0  
**Last Updated:** October 2026  
**Status:** Living Master Specification & Historical Record  

---

## 1. Executive Summary & Product Vision

### 1.1 What is Tailored?
**Tailored** is an AI-powered job discovery and application platform built specifically for **job seekers**. Unlike traditional recruitment platforms, job boards, or Applicant Tracking Systems (ATS) that optimize for recruiters filtering out candidates, Tailored acts as an **intelligent candidate copilot**.

The platform is organized around **Three Core Stories**:
1. **Story 1: The Multi-Source Job Fetcher & Ingestion Engine**  
   Aggregates live job postings across diverse sources (LinkedIn via Apify, regional job boards like Wuzzuf, and direct corporate careers pages), normalizes raw HTML/text into rich descriptions, and eliminates duplicates.
2. **Story 2: The Job Match Scoring & Feed Ranking Engine (CV Fit & Tailoring)**  
   Extracts structured insights from job descriptions using lightweight LLMs, evaluates job specifications against the candidate’s rich, multi-persona profile, and **orders/ranks jobs** in descending order of fit. It produces explainable match breakdowns and actionable CV tailoring recommendations.
3. **Story 3: The Job Application Assistant**  
   Assists the candidate through the final mile: auto-generating tailored CVs and cover letters targeted to the job’s specific requirements, and tracking application status.

---

## 2. Core Business Logic & Guiding Philosophy

### 2.1 The Cardinal Principle: Candidate Copilot vs. Recruiter Screener
The defining business philosophy of Tailored is:
> **"We are not recruiting. We are scoring if the user matches the job or not. We will not reject anyone or eliminate candidates—it is not our job. Our job is to order jobs based on data we got from the user against job specifications."**

```
┌─────────────────────────────────────────────────────────────┐
│                    TRADITIONAL ATS / RECRUITER              │
│  Goal: Disqualify & eliminate candidates to find top 2%     │
│  Logic: Knockout rules, binary rejections ("Disqualified")  │
└─────────────────────────────────────────────────────────────┘
                               ▲
                       OPPOSING PARADIGMS
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                         TAILORED                            │
│  Goal: Empower the candidate to find & tailor best jobs     │
│  Logic: Score & order all jobs; highlight strengths & gaps  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 The "Zero-Drop" Guarantee
- **No Ingested Job is Deleted or Disqualified:** If 10 relevant jobs are fetched, all 10 jobs remain visible in the user's feed.
- **Continuous Relative Ranking:** A job with a 45% match is not dropped; it is simply ordered lower in the feed than an 88% match job.
- **Constructive Framing:** Gaps are never presented as "You failed minimum requirements." Instead, they are framed as **"Tailoring Opportunities"** (e.g., *"Role asks for 5 years in AWS; highlight your hands-on Swvl Docker/ECS deployments and cloud projects to offset the stated requirement"*).

### 2.3 The Multi-Persona Reality of Modern Careers
A candidate is rarely defined by a single static job title. In today's market:
- A technical professional may be qualified as a **Data Scientist**, a **Machine Learning Engineer**, or a **Data Analyst**.
- A software engineer may target both **FullStack Python Engineer** and **Backend Systems Engineer**.
- Each persona possesses its own tailored set of skills, highlight projects, relevant work experience, and certifications.
- **Business Logic:** Tailored evaluates every job against **all** of the user's active career personas, dynamically identifies the **Best-Fit Persona**, and scores the job accordingly.

### 2.4 Multi-Geography & Regional Contact Identity
Candidates often seek opportunities across multiple geographies (e.g., home country and Gulf/relocation markets like Saudi Arabia or UAE, or remote worldwide):
- When applying to Egyptian jobs, an Egyptian phone number (`+20`) and local residence address should be presented.
- When applying to Saudi Arabian jobs, a Saudi number (`+966`) or clear relocation indicator should be used.
- **Business Logic:** The user profile maintains multi-regional identities, dynamic contact numbers, and target location preferences.

---

## 3. Chronological Step-by-Step Evolution & Key Decisions

### Phase 1: Ingestion Architecture & Job Fetching (Story 1)

#### 1. The Fetching Strategy Dilemma
* **Idea Discussed:**
  - *Option A: Hourly scheduled scraping of all jobs into a global database.*  
    *Pros:* Instant search response.  
    *Cons:* Massively high cost, high volume of stale/expired jobs, rate limits, storage bloat.
  - *Option B: Pure on-demand scraping when the user searches.*  
    *Pros:* Always 100% live.  
    *Cons:* Very slow (scraping LinkedIn or external sites takes 30–60 seconds per search).
  - *Option C: Profile-Driven Proactive Ingestion (Chosen Hybrid).*  
    When a user creates or updates their profile, their active personas and target locations trigger an immediate, targeted fetch. Results are cached, deduplicated, and kept fresh with automated background sweeps.
* **Decision:** Adopted **Option C**. Searches are scoped to the user’s primary titles and locations, avoiding wasteful scraping of irrelevant domains.

#### 2. Multi-Source Integration Strategy
* **Idea Discussed:** Build raw web scrapers for every platform vs. leverage specialized APIs.
* **Decisions:**
  - **LinkedIn:** Scraping LinkedIn directly triggers aggressive IP bans and bot-detection. Decided to use a dedicated Apify Actor (`curious_coder/linkedin-jobs-scraper`) via the official `apify-client` 3.x Python SDK.
  - **Wuzzuf (Regional MENA):** Built an asynchronous BeautifulSoup scraper.
  - **Company Careers Pages:** Future plan to ingest via Greenhouse/Lever/Workday public ATS endpoints.

#### 3. The Wuzzuf Deep-Description Lesson
* **Problem Discovered:** Wuzzuf search result cards only include short 1-line snippet teasers (e.g., "Python, Django, Cairo..."), omitting requirements, salary, and responsibilities.
* **Decision:** Enhanced `WuzzufScraperSource` with a two-tier scraping pipeline:
  1. Scrape search listing page to gather job URLs.
  2. Concurrently fetch the full job details page (`https://wuzzuf.net/jobs/p/...`) to capture complete 2,000–4,000 character job descriptions, full requirements, and company info.

#### 4. Canonical Deduplication & Noise Filtering
* **Problem:** Searching across multiple sources (LinkedIn + Wuzzuf) causes cross-platform duplicate postings. Additionally, some job search APIs return noise (e.g., "Cashier at Home Depot" when searching for "Python" or broad terms).
* **Decisions:**
  - Implemented **Canonical Hash Deduplication:** Computes a SHA-256 hash over normalized `(title, company, city, country)`. If the hash exists, duplicates are discarded.
  - Implemented **Negative Keyword Filtering:** Pre-filters out completely unrelated roles (e.g., cashier, delivery driver, retail associate) before passing data to expensive LLM extraction steps.

---

### Phase 2: User Input Architecture & Multi-Persona Profile Design

#### 1. Decoupled Data Model
Instead of a single monolithic CV string, the user data was decomposed into strongly typed Pydantic models in `backend/app/schemas/user_profile.py`:
- `PersonalInfo` & `ContactNumber`: Supports country codes (`EG`, `SA`, `AE`, `US`), international dial codes, and dynamic selection via `get_contact_for_country()`.
- `ResidenceAndMobility`: Current residence, relocation willingness, and multiple `TargetLocation` records (with individual allowed `work_modes`: Remote, Hybrid, On-site).
- `CareerPersona`: Allows multiple professional personas with:
  - `target_title` & `alternative_titles`
  - `seniority_level` & `years_of_experience`
  - `skills_and_tools` (categorized into core skills, programming languages, frameworks/libraries, tools/platforms)
  - `experience_highlights` & `featured_projects` (with tech stacks and measurable achievements)
  - `certifications`

#### 2. Autonomous Query Generation
Implemented `backend/app/pipeline/query_generator.py`:
- Automatically derives search queries from the user's primary persona and active locations.
- Allows user override through `SearchRequest` without modifying the core master profile.

---

### Phase 3: Structured Job Insights Extraction via Lite LLM

#### 1. Why Raw Text Extraction is Necessary
Job descriptions are notoriously noisy, full of HR boilerplate, ambiguous titles, and buried requirements. Downstream matching algorithms cannot effectively operate on unparsed HTML.

#### 2. Model Selection & Extraction Architecture
* **Decision:** Use Google Vertex AI with `gemini-2.5-flash` via the modern `google.genai` SDK.
* **Why `gemini-2.5-flash`?** Fast inference latency (<1.5s per job), low cost per token, and native support for Pydantic schema-guided JSON decoding (`response_schema=JobInsights`).
* **Schema Extracted (`backend/app/schemas/job_insights.py`):**
  1. `normalized_title` & `seniority_level` (Entry, Junior, Mid-Level, Senior, Lead)
  2. `work_mode` (Remote, Hybrid, On-site) & `location` (city, country, relocation offered)
  3. `experience_requirements` (minimum years, education level)
  4. `skills_and_technologies` categorized cleanly into:
     - `mandatory_skills` (strict core requirements)
     - `nice_to_have_skills` (preferred/bonus)
     - `soft_skills` (communication, leadership, mentoring)
  5. `core_responsibilities` (3–5 concise, actionable bullet points)
  6. `compensation_and_benefits` (currency, min/max salary if disclosed, benefits)
  7. `dealbreakers_and_flags` (unpaid, internship, visa sponsorship required)

---

### Phase 4: Job Match Scoring & Feed Ranking Architecture (Story 2)

#### 1. Pivot from Recruiter Evaluation to Candidate-Facing Ranking
* **Context:** An early draft planned an ATS-like candidate evaluation with disqualification checks.
* **Correction:** The user clarified the core identity:
  > *"we are not recruiting, we are scoring if the user matches the job or not, we will not reject anyone or eleminate candidates, its not our job. our job is to order jobs based on data we got from user against job specifications"*
* **Result:** Designed the **Candidate-Centric Job Match Scoring & Feed Ranking Engine** ([job_ranking_and_match_scoring_plan.md](file:///d:/Tailored/Documentations/job_ranking_and_match_scoring_plan.md)).

#### 2. The 5-Dimensional Scoring Algorithm
Every job is evaluated against the candidate across 5 transparent dimensions:

| Dimension | Weight ($w_i$) | Core Scoring Rationale |
| :--- | :---: | :--- |
| **Technical Skills Overlap** | **35%** | Compares candidate skills against `mandatory_skills` (80% of skills score) and `nice_to_have_skills` (20% bonus). Uses alias mapping (e.g., PyTorch satisfies Deep Learning). |
| **Role & Title Alignment** | **20%** | Proximity between job `normalized_title` and persona's target + alternative titles. |
| **Experience & Seniority Proximity** | **20%** | Continuous proximity scoring between candidate years/seniority and job requirement. **No zeroing out**: If candidate has 3 years and job asks for 5 years, candidate gets 70% proximity score. |
| **Project & Domain Relevance** | **15%** | Matches candidate project tech stacks and past achievements against the job's `core_responsibilities`. |
| **Location & Work Mode Fit** | **10%** | Verifies alignment between job location/work mode and candidate's target locations and mobility preferences. |

$$\text{Composite Match Score } S = \sum_{i=1}^{5} w_i \cdot S_i \quad \in [0, 100]$$

#### 3. Multi-Persona Best-Fit Resolution
When a job is scored:
1. It is evaluated against every active persona in `UserProfile.career_personas`.
2. The persona achieving the highest composite score is selected as the `best_matched_persona`.
3. The job feed is sorted by this best-fit score by default:
   $$\text{Job Feed} = \text{SortByDesc}(Jobs, \lambda j: j.best\_matched\_score)$$
4. The user can switch persona filters in the UI to see how jobs rank specifically for their "Data Analyst" track vs. their "Data Scientist" track.

#### 4. The Output Contract: `ranked_jobs.json`
Every job in the output JSON includes:
- `rank`: Integer rank position (1 to $N$).
- `overall_match_score`: Float between $0.0$ and $100.0$.
- `match_level`: "Exceptional Match" ($\ge 85$), "Strong Match" ($70–84$), "Moderate Fit" ($50–69$), "Exploratory Fit" ($<50$).
- `best_matched_persona`: Persona ID and title.
- `dimension_breakdown`: Granular scores and exact matched/missing skills.
- `tailoring_guidance`: 
  - `key_strengths_to_highlight`: Specific achievements to front-load.
  - `tailoring_opportunities`: Actionable ways to frame the CV to bridge gaps.

---

## 4. End-to-End System Architecture Diagram

```mermaid
flowchart TD
    subgraph User Input Layer
        UP[User Profile] --> P1[Persona: Data Scientist]
        UP --> P2[Persona: Data Analyst]
        UP --> LOC[Target Locations & Work Modes]
        UP --> CONT[Multi-Country Contacts]
    end

    subgraph Query Generation
        UP --> QG[Query Generator]
        QG --> Q1["Query: Data Scientist in Cairo, Riyadh, Remote"]
    end

    subgraph Ingestion & Fetching Engine (Story 1)
        Q1 --> AP[Apify LinkedIn Actor]
        Q1 --> WZ[Wuzzuf Scraper]
        AP --> RAW[Raw Ingestion Stream]
        WZ --> RAW
        RAW --> DEDUP[Canonical SHA-256 Deduplication]
        DEDUP --> NEG[Negative Keyword Filter]
        NEG --> RAW_FIXTURE[fetched_raw_jobs.json]
    end

    subgraph Extraction Engine (Story 2 Part A)
        RAW_FIXTURE --> LLM[Fast LLM: Gemini 2.5 Flash]
        LLM --> INSIGHTS[ExtractedJobRecord with JobInsights]
        INSIGHTS --> EXT_FIXTURE[extracted_job_insights.json]
    end

    subgraph Scoring & Ranking Engine (Story 2 Part B)
        EXT_FIXTURE --> MATCHER[Multi-Persona Match Scorer]
        UP --> MATCHER
        MATCHER --> D1[Skills Overlap 35%]
        MATCHER --> D2[Title Alignment 20%]
        MATCHER --> D3[Experience Proximity 20%]
        MATCHER --> D4[Project Relevance 15%]
        MATCHER --> D5[Location/Mode Fit 10%]
        D1 & D2 & D3 & D4 & D5 --> COMP[Composite Score 0-100%]
        COMP --> BEST_P[Select Best-Fit Persona]
        BEST_P --> ADVISOR[Tailoring Advisor]
        ADVISOR --> SORT[Sort By Match Score DESC]
        SORT --> RANKED_FEED[ranked_jobs.json]
    end

    subgraph Final Mile (Story 3)
        RANKED_FEED --> TAILOR_CV[Tailored CV & Cover Letter Generator]
        RANKED_FEED --> TRACKER[Application Status Tracker]
    end
```

---

## 5. Architectural Decision Records (ADR Summary Table)

| ADR ID | Decision Topic | Choice Made | Rationale | Alternatives Considered & Rejected |
| :--- | :--- | :--- | :--- | :--- |
| **ADR-001** | Job Fetching Timing | Profile-Driven Proactive Fetch | Avoids massive crawling bills and stale database bloat while keeping user search responsive. | Global hourly crawling (too expensive, stale DB); Pure on-demand scraping (too slow for user). |
| **ADR-002** | LinkedIn Ingestion | Apify LinkedIn Jobs Scraper | LinkedIn maintains intense anti-scraping protections. Apify handles rotating proxies and anti-bot measures cleanly. | In-house Playwright scraper (constant maintenance, high IP ban risk). |
| **ADR-003** | Wuzzuf Scraping Depth | Two-Tier Search + Full Details Fetch | Wuzzuf search cards only provide brief snippets; the full page contains essential requirements and descriptions. | Scraping card snippets only (inadequate for skill extraction). |
| **ADR-004** | Deduplication Key | SHA-256 on normalized `(title, company, city, country)` | Prevents duplicate cross-posts across platforms (e.g., job listed on both LinkedIn and Wuzzuf). | URL-based deduplication (fails across different job boards). |
| **ADR-005** | User Identity Model | Multi-Persona + Regional Contacts | Real job seekers have multiple career tracks and apply to both local and international markets with distinct contacts. | Single flat CV resume (forces candidates into a single box). |
| **ADR-006** | Extraction Engine Model | Google `gemini-2.5-flash` via Vertex AI | Sub-second latency, structured JSON output via Pydantic schemas, cost-effective for batch job extraction. | Open-source local models (slow, requires heavy GPUs); GPT-4o (unnecessarily expensive for batch extraction). |
| **ADR-007** | Evaluation Perspective | **Candidate Copilot / Ranking Engine** | The platform serves the candidate. We never disqualify or reject candidates; we score and order jobs to maximize user opportunities. | Recruiter / ATS knockout screener (wrong perspective, eliminates candidate options). |
| **ADR-008** | Experience Scoring Model | Continuous Proximity Curve (No Cutoff) | Candidates with 3 years experience can and do land jobs asking for 5 years. A strict cutoff harms candidates. | Binary cutoff: $Y < Y_{min} \rightarrow 0$ (unrealistic, exclusionary). |
| **ADR-009** | Persona Selection | Dynamic Max-Fit Resolution | Automatically surfaces the candidate's strongest track for any given job while preserving transparency across all personas. | Forcing the user to manually select which persona to evaluate against each job. |

---

## 6. Current Implementation Status & Artifacts

| Component | Status | Source Location / Artifact |
| :--- | :--- | :--- |
| **User Profile Schemas** | Completed | [user_profile.py](file:///d:/Tailored/backend/app/schemas/user_profile.py) |
| **Sample Profile Fixture** | Completed | [sample_user_profile.json](file:///d:/Tailored/backend/tests/fixtures/sample_user_profile.json) |
| **Query Generator** | Completed | [query_generator.py](file:///d:/Tailored/backend/app/pipeline/query_generator.py) |
| **Apify LinkedIn Source** | Completed | [apify_linkedin.py](file:///d:/Tailored/backend/app/scrapers/apify_linkedin.py) |
| **Wuzzuf Full Scraper** | Completed | [wuzzuf_scraper.py](file:///d:/Tailored/backend/app/scrapers/wuzzuf_scraper.py) |
| **Ingestion Engine & Dedup** | Completed | [ingestion_engine.py](file:///d:/Tailored/backend/app/pipeline/ingestion_engine.py) |
| **Raw Jobs Fixture** | Completed | [fetched_raw_jobs.json](file:///d:/Tailored/backend/tests/fixtures/fetched_raw_jobs.json) |
| **Job Insights Schemas** | Completed | [job_insights.py](file:///d:/Tailored/backend/app/schemas/job_insights.py) |
| **Fast LLM Extractor** | Completed | [fast_extractor.py](file:///d:/Tailored/backend/app/ai/extractor/fast_extractor.py) |
| **Batch Extraction Pipeline** | Completed | [batch_extractor.py](file:///d:/Tailored/backend/app/pipeline/batch_extractor.py) |
| **Extracted Insights Fixture** | Completed | [extracted_job_insights.json](file:///d:/Tailored/backend/tests/fixtures/extracted_job_insights.json) |
| **Ranking & Match Scoring Plan** | Completed | [job_ranking_and_match_scoring_plan.md](file:///d:/Tailored/Documentations/job_ranking_and_match_scoring_plan.md) |
| **Ranking Engine Implementation** | Next Step | `backend/app/ranking/` & `test_job_ranking_pipeline.py` |

---

## 7. Next Engineering Steps

1. **Implement `backend/app/schemas/job_ranking.py`:**  
   Pydantic schema definitions for `DimensionScores`, `RankedJobItem`, and `RankedJobFeed`.
2. **Implement `backend/app/ranking/dimension_scorers.py`:**  
   Deterministic, high-throughput calculation functions for Skills, Title, Experience, Projects, and Location.
3. **Implement `backend/app/ranking/persona_matcher.py` & `ranker_engine.py`:**  
   Multi-persona evaluation, best-fit selection, sorting by match score, and rank assignment.
4. **Implement `backend/app/ranking/tailoring_advisor.py`:**  
   Generates actionable strengths and tailoring opportunities for the candidate.
5. **Execute Verification Test (`backend/tests/test_job_ranking_pipeline.py`):**  
   Run end-to-end ranking on the real fixture jobs in `extracted_job_insights.json` against `sample_user_profile.json` and generate `ranked_jobs_feed.json`.
