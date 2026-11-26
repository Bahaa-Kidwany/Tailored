# Technical Plan: Fast Structured Job Extraction via Lite LLM

This document specifies the technical design, data schema, prompt engineering, and execution architecture for **Structured Job Description Insights Extraction** using a high-speed, cost-effective "Lite LLM".

---

## 1. Objective & Role in Pipeline

In **Story 1 (Job Fetcher)**, we established the multi-source ingestion engine that produces [fetched_raw_jobs.json](file:///d:/Tailored/backend/tests/fixtures/fetched_raw_jobs.json). These raw postings contain messy, unstructured text or HTML.

In this stage, the **Job Extractor** transforms raw text into a clean, structured JSON artifact:
**`extracted_job_insights.json`**.

```
┌──────────────────────────────────────┐
│  fetched_raw_jobs.json               │
│  (Messy HTML, long descriptions,     │
│   unstandardized company titles)     │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│  High-Speed Lite LLM Extractor       │
│  • Gemini 2.5 / 1.5 Flash            │
│  • Native JSON Schema Enforcement    │
│  • Sub-second latency (~400-800ms)   │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│  extracted_job_insights.json         │
│  (Normalized title, skills, tools,   │
│   experience, work mode, salary)     │
└──────────────────┬───────────────────┘
                   │
                   ▼
     [Story 2: CV Fit Scoring & Tailoring]
```

> [!NOTE]
> **Why use a Lite LLM?**
> Extraction is an **Information Extraction (IE)** task, not a creative reasoning or document writing task. Large frontier models (Claude 3.5 Sonnet, GPT-4o) are 10x–20x more expensive and 3x slower. A model like **Gemini 2.5 Flash** or **Claude 3.5 Haiku** provides:
> - **Speed:** 300ms – 700ms response time.
> - **Cost:** ~$0.00015 per job (~$0.15 per 1,000 jobs).
> - **Guaranteed JSON:** Native Structured Outputs (guaranteed schema compliance).

---

## 2. Target JSON Schema: `ExtractedJobInsights`

The target JSON output will be saved into `backend/tests/fixtures/extracted_job_insights.json`.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "source_id": "linkedin_4384675689",
  "canonical_hash": "609853d0a59a9c9de88853acae45180c997761bf0e7ce0e17a28aa4a91bf27a8",
  "raw_title": "Sr. Python Dev / FullStack Engineer",
  "company_name": "Sprints",
  "extracted_insights": {
    "normalized_title": "Senior Python Developer",
    "seniority_level": "Senior",
    "employment_type": "Full-time",
    "work_mode": "Hybrid",
    "location": {
      "city": "Cairo",
      "country": "Egypt",
      "is_relocation_offered": false,
      "geography_restrictions": "Must reside in Greater Cairo"
    },
    "experience_requirements": {
      "minimum_years": 4,
      "maximum_years": 7,
      "education_level": "Bachelor's Degree in Computer Science or related"
    },
    "skills_and_technologies": {
      "mandatory_skills": ["Python", "FastAPI", "PostgreSQL", "REST APIs"],
      "nice_to_have_skills": ["Docker", "Redis", "Celery", "AWS"],
      "soft_skills": ["Problem Solving", "Technical Mentorship", "Agile Collaboration"]
    },
    "core_responsibilities": [
      "Architect and scale backend RESTful APIs using FastAPI and PostgreSQL.",
      "Lead database query optimization and schema migrations.",
      "Mentor junior software engineers and conduct code reviews."
    ],
    "compensation_and_benefits": {
      "is_salary_disclosed": true,
      "currency": "EGP",
      "min_salary": 45000,
      "max_salary": 65000,
      "benefits": ["Medical Insurance", "Flexible Hours", "Annual Learning Budget"]
    },
    "dealbreakers_and_flags": {
      "is_unpaid": false,
      "is_internship": false,
      "requires_visa_sponsorship": false
    }
  }
}
```

---

## 3. Pydantic Domain Contract (`backend/app/schemas/job_insights.py`)

```python
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class JobLocationInsight(BaseModel):
    city: str = "Unknown"
    country: str = "Unknown"
    is_relocation_offered: bool = False
    geography_restrictions: Optional[str] = None

class ExperienceRequirement(BaseModel):
    minimum_years: int = 0
    maximum_years: Optional[int] = None
    education_level: Optional[str] = None

class SkillsTaxonomy(BaseModel):
    mandatory_skills: List[str] = Field(default_factory=list)
    nice_to_have_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)

