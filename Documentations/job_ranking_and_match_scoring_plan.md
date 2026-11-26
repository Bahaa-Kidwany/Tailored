# Job Match Scoring & Feed Ranking Architecture Plan
## Candidate-Centric Job Ordering & Match Scoring Engine

**Document Version:** 1.0.0  
**Status:** Approved Architectural Plan  
**Target Milestone:** Story 2 — CV Fit & Match Scoring Engine  

---

## 1. Architectural Mission & Philosophy

### 1.1 The Shift: Candidate Copilot vs. Recruiter Screener
In traditional Human Resources (HR) and Applicant Tracking Systems (ATS), evaluation is fundamentally **exclusionary**: candidates are filtered, screened out, and eliminated based on rigid knock-out criteria.

**Tailored operates on the inverse paradigm:**
- **We are NOT recruiters:** We do **never** reject, disqualify, or eliminate candidates.
- **We are the candidate's personal intelligence copilot:** Our goal is to fetch available market opportunities, evaluate how well each job aligns with the candidate's multi-persona career background, and **order/rank the jobs** from best fit to lowest fit in the user's feed.
- **Zero Drop Guarantee:** Every single fetched job remains in the candidate's feed. A job with a 50% match is not discarded; it is positioned lower in the feed with transparent insights on what technical gaps exist and how the candidate can bridge or address them.

```mermaid
graph TD
    subgraph Traditional ATS (Exclusionary)
        Candidates[Candidate Pool] --> Filter[Hard Knockout Rules]
        Filter --> Rejected[Candidate Disqualified]
        Filter --> Passed[Shortlist]
    end

    subgraph Tailored Paradigm (Candidate Copilot)
        Jobs[All Ingested Jobs] --> MatchEngine[Match Scoring Engine]
        Profile[User Profile & Personas] --> MatchEngine
        MatchEngine --> SortedFeed[Ordered Job Feed by Match Score DESC]
        SortedFeed --> TailoringHints[Strengths & Tailoring Opportunities]
    end
```

---

## 2. Core Principles of the Ranking Engine

1. **Relative Ranking over Binary Decisions:**
   Every job receives a composite **Match Score** $S \in [0, 100]$. The feed is presented as a sorted list:
   $$\text{Feed} = \text{SortByDesc}(Jobs, \lambda j: j.match\_score)$$

2. **Multi-Persona Optimization:**
   The candidate can possess multiple career personas (e.g., *Data Scientist* vs. *Data Analyst* vs. *Python Developer*). The engine calculates the match score across **all** of the candidate's active personas, identifies the **Best-Fit Persona** for each job, and displays the persona that maximizes the candidate's chances.

3. **Constructive Tailoring Guidance (Not Knockout Rejection):**
   Where gaps exist (e.g., candidate has 3 years of experience; job asks for 5 years), the engine does not issue a "Disqualified" flag. Instead, it provides **Tailoring Opportunities** (e.g., *"Role emphasizes 5 years of production experience; highlight your high-impact Swvl regression models and leadership in model deployment to demonstrate senior-level capability"*).

4. **Deterministic Reproducibility & Grounded Explanations:**
   The score is backed by granular breakdown metrics (Skills, Seniority, Projects, Location/Work Mode) so the user understands exactly *why* a job is ranked #1 versus #8.

---

## 3. Data Inputs & Context

The Match Scoring Engine consumes two standardized inputs:

