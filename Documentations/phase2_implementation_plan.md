# Phase 2 Implementation Plan: Scraping & Structured Job Evaluation

This document outlines the detailed architecture for Phase 2. The core requirements are **modular evaluation metrics** (each with isolated logic) and **flexible data sources** (supporting both scrapers and APIs).

## 1. Where the LLM is Used (and Where it is NOT)

To maintain cost efficiency and speed, the LLM is isolated to a single, specific step in the pipeline.

*   **NOT USED:** Fetching/Searching (Handled by standard HTTP/browser scraping or APIs).
*   **NOT USED:** Scoring/Evaluation (Handled by deterministic Python logic/math).
*   **✅ EXCLUSIVELY USED:** **Structured Extraction**. The LLM (e.g., Gemini Flash or Claude Haiku) takes the unstructured raw HTML/text of a job description and strictly maps it to a predefined JSON schema (`ParsedJob`).

---

## 2. Data Models (Inputs & Outputs)

We will use `Pydantic` for validation and `SQLModel` for database interactions.

```python
from pydantic import BaseModel
from typing import List, Optional

# 1. The Raw Data (Output of the Source/Scraper)
class RawJob(BaseModel):
    source_id: str          # e.g., "linkedin_12345"
    title: str
    url: str
    raw_description: str    # The full, messy HTML or Text
    company_name: str

# 2. The Structured Data (Output of the LLM)
class ParsedJob(BaseModel):
    required_skills: List[str]
    nice_to_have_skills: List[str]
    minimum_years_experience: int
    location_type: str      # "Remote", "On-site", "Hybrid"
    is_senior_role: bool
    core_responsibilities: List[str]

# 3. The User Profile (Input for Evaluator)
class UserProfile(BaseModel):
    target_titles: List[str]
    core_skills: List[str]
    years_of_experience: int
    preferred_location_type: str

# 4. The Evaluation Result (Output of the Evaluator)
class MetricScore(BaseModel):
    metric_name: str
    score: float            # 0.0 to 1.0
    weight: float           # How much this metric matters
    reasoning: str          # e.g., "Matched 3 out of 5 skills"

class JobEvaluation(BaseModel):
    raw_job_id: str
    total_score: float      # Out of 100
    metrics: List[MetricScore]
    is_passed: bool         # True if total_score > threshold
```

---

## 3. Flexible Sources (Scrapers & APIs)

We define a base interface. Whether we are scraping LinkedIn with a headless browser or hitting a clean API like RemoteOK, the rest of the system doesn't care, as long as it returns a list of `RawJob` objects.

```python
from abc import ABC, abstractmethod
from typing import List

class BaseJobSource(ABC):
    @abstractmethod
    def fetch_jobs(self, keywords: List[str], location: str) -> List[RawJob]:
        pass

# Example Mock Implementations
class LinkedInScraperSource(BaseJobSource):
    def fetch_jobs(self, keywords: List[str], location: str) -> List[RawJob]:
        # TODO: Implement Playwright stealth logic here
        # Return mock data for now
        return [RawJob(title="Data Scientist", ...)]

class RemoteOkApiSource(BaseJobSource):
    def fetch_jobs(self, keywords: List[str], location: str) -> List[RawJob]:
        # TODO: Implement simple `requests.get()` logic here
        return [RawJob(title="Remote Data Engineer", ...)]
```

---

## 4. The LLM Extractor

This is the only place AI is used in this pipeline.

```python
class JobExtractor:
    def __init__(self, llm_client):
        self.llm = llm_client
    
    def extract(self, raw_job: RawJob) -> ParsedJob:
        # ✅ LLM IS USED HERE
        # We pass `raw_job.raw_description` to the LLM and force it 
        # to output a JSON object that matches the `ParsedJob` schema.
        pass
```

---

## 5. Modular Evaluator Metrics

Each metric is isolated. If we want to add a new metric (e.g., "Degree Match" or "Company Size"), we simply create a new class that inherits from `BaseMetric` and add it to the `JobEvaluator`. No core logic needs to change.

```python
from abc import ABC, abstractmethod

class BaseMetric(ABC):
    def __init__(self, weight: float):
        self.weight = weight

    @abstractmethod
    def calculate(self, job: ParsedJob, profile: UserProfile) -> MetricScore:
        pass

# Metric 1: Skill Match (Math/Logic, NO AI)
class SkillMatchMetric(BaseMetric):
    def calculate(self, job: ParsedJob, profile: UserProfile) -> MetricScore:
        # Example logic: Overlap between job.required_skills and profile.core_skills
        matched = set(job.required_skills).intersection(set(profile.core_skills))
        score = len(matched) / len(job.required_skills) if job.required_skills else 1.0
        return MetricScore(
            metric_name="Skill Match", 
            score=score, 
            weight=self.weight, 
            reasoning=f"Matched {len(matched)} skills."
        )

# Metric 2: Experience Match (Math/Logic, NO AI)
class ExperienceMetric(BaseMetric):
    def calculate(self, job: ParsedJob, profile: UserProfile) -> MetricScore:
        if profile.years_of_experience >= job.minimum_years_experience:
            score = 1.0
        else:
            score = max(0, 1.0 - (job.minimum_years_experience - profile.years_of_experience) * 0.2)
        return MetricScore(
            metric_name="Experience Match", 
            score=score, 
            weight=self.weight, 
            reasoning=f"Needs {job.minimum_years_experience}y, user has {profile.years_of_experience}y."
        )

# The Main Evaluator
class JobEvaluator:
    def __init__(self, metrics: List[BaseMetric]):
        self.metrics = metrics
        
    def evaluate(self, job: ParsedJob, profile: UserProfile) -> JobEvaluation:
        metric_scores = [m.calculate(job, profile) for m in self.metrics]
        
        # Calculate weighted average
        total_weight = sum(m.weight for m in self.metrics)
        final_score = sum(m.score * m.weight for m in metric_scores) / total_weight
        
        return JobEvaluation(
            raw_job_id="placeholder", 
            total_score=final_score * 100, 
            metrics=metric_scores, 
            is_passed=(final_score * 100) >= 75.0
        )
```

---

## 6. The Pipeline (Connecting it to the Database)

This is the orchestrator that brings it all together.

```python
def run_discovery_pipeline(source: BaseJobSource, profile: UserProfile, extractor: JobExtractor, evaluator: JobEvaluator):
    # 1. Fetch raw jobs (NO AI)
    raw_jobs = source.fetch_jobs(profile.target_titles, profile.preferred_location_type)
    
    for raw_job in raw_jobs:
        # 2. Extract metrics (✅ AI USED)
        parsed_job = extractor.extract(raw_job)
        
        # 3. Score the job (NO AI)
        evaluation = evaluator.evaluate(parsed_job, profile)
        
        # 4. Save to Database
        if evaluation.is_passed:
            # TODO: db.session.add(job) -> Only save winners
            print(f"Saved Job: {raw_job.title} | Score: {evaluation.total_score}")
        else:
            print(f"Discarded Job: {raw_job.title} | Score: {evaluation.total_score}")
```