class CompensationInsight(BaseModel):
    is_salary_disclosed: bool = False
    currency: Optional[str] = None
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None
    benefits: List[str] = Field(default_factory=list)

class DealbreakersAndFlags(BaseModel):
    is_unpaid: bool = False
    is_internship: bool = False
    requires_visa_sponsorship: bool = False

class JobInsights(BaseModel):
    normalized_title: str
    seniority_level: str = "Mid-Level"  # "Entry-Level", "Junior", "Mid-Level", "Senior", "Lead"
    employment_type: str = "Full-time"  # "Full-time", "Part-time", "Contract", "Internship"
    work_mode: str = "On-site"          # "Remote", "Hybrid", "On-site"
    location: JobLocationInsight = Field(default_factory=JobLocationInsight)
    experience_requirements: ExperienceRequirement = Field(default_factory=ExperienceRequirement)
    skills_and_technologies: SkillsTaxonomy = Field(default_factory=SkillsTaxonomy)
    core_responsibilities: List[str] = Field(default_factory=list)
    compensation_and_benefits: CompensationInsight = Field(default_factory=CompensationInsight)
    dealbreakers_and_flags: DealbreakersAndFlags = Field(default_factory=DealbreakersAndFlags)

class ExtractedJobRecord(BaseModel):
    source_id: str
    canonical_hash: str
    raw_title: str
    company_name: str
    url: str
    extracted_insights: JobInsights
```

---

## 4. Prompt Engineering & Anti-Hallucination Guardrails

To prevent the LLM from inventing fake years of experience or hallucinating skills:

### System Prompt Directive
```text
You are a precise, deterministic Recruitment Intelligence Parser.
Your objective is to extract structured job requirements from raw job descriptions.

STRICT RULES:
1. ONLY extract skills and tools that are explicitly mentioned in the text. DO NOT extrapolate or guess.
2. If years of experience are not specified, set minimum_years to 0 and maximum_years to null.
3. For work_mode:
   - Mark "Remote" ONLY if the text explicitly states remote work is allowed.
   - Mark "Hybrid" if both on-site and remote are mentioned.
   - Otherwise, default to "On-site".
4. Normalize the job title to standard industry titles (e.g. "Senior Python Developer" instead of "Python Ninja").
5. Return strictly valid JSON conforming to the requested schema. No conversational preamble or markdown backticks.
```

---

## 5. High-Speed Processing & Concurrency Strategy

When a batch of 20–50 raw jobs is fetched:
Processing them sequentially with an LLM takes $30 \times 1\text{s} = 30\text{ seconds}$.
With **async concurrency** (`asyncio.gather` with a concurrency semaphore of 5):
- 30 jobs run in 6 concurrent waves.
- Total processing time drops to **~3–5 seconds**!

```
[fetched_raw_jobs.json (30 jobs)]
       │
       ▼
[Async Concurrency Pool (Semaphore=5)]
 ├── Worker 1: Job 1..5   ──► Lite LLM (Gemini Flash)
 ├── Worker 2: Job 6..10  ──► Lite LLM
 ├── Worker 3: Job 11..15 ──► Lite LLM
 ├── Worker 4: Job 16..20 ──► Lite LLM
 └── Worker 5: Job 21..25 ──► Lite LLM
       │
       ▼
[Validate with Pydantic]
       │
       ▼
[Save to extracted_job_insights.json]
```

---

## 6. Implementation Steps

1. **Create Insights Schema (`backend/app/schemas/job_insights.py`):**
   - Implement typed Pydantic models with validation.
2. **Implement Lite LLM Extractor Client (`backend/app/ai/extractor/fast_extractor.py`):**
   - Connects to Google GenAI / Gemini Flash (or Vertex AI / LiteLLM fallback).
   - Enforces Pydantic output schema via `response_schema=JobInsights`.
   - Includes graceful offline fallback using regex-based extraction if API keys are missing.
3. **Implement Batch Extraction Pipeline (`backend/app/pipeline/batch_extractor.py`):**
   - Reads [fetched_raw_jobs.json](file:///d:/Tailored/backend/tests/fixtures/fetched_raw_jobs.json).
   - Runs concurrent extractions with rate limiting.
   - Writes the completed list into [extracted_job_insights.json](file:///d:/Tailored/backend/tests/fixtures/extracted_job_insights.json).
4. **Create Test Verification Script (`backend/tests/test_extraction_pipeline.py`):**
   - Loads the 8 jobs currently in `fetched_raw_jobs.json`.
   - Runs extraction on each.
   - Validates that mandatory skills, normalized titles, and work modes are accurately extracted.
   - Dumps and asserts the output JSON structure.