### Input A: User Profile (`UserProfile`)
From [user_profile.py](file:///d:/Tailored/backend/app/schemas/user_profile.py):
- **Personal Info & Regional Contacts:** Multi-country phone numbers, links.
- **Mobility Preferences:** Target locations, cities, allowed work modes (Remote, Hybrid, On-site).
- **Career Personas:** List of `CareerPersona` records, each with:
  - `target_title` and `alternative_titles`
  - `seniority_level` and `years_of_experience`
  - `skills_and_tools` (categorized: core skills, programming languages, frameworks, tools)
  - `experience_highlights` (companies, roles, measurable achievements)
  - `featured_projects` (tech stacks, impact summaries)
  - `certifications`

### Input B: Extracted Job Record (`ExtractedJobRecord`)
From [job_insights.py](file:///d:/Tailored/backend/app/schemas/job_insights.py):
- `normalized_title` and `seniority_level`
- `work_mode` (Remote, Hybrid, On-site) and `location` (city, country)
- `experience_requirements` (minimum years, education)
- `skills_and_technologies` (`mandatory_skills`, `nice_to_have_skills`, `soft_skills`)
- `core_responsibilities` (3–5 bullet points)
- `dealbreakers_and_flags` (unpaid flags, visa restrictions, internships)

---

## 4. Multi-Dimensional Scoring Dimensions & Weighting

To provide a fair, comprehensive, and meaningful ranking, the composite score is evaluated across **five weighted dimensions**:

| Dimension | Weight ($w_i$) | Description & Focus |
| :--- | :---: | :--- |
| **1. Technical Skills Overlap** | **35%** | Overlap between candidate's technical skills (languages, frameworks, tools) and the job's mandatory vs nice-to-have requirements. |
| **2. Role & Title Alignment** | **20%** | Proximity between candidate's target/alternative titles and the job's normalized role title. |
| **3. Seniority & Experience Proximity** | **20%** | Proximity between candidate's years of experience / seniority tier and the job's stated requirements. |
| **4. Project & Domain Relevance** | **15%** | Alignment between candidate's past projects / company achievements and the job's core responsibilities. |
| **5. Location & Work Mode Fit** | **10%** | Compatibility between candidate's work mode preferences (Remote/Hybrid/On-site) and location versus job specifications. |

$$\text{Overall Match Score } S = \sum_{i=1}^{5} w_i \cdot S_i \quad \in [0, 100]$$

---

## 5. Granular Scoring Logic per Dimension

### Dimension 1: Technical Skills Overlap ($S_{skills} \in [0, 100]$)
- Let $M$ be the set of **mandatory skills** in the job specifications.
- Let $N$ be the set of **nice-to-have skills** in the job specifications.
- Let $C$ be the candidate's skills pool for the evaluated persona (with canonical aliases, e.g., `PyTorch` $\in$ `Deep Learning`).
- **Mandatory Match Rate ($R_M$):**
  $$R_M = \frac{|C \cap M|}{|M|} \quad (\text{if } |M| > 0 \text{ else } 1.0)$$
- **Bonus Nice-to-Have Rate ($R_N$):**
  $$R_N = \frac{|C \cap N|}{|N|} \quad (\text{if } |N| > 0 \text{ else } 0.0)$$
- **Skills Score:**
  $$S_{skills} = \min(100, (R_M \times 80) + (R_N \times 20))$$

### Dimension 2: Role & Title Alignment ($S_{title} \in [0, 100]$)
- Compares job `normalized_title` against candidate `target_title` and `alternative_titles`.
- **Exact match:** 100% (e.g., "Data Scientist" == "Data Scientist").
- **Alternative/Semantic match:** 80–95% (e.g., "Machine Learning Engineer" vs. "Data Scientist").
- **Adjacent role:** 50–70% (e.g., "Python Developer" vs. "Data Scientist").
- **Distant role:** 20–40% (e.g., "Frontend Developer" vs. "Data Scientist").

### Dimension 3: Seniority & Experience Proximity ($S_{exp} \in [0, 100]$)
Instead of hard cutoffs, we calculate continuous proximity:
- Let $Y_{cand}$ = Candidate years of experience.
- Let $Y_{req}$ = Job minimum years required.
- **Experience Ratio ($R_{exp}$):**
  - If $Y_{cand} \ge Y_{req}$: $S_{exp\_years} = 100$
  - If $Y_{cand} < Y_{req}$: $S_{exp\_years} = \max\left(40, 100 - (Y_{req} - Y_{cand}) \times 15\right)$
    *(Example: Candidate has 3 years, job asks for 5 years $\rightarrow 100 - (2 \times 15) = 70\%$. Candidate is never zeroed out!)*
- **Seniority Tier Proximity:**
  Compare seniority levels on a numerical scale:
  $Level(\text{Entry}) = 1, Level(\text{Junior}) = 2, Level(\text{Mid}) = 3, Level(\text{Senior}) = 4, Level(\text{Lead}) = 5$
  $$\Delta Level = |Level_{cand} - Level_{job}|$$
  - $\Delta = 0 \rightarrow 100\%$
  - $\Delta = 1 \rightarrow 80\%$
  - $\Delta = 2 \rightarrow 60\%$
  - $\Delta \ge 3 \rightarrow 40\%$
- **Dimension Score:** $S_{exp} = 0.6 \cdot S_{exp\_years} + 0.4 \cdot S_{seniority}$

### Dimension 4: Project & Domain Relevance ($S_{proj} \in [0, 100]$)
- Evaluates tech stacks and descriptions of `featured_projects` and `experience_highlights` against the job's `core_responsibilities`.
- **Full alignment:** Candidate has built production systems or projects directly utilizing the required workflows (e.g., deployed models with FastAPI + Docker for a backend/ML role) $\rightarrow 85 - 100\%$.
- **Partial alignment:** Relevant domains or tooling $\rightarrow 60 - 84\%$.
- **General technical baseline:** $\rightarrow 40 - 59\%$.

### Dimension 5: Location & Work Mode Fit ($S_{loc} \in [0, 100]$)
- Checks compatibility between candidate's `target_locations` and job location/work mode:
  - Job is **Remote** and candidate accepts **Remote** $\rightarrow 100\%$.
  - Job is **Hybrid / On-site** in candidate's current residence city or active target city $\rightarrow 100\%$.
  - Job is in a target relocation country and candidate marked `willing_to_relocate = True` $\rightarrow 85\%$.
  - Job is in another city/country without explicit relocation $\rightarrow 50\%$.

---

## 6. Multi-Persona Evaluation: Best-Fit Persona

Candidates frequently have diverse experience and target multiple tracks. For example:
- **Persona 1:** "Data Scientist" (Python, PyTorch, ML, Statistics, NLP)
- **Persona 2:** "Data Analyst" (SQL, Tableau, PowerBI, Pandas, Business Intelligence)
- **Persona 3:** "Python Backend Engineer" (FastAPI, Django, PostgreSQL, Docker)

When a job (e.g., *"Senior Fullstack Python Engineer"*) enters the scoring engine:
1. The engine calculates the composite match score $S$ against **Persona 1**, **Persona 2**, and **Persona 3**.
2. It assigns:
   $$\text{Best-Fit Persona} = \arg\max_{p \in Personas}(S_p)$$
3. The job feed uses this maximum score for default ordering, while tagging the job with:
   - `best_matched_persona_id`: e.g., `"python_backend_track"`
   - `best_matched_persona_title`: `"Python Backend Engineer"`
   - `persona_scores`: `{"data_scientist_track": 68.5, "data_analyst_track": 42.0, "python_backend_track": 84.2}`
4. The user can easily view their global ranked feed OR filter by a specific persona.

---

## 7. Explainability & Output Schema: `ranked_jobs.json`

Every ranked job in the output JSON delivers complete transparency to the user:

```json
{
  "rank": 1,
  "job_id": "wuzzuf_rcqxngwvzmck",
  "raw_title": "Senior FullStack (Python) Engineer",
  "company_name": "Vertex Technologies",
  "url": "https://wuzzuf.net/jobs/p/rcqxngwvzmck...",
  "overall_match_score": 84.5,
  "match_level": "Strong Match", 
  "best_matched_persona": {
    "persona_id": "data_scientist_track",
    "persona_title": "Data Scientist",
    "persona_match_score": 84.5
  },
  "dimension_breakdown": {
    "skills_match": {
      "score": 82.0,
      "matched_mandatory_skills": ["Python", "FastAPI", "Docker", "Relational Databases", "REST services"],
      "missing_mandatory_skills": ["TypeScript", "Vue", "RabbitMQ"],
      "matched_nice_to_have_skills": ["GCP", "Kubernetes"]
    },
    "role_and_title_match": {
      "score": 75.0,
      "analysis": "Data Scientist persona aligns with Python backend engineering, but role requires frontend (Vue/TypeScript)."
    },
    "experience_match": {
      "score": 80.0,
      "candidate_years": 3,
      "required_years": 5,
      "analysis": "3 years experience vs 5 years requested. Proximity score: 70%."
    },
    "project_and_domain_match": {
      "score": 90.0,
      "analysis": "Candidate projects feature production FastAPI deployments, Docker containers, and high-volume data APIs."
    },
    "location_and_mode_match": {
      "score": 100.0,
      "analysis": "Job is On-site in Cairo, Egypt; matches candidate primary residence."
    }
  },
  "tailoring_guidance": {
    "key_strengths_to_highlight": [
      "Deep Python expertise and production FastAPI experience directly match core backend stack.",
      "Hands-on experience with Docker containerization and PostgreSQL relational data optimization."
    ],
    "tailoring_opportunities": [
      "The role emphasizes FullStack with TypeScript/Vue. Highlight your frontend work or fullstack API integration in your CV.",
      "Address the 5-year requirement by showcasing high-impact achievements from Swvl where you owned end-to-end production pipelines."
    ]
  }
}
```

---

## 8. Technical Architecture & Component Design

The implementation will be modularized cleanly inside `backend/app/`:

```
backend/app/
├── schemas/
│   ├── user_profile.py             # UserProfile, CareerPersona
│   ├── job_insights.py             # JobInsights, ExtractedJobRecord
│   └── job_ranking.py              # New: RankedJobItem, RankedFeedResponse, DimensionScores
├── ranking/
│   ├── __init__.py
│   ├── dimension_scorers.py        # Deterministic scoring: Skills, Title, Exp, Location
│   ├── persona_matcher.py          # Multi-persona evaluation & best-fit selection
│   ├── ranker_engine.py            # Composite score computation, sorting, ranking
│   └── tailoring_advisor.py        # Generates strengths & CV tailoring guidance
└── pipeline/
    └── full_matching_pipeline.py   # Ingests jobs -> extracts insights -> ranks feed
```

### Component Roles:
1. **`dimension_scorers.py`**:
   Pure, deterministic algorithms for fast execution:
   - `score_skills(persona_skills, job_skills)`
   - `score_title(persona_titles, job_title)`
   - `score_experience(persona_exp, job_req)`
   - `score_location(user_locations, job_loc, job_mode)`
2. **`persona_matcher.py`**:
   Iterates over all user personas and selects the persona yielding the highest composite fit.
3. **`tailoring_advisor.py`**:
   Uses concise LLM reasoning or template-driven insights to produce constructive, actionable CV tailoring advice for the candidate.
4. **`ranker_engine.py`**:
   Runs the end-to-end ranking, sorts descending, assigns `rank` integers (1 to $N$), and returns `RankedFeedResponse`.

---

## 9. Verification & Testing Strategy

We will validate the complete scoring and ranking engine with automated tests:
1. **Input Fixtures:**
   - User Profile: `backend/tests/fixtures/sample_user_profile.json` (Ahmed El-Sayed: 3 years exp, Data Scientist & Data Analyst personas, Cairo resident).
   - Extracted Jobs: `backend/tests/fixtures/extracted_job_insights.json` (Real scraped Wuzzuf + LinkedIn jobs across Senior, Mid, Python, FullStack, AI/ML).
2. **Verification Criteria:**
   - **Zero Jobs Dropped:** If 8 jobs are ingested, exactly 8 jobs appear in the ranked feed.
   - **Monotonic Ordering:** $Score(Rank_i) \ge Score(Rank_{i+1})$ for all $i$.
   - **Accurate Persona Mapping:** A Data Science job maps to `data_scientist_track`; a Data Analyst job maps to `data_analyst_track`.
   - **Transparent Explanations:** Every ranked item contains clear breakdown scores and actionable tailoring advice.
   - **Test Script:** `backend/tests/test_job_ranking_pipeline.py` producing `backend/tests/fixtures/ranked_jobs_feed.json`.

---

## 10. Summary of Next Execution Steps
1. Create `backend/app/schemas/job_ranking.py` with Pydantic models for scores, breakdown, tailoring guidance, and ranked feed.
2. Implement deterministic scorers in `backend/app/ranking/dimension_scorers.py`.
3. Implement `backend/app/ranking/persona_matcher.py` and `backend/app/ranking/ranker_engine.py`.
4. Implement `backend/app/ranking/tailoring_advisor.py`.
5. Run automated pipeline test against `backend/tests/fixtures/extracted_job_insights.json` and verify the ordered feed output.
