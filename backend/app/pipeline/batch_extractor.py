import os
import json
import time
import logging
from typing import List, Optional
from pathlib import Path

from app.models.job import RawJob
from app.schemas.job_insights import ExtractedJobRecord
from app.ai.extractor.fast_extractor import FastJobExtractor

logger = logging.getLogger(__name__)

class BatchJobExtractor:
    """
    Orchestrates batch extraction across a list of raw job records.
    Provides timing metrics and writes formatted JSON output.
    """

    def __init__(self, extractor: Optional[FastJobExtractor] = None, delay_between_calls: float = 0.5):
        self.extractor = extractor or FastJobExtractor()
        self.delay_between_calls = delay_between_calls

    def process_raw_jobs(self, raw_jobs: List[RawJob]) -> List[ExtractedJobRecord]:
        """
        Processes a list of RawJob domain models and returns structured ExtractedJobRecord instances.
        """
        extracted_records: List[ExtractedJobRecord] = []
        total = len(raw_jobs)
        logger.info("Starting batch extraction for %d raw jobs using %s...", total, self.extractor.model_name)

        start_time = time.perf_counter()

        for idx, raw_job in enumerate(raw_jobs, start=1):
            job_start = time.perf_counter()
            logger.info("[%d/%d] Extracting insights for: '%s' at '%s'", idx, total, raw_job.title, raw_job.company_name)
            
            try:
                record = self.extractor.extract(raw_job)
                extracted_records.append(record)
                job_elapsed = time.perf_counter() - job_start
                logger.info(
                    "[%d/%d] Completed in %.2fs -> Normalized Title: '%s', Skills: %s",
                    idx, total, job_elapsed,
                    record.extracted_insights.normalized_title,
                    record.extracted_insights.skills_and_technologies.mandatory_skills[:4]
                )
            except Exception as exc:
                logger.error("[%d/%d] Failed extracting job '%s': %s", idx, total, raw_job.title, exc)

            if idx < total and self.delay_between_calls > 0:
                time.sleep(self.delay_between_calls)

        total_elapsed = time.perf_counter() - start_time
        avg_time = (total_elapsed / total) if total > 0 else 0
        logger.info(
            "Batch extraction finished: %d jobs processed in %.2fs (Average: %.2fs/job)",
            len(extracted_records), total_elapsed, avg_time
        )
        return extracted_records

    def process_file_to_file(self, input_path: str, output_path: str) -> List[ExtractedJobRecord]:
        """
        Reads input JSON containing RawJob records, extracts insights,
        and saves the resulting ExtractedJobRecord list into output_path.
        """
        in_file = Path(input_path)
        if not in_file.exists():
            raise FileNotFoundError(f"Input raw jobs file not found: {input_path}")

        with open(in_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        raw_jobs = [RawJob.model_validate(item) for item in data]
        records = self.process_raw_jobs(raw_jobs)

        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        serialized = [rec.model_dump(mode="json") for rec in records]
        
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(serialized, f, indent=2, ensure_ascii=False)

        logger.info("Saved %d extracted job insights records to '%s'.", len(records), output_path)
        return records
