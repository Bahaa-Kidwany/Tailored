import json
from typing import List
from sqlmodel import Session
from app.core.database import engine
from app.models.job import UserProfile, JobDB
from app.scrapers.base import BaseJobSource
from app.ai.extractor.llm_extractor import JobExtractor
from app.evaluator.engine import JobEvaluator

def run_discovery_pipeline(
    sources: List[BaseJobSource], 
    profile: UserProfile, 
    extractor: JobExtractor, 
    evaluator: JobEvaluator
) -> List[JobDB]:
    """
    The main Closed-Loop discovery pipeline.
    1. Fetches raw jobs from all configured sources.
    2. Extracts structured metrics via LLM.
    3. Evaluates candidates using deterministic mathematical metrics.
    4. Filters and persists high-fit jobs into the database.
    """
    print(f"--- Starting Discovery Pipeline for {profile.target_titles} ---")
    
    all_raw_jobs = []
    for source in sources:
        jobs = source.fetch_jobs(keywords=profile.target_titles, location=profile.preferred_location_type)
        all_raw_jobs.extend(jobs)
        
    print(f"Fetched {len(all_raw_jobs)} total raw jobs.")
    print("-" * 40)
    
    saved_jobs: List[JobDB] = []
    discarded_count = 0
    
    with Session(engine, expire_on_commit=False) as session:
        for raw_job in all_raw_jobs:
            # Step 2: Structured LLM Extraction
            parsed_job = extractor.extract(raw_job)
            
            # Step 3: Deterministic Metric Scoring
            evaluation = evaluator.evaluate(raw_job_id=raw_job.source_id, job=parsed_job, profile=profile)
            
            # Step 4: Filtering & Database Persistence
            if evaluation.is_passed:
                job_record = JobDB(
                    source_id=raw_job.source_id,
                    title=raw_job.title,
                    company_name=raw_job.company_name,
                    location=raw_job.location,
                    url=raw_job.url,
                    raw_description=raw_job.raw_description,
                    fit_score=evaluation.total_score,
                    parsed_job_json=parsed_job.model_dump_json(),
                    evaluation_json=evaluation.model_dump_json(),
                )
                session.add(job_record)
                session.commit()
                session.refresh(job_record)
                saved_jobs.append(job_record)

                print(f"✅ PASSED & SAVED (ID: {job_record.id}) | Score: {evaluation.total_score:.1f}% | Title: {raw_job.title}")
                for m in evaluation.metrics:
                    print(f"   -> [{m.metric_name}]: {m.score * 100:.0f}% ({m.reasoning})")
            else:
                discarded_count += 1
                print(f"❌ DISCARDED | Score: {evaluation.total_score:.1f}% | Title: {raw_job.title}")
                for m in evaluation.metrics:
                    print(f"   -> [{m.metric_name}]: {m.score * 100:.0f}% ({m.reasoning})")
                    
            print("-" * 40)
            
    print(f"Pipeline Complete! Saved: {len(saved_jobs)}, Discarded: {discarded_count}")
    return saved_jobs

# --- SCRIPT RUNNER ---
if __name__ == "__main__":
    from app.core.database import init_db
    from app.scrapers.mock_scrapers import LinkedInMockSource, WuzzufMockSource
    from app.evaluator.metrics import SkillMatchMetric, ExperienceMetric, LocationMetric
    
    init_db()
    
    my_profile = UserProfile(
        target_titles=["Data Scientist", "Data Analyst"],
        core_skills=["Python", "SQL", "Pandas"],
        years_of_experience=2,
        preferred_location_type="Remote"
    )
    
    sources = [LinkedInMockSource(), WuzzufMockSource()]
    extractor = JobExtractor()
    evaluator = JobEvaluator(
        metrics=[
            SkillMatchMetric(weight=4.0),
            ExperienceMetric(weight=2.0),
            LocationMetric(weight=2.0)
        ],
        passing_threshold=65.0
    )
    
    run_discovery_pipeline(sources, my_profile, extractor, evaluator)
