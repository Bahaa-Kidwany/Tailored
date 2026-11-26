import os
import json
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path

from app.models.job import RawJob, compute_canonical_hash
from app.schemas.search_request import SearchRequest, SearchLocation
from app.scrapers.base import BaseJobSource
from app.scrapers.apify_linkedin import (
    ApifyLinkedInSource,
    ApifyLinkedInPostsSource,
    DEFAULT_APIFY_MAX_ITEMS_CAP,
)
from app.scrapers.wuzzuf_scraper import WuzzufScraperSource

logger = logging.getLogger(__name__)

class IngestionEngine:
    """
    Coordinates multi-source job fetching, fan-out across multiple locations,
    negative keyword filtering, and cross-source canonical deduplication.
    Strictly deterministic - zero AI / zero LLM reasoning.
    """

    def __init__(self, sources: Optional[List[BaseJobSource]] = None):
        self.sources = sources if sources is not None else [
            ApifyLinkedInSource(),
            ApifyLinkedInPostsSource(),
            WuzzufScraperSource(fetch_full_details=False)  # Lightweight card extraction by default
        ]

    def execute_search(self, request: SearchRequest) -> List[RawJob]:
        """
        Executes job ingestion across all enabled sources and target locations.
        Enforces a strict total cap (default: 2 items) per Apify actor to protect the $5 credit limit.
        """
        all_raw_jobs: List[RawJob] = []
        apify_cap = min(
            int(os.getenv("APIFY_MAX_ITEMS_PER_ACTOR", str(DEFAULT_APIFY_MAX_ITEMS_CAP))),
            getattr(request.constraints, "apify_max_items_per_actor", DEFAULT_APIFY_MAX_ITEMS_CAP),
        )

        logger.info(
            "Starting ingestion search for persona='%s', query_terms=%s across %d locations (Apify cap=%d per actor).",
            request.persona_id, request.query_terms, len(request.target_locations), apify_cap
        )

        # 1. Fan-out across sources and locations
        for source in self.sources:
            # Check if source is enabled
            if isinstance(source, ApifyLinkedInSource) and not request.enabled_sources.enable_linkedin:
                continue
            if isinstance(source, ApifyLinkedInPostsSource) and not getattr(request.enabled_sources, "enable_linkedin_posts", True):
                continue
            if isinstance(source, WuzzufScraperSource) and not request.enabled_sources.enable_wuzzuf:
                continue

            is_apify_source = isinstance(source, (ApifyLinkedInSource, ApifyLinkedInPostsSource))
            fetched_for_this_source = 0

            for loc in request.target_locations:
                if is_apify_source and fetched_for_this_source >= apify_cap:
                    logger.info(
                        "Reached Apify credit protection cap (%d items) for %s; skipping remaining locations.",
                        apify_cap,
                        source.__class__.__name__,
                    )
                    break

                remaining_apify_budget = max(1, apify_cap - fetched_for_this_source)
                max_items_for_call = (
                    min(request.constraints.max_results_per_source_per_location, remaining_apify_budget)
                    if is_apify_source
                    else request.constraints.max_results_per_source_per_location
                )

                try:
                    logger.info(
                        "Querying %s for location='%s' (max_items=%d)...",
                        source.__class__.__name__,
                        loc.query_string,
                        max_items_for_call,
                    )
                    jobs = source.fetch_jobs(
                        keywords=request.query_terms,
                        location=loc.query_string,
                        max_items=max_items_for_call,
                        date_posted=request.date_posted_filter,
                        remote=loc.is_remote
                    )
                    if is_apify_source:
                        jobs = jobs[:remaining_apify_budget]
                        fetched_for_this_source += len(jobs)
                    all_raw_jobs.extend(jobs)
                except Exception as exc:
                    logger.error("Source %s failed for location %s: %s", source.__class__.__name__, loc.query_string, exc)

                # For Apify actors during testing, run at most once on the primary location to avoid multiple actor invocations
                if is_apify_source:
                    break

        logger.info("Raw fetch complete: gathered %d total records before deduplication.", len(all_raw_jobs))

        # 2. Filter out negative keywords (e.g. unpaid, internship)
        filtered_jobs = self._filter_negative_keywords(all_raw_jobs, request.constraints.exclude_keywords)

        # 3. Canonical Deduplication
        deduplicated_jobs = self._deduplicate_jobs(filtered_jobs)

        logger.info(
            "Ingestion pipeline finished. Result: %d unique, high-signal raw jobs.",
            len(deduplicated_jobs)
        )
        return deduplicated_jobs

    def _filter_negative_keywords(self, jobs: List[RawJob], exclude_keywords: List[str]) -> List[RawJob]:
        """Excludes postings whose title or description contains dealbreaker keywords."""
        if not exclude_keywords:
            return jobs

        clean_jobs: List[RawJob] = []
        lowered_excludes = [k.lower().strip() for k in exclude_keywords if k.strip()]

        for job in jobs:
            text_to_check = f"{job.title} {job.raw_description}".lower()
            if any(term in text_to_check for term in lowered_excludes):
                logger.debug("Discarding job '%s' at '%s' due to excluded keyword.", job.title, job.company_name)
                continue
            clean_jobs.append(job)

        return clean_jobs

    def _deduplicate_jobs(self, jobs: List[RawJob]) -> List[RawJob]:
        """
        Deduplicates jobs based on canonical_hash.
        Merges alternate source links into primary job's source_metadata.
        """
        unique_jobs: Dict[str, RawJob] = {}

        for job in jobs:
            chash = job.canonical_hash or compute_canonical_hash(job.company_name, job.title, job.location)
            
            if chash in unique_jobs:
                # Merge source links
                existing = unique_jobs[chash]
                alt_sources = existing.source_metadata.setdefault("alternate_sources", [])
                alt_sources.append({
                    "source_type": job.source_type,
                    "url": job.url,
                    "source_id": job.source_id
                })
                logger.debug("Merged duplicate job '%s' from %s into existing record.", job.title, job.source_type)
            else:
                unique_jobs[chash] = job

        return list(unique_jobs.values())

    @staticmethod
    def save_results_to_json(jobs: List[RawJob], output_path: str) -> None:
        """Serializes raw job list into a formatted JSON test file."""
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        
        serialized = [job.model_dump(mode="json") for job in jobs]
        with open(target, "w", encoding="utf-8") as f:
            json.dump(serialized, f, indent=2, ensure_ascii=False)
        logger.info("Saved %d raw jobs to '%s'.", len(jobs), output_path)
