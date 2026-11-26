import sys
import json
import time
import logging
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

load_dotenv(BASE_DIR / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TestExtraction")

from app.models.job import RawJob
from app.schemas.job_insights import JobInsights, ExtractedJobRecord
from app.ai.extractor.fast_extractor import FastJobExtractor
from app.pipeline.batch_extractor import BatchJobExtractor

FIXTURES_DIR = BASE_DIR / "tests" / "fixtures"

def test_single_job_extraction():
    logger.info("--- [STEP 1] Testing Single Job Extraction via Lite LLM ---")
    raw_jobs_path = FIXTURES_DIR / "fetched_raw_jobs.json"
    assert raw_jobs_path.exists(), f"Raw jobs fixture missing at {raw_jobs_path}"

    with open(raw_jobs_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Pick the first technical job (e.g. Middle FullStack Python Developer)
    sample_raw = RawJob.model_validate(data[0])
    logger.info("Raw Input Title: '%s' at '%s'", sample_raw.title, sample_raw.company_name)

    extractor = FastJobExtractor()
    t0 = time.perf_counter()
    record = extractor.extract(sample_raw)
    elapsed = time.perf_counter() - t0

    insights = record.extracted_insights
    logger.info("✓ Extraction Latency: %.2f seconds", elapsed)
    logger.info("✓ Normalized Title: '%s'", insights.normalized_title)
    logger.info("✓ Seniority: %s | Work Mode: %s", insights.seniority_level, insights.work_mode)
    logger.info("✓ Min Years Experience: %d", insights.experience_requirements.minimum_years)
    logger.info("✓ Mandatory Skills: %s", insights.skills_and_technologies.mandatory_skills)
    logger.info("✓ Nice-to-have Skills: %s", insights.skills_and_technologies.nice_to_have_skills)
    logger.info("✓ Core Responsibilities: %s", insights.core_responsibilities[:2])

    assert insights.normalized_title, "Normalized title should not be empty"
    assert isinstance(insights.experience_requirements.minimum_years, int)
    assert insights.work_mode in ["Remote", "Hybrid", "On-site"]
    return record

def test_batch_extraction_and_file_dump():
    logger.info("\n--- [STEP 2] Testing Batch Extraction & JSON File Output ---")
    raw_jobs_path = FIXTURES_DIR / "fetched_raw_jobs.json"
    output_path = FIXTURES_DIR / "extracted_job_insights.json"

    with open(raw_jobs_path, "r", encoding="utf-8") as f:
        all_raw_data = json.load(f)

    # Process first 3 diverse jobs (Wuzzuf technical job, Nile Bits Python dev, LinkedIn position)
    selected_jobs = [RawJob.model_validate(item) for item in all_raw_data[:3]]
    logger.info("Processing batch of %d diverse jobs...", len(selected_jobs))

    batch_runner = BatchJobExtractor(delay_between_calls=0.3)
    t0 = time.perf_counter()
    extracted_records = batch_runner.process_raw_jobs(selected_jobs)
    total_elapsed = time.perf_counter() - t0

    assert len(extracted_records) == len(selected_jobs)

    # Save to extracted_job_insights.json
    serialized = [rec.model_dump(mode="json") for rec in extracted_records]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(serialized, f, indent=2, ensure_ascii=False)

    logger.info("✓ Saved %d extracted records to: %s", len(extracted_records), output_path)
    logger.info("✓ Total Batch Elapsed: %.2fs (Avg: %.2fs per job)", total_elapsed, total_elapsed / len(selected_jobs))

    # Re-read and assert structure
    with open(output_path, "r", encoding="utf-8") as f:
        saved_data = json.load(f)

    assert len(saved_data) == 3
    for entry in saved_data:
        assert "source_id" in entry
        assert "canonical_hash" in entry
        assert "extracted_insights" in entry
        ins = entry["extracted_insights"]
        assert "normalized_title" in ins
        assert "skills_and_technologies" in ins
        assert "experience_requirements" in ins

    logger.info("✓ Verified output schema and field integrity in extracted_job_insights.json")

def run_all_tests():
    logger.info("============================================================")
    logger.info("    RUNNING FAST LITE LLM JOB EXTRACTION TEST HARNESS       ")
    logger.info("============================================================")
    test_single_job_extraction()
    test_batch_extraction_and_file_dump()
    logger.info("\n============================================================")
    logger.info("             EXTRACTION PIPELINE TESTS PASSED!              ")
    logger.info("============================================================")

if __name__ == "__main__":
    run_all_tests()
