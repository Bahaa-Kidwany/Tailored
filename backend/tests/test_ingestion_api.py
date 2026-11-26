import os
import sys
import json
import logging
from pathlib import Path
import pytest
from dotenv import load_dotenv

# Ensure backend root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Load .env
load_dotenv(BASE_DIR / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TestIngestion")

from app.schemas.user_profile import UserProfile
from app.schemas.search_request import SearchRequest
from app.pipeline.query_generator import QueryGenerator
from app.models.job import RawJob, compute_canonical_hash
from app.scrapers.wuzzuf_scraper import WuzzufScraperSource
from app.scrapers.apify_linkedin import ApifyLinkedInSource, ApifyLinkedInPostsSource
from app.pipeline.ingestion_engine import IngestionEngine

FIXTURES_DIR = BASE_DIR / "tests" / "fixtures"

@pytest.fixture
def profile() -> UserProfile:
    profile_path = FIXTURES_DIR / "sample_user_profile.json"
    with open(profile_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return UserProfile.model_validate(data)

def test_user_profile_parsing(profile: UserProfile):
    logger.info("--- [STEP 1] Testing UserProfile Parsing & Regional Contacts ---")
    assert profile.personal_info.full_name == "Ahmed El-Sayed"
    
    # Test regional contact resolution
    sa_contact = profile.personal_info.get_contact_for_country("SA")
    assert sa_contact is not None, "Failed to resolve Saudi contact number"
    assert sa_contact.dial_code == "+966", f"Expected +966, got {sa_contact.dial_code}"
    logger.info("✓ Resolved Saudi Contact: %s %s (%s)", sa_contact.dial_code, sa_contact.phone_number, sa_contact.label)

    eg_contact = profile.personal_info.get_contact_for_country("EG")
    assert eg_contact is not None, "Failed to resolve Egypt contact number"
    assert eg_contact.dial_code == "+20", f"Expected +20, got {eg_contact.dial_code}"
    logger.info("✓ Resolved Egypt Contact: %s %s (%s)", eg_contact.dial_code, eg_contact.phone_number, eg_contact.label)

    # Test active search locations
    active_locs = profile.get_active_search_locations()
    assert len(active_locs) == 3, f"Expected 3 active locations, got {len(active_locs)}"
    loc_names = [f"{l.city}, {l.country}" for l in active_locs]
    logger.info("✓ Active Target Locations: %s", loc_names)

    # Test career personas
    primary_persona = profile.get_primary_persona()
    assert primary_persona is not None
    assert primary_persona.target_title == "Data Scientist"
    logger.info("✓ Primary Persona: '%s' with %d skills and %d projects",
                primary_persona.target_title,
                len(primary_persona.skills_and_tools.core_skills),
                len(primary_persona.featured_projects))

def test_query_generator(profile: UserProfile):
    logger.info("\n--- [STEP 2] Testing QueryGenerator from Profile & Persona ---")
    
    # Generate request for primary persona
    request = QueryGenerator.generate_search_request(
        profile=profile,
        persona_id="data_scientist_track",
        date_posted="past-24h",
        max_results_per_location=5
    )

    assert request.persona_id == "data_scientist_track"
    assert "Data Scientist" in request.query_terms
    assert "Machine Learning Engineer" in request.query_terms
    assert len(request.target_locations) == 3
    
    logger.info("✓ Generated Query Terms: %s", request.query_terms)
    logger.info("✓ Target Locations: %s", [loc.query_string for loc in request.target_locations])
    logger.info("✓ Seniority Filter: %s", request.seniority_filter)
    logger.info("✓ Negative Keywords: %s", request.constraints.exclude_keywords)

    return request

def test_wuzzuf_scraper():
    logger.info("\n--- [STEP 3] Testing Wuzzuf HTTP Scraper (Full Description Fetch) ---")
    scraper = WuzzufScraperSource(fetch_full_details=True)
    
    # Test a targeted search query for Cairo
    results = scraper.fetch_jobs(keywords=["Python"], location="Cairo, Egypt", max_items=3)
    logger.info("✓ Wuzzuf Scraper returned %d jobs with full descriptions.", len(results))
    
    for idx, job in enumerate(results, start=1):
        logger.info("   [%d] %s at %s (%s) - Description Length: %d chars", 
                    idx, job.title, job.company_name, job.location, len(job.raw_description))
        assert job.source_type == "wuzzuf"
        assert job.canonical_hash is not None
        assert job.title
        assert job.company_name
        assert len(job.raw_description) > 300, f"Expected full description (>300 chars), got {len(job.raw_description)}"

    return results

def test_apify_linkedin_scraper():
    logger.info("\n--- [STEP 4] Testing Apify LinkedIn Scraper Actors (Max 2 Items Cap per API) ---")
    api_token = os.getenv("APIFY_API_TOKEN")
    actor_id = os.getenv("APIFY_LINKEDIN_ACTOR_ID", "curious_coder/linkedin-jobs-scraper")
    posts_actor_id = os.getenv("APIFY_LINKEDIN_POSTS_ACTOR_ID", "codetr/linkedin-hiring-posts-scraper")

    if not api_token or "your_" in api_token:
        logger.warning("No valid APIFY_API_TOKEN configured. Skipping live Apify call.")
        return []

    logger.info("Found Apify Token. Initializing ApifyLinkedInSource (%s) & ApifyLinkedInPostsSource (%s) with max_items_cap=2", actor_id, posts_actor_id)
    source = ApifyLinkedInSource(api_token=api_token, actor_id=actor_id, timeout_secs=90, max_items_cap=2)
    posts_source = ApifyLinkedInPostsSource(api_token=api_token, actor_id=posts_actor_id, timeout_secs=90, max_items_cap=2)
    assert source.max_items_cap == 2
    assert posts_source.max_items_cap == 2
    
    # Check if a recent dataset exists from previous runs to read instantaneously without re-burning run quota
    from apify_client import ApifyClient
    client = ApifyClient(api_token)
    recent_runs = client.runs().list(limit=5).items
    dataset_id = None
    for r in recent_runs:
        if r.status == "SUCCEEDED" and r.default_dataset_id:
            dataset_id = r.default_dataset_id
            break

    results: List[RawJob] = []
    if dataset_id:
        logger.info("Reading up to 2 live LinkedIn jobs from recent Apify dataset '%s'...", dataset_id)
        for item in client.dataset(dataset_id).iterate_items(limit=2):
            if len(results) >= 2:
                break
            job = source._map_apify_item_to_raw_job(item, fallback_location="Cairo, Egypt")
            if job:
                results.append(job)
    else:
        logger.info("No prior successful dataset found. Triggering live Apify Jobs Actor call (max_items=2)...")
        results = source.fetch_jobs(
            keywords=["Python Developer"],
            location="Cairo, Egypt",
            max_items=2,
            date_posted="past-24h"
        )

    logger.info("✓ Apify LinkedIn Source returned %d jobs (capped at 2).", len(results))
    assert len(results) <= 2, f"Expected at most 2 jobs from Apify, got {len(results)}"
    for idx, job in enumerate(results, start=1):
        logger.info("   [%d] %s at %s (%s) - URL: %s", 
                    idx, job.title, job.company_name, job.location, job.url)
        assert job.source_type == "linkedin_apify"
        assert job.canonical_hash is not None

    return results

def test_canonical_deduplication():
    logger.info("\n--- [STEP 5] Testing Cross-Source Canonical Deduplication ---")
    engine = IngestionEngine(sources=[])

    # Simulate same job posted on both LinkedIn and Wuzzuf
    job_linkedin = RawJob(
        source_type="linkedin_apify",
        source_id="linkedin_101",
        title="Senior Python Developer",
        company_name="Vodafone Egypt",
        location="Cairo, Egypt",
        url="https://linkedin.com/jobs/view/101",
        raw_description="We are hiring a Senior Python Developer with Django experience."
    )

    job_wuzzuf = RawJob(
        source_type="wuzzuf",
        source_id="wuzzuf_202",
        title="Senior Python Developer",
        company_name="Vodafone Egypt",
        location="Cairo, Egypt",
        url="https://wuzzuf.net/jobs/p/202",
        raw_description="Vodafone Egypt is looking for a Senior Python Developer."
    )

    # Different job
    job_swvl = RawJob(
        source_type="wuzzuf",
        source_id="wuzzuf_303",
        title="Data Engineer",
        company_name="Swvl",
        location="Cairo, Egypt",
        url="https://wuzzuf.net/jobs/p/303",
        raw_description="Swvl is looking for a Data Engineer."
    )

    # Job with excluded keyword
    job_unpaid = RawJob(
        source_type="wuzzuf",
        source_id="wuzzuf_404",
        title="Unpaid Python Internship",
        company_name="Startup X",
        location="Cairo, Egypt",
        url="https://wuzzuf.net/jobs/p/404",
        raw_description="3-month unpaid internship."
    )

    all_jobs = [job_linkedin, job_wuzzuf, job_swvl, job_unpaid]
    logger.info("Input jobs: %d", len(all_jobs))

    filtered = engine._filter_negative_keywords(all_jobs, exclude_keywords=["unpaid", "internship"])
    assert len(filtered) == 3, f"Expected 3 jobs after negative filter, got {len(filtered)}"
    logger.info("✓ Filtered out unpaid internship: %d jobs remaining", len(filtered))

    deduped = engine._deduplicate_jobs(filtered)
    assert len(deduped) == 2, f"Expected 2 unique jobs after deduplication, got {len(deduped)}"
    logger.info("✓ Deduplicated Vodafone job: %d unique jobs remaining", len(deduped))

    # Verify merged source links
    vodafone_job = [j for j in deduped if "vodafone" in j.company_name.lower()][0]
    alt_sources = vodafone_job.source_metadata.get("alternate_sources", [])
    assert len(alt_sources) == 1, "Expected 1 alternate source attached to Vodafone job"
    logger.info("✓ Alternate source merged successfully: %s", alt_sources)

    return deduped

def run_all_tests():
    logger.info("============================================================")
    logger.info("      RUNNING STORY 1 INGESTION ENGINE TEST HARNESS        ")
    logger.info("============================================================")

    # 1. Profile parsing & regional contacts
    profile = test_user_profile_parsing()

    # 2. Query generator
    request = test_query_generator(profile)

    # 3. Wuzzuf live scraper
    wuzzuf_jobs = test_wuzzuf_scraper()

    # 4. Apify LinkedIn scraper (live check)
    apify_jobs = test_apify_linkedin_scraper()

    # 5. Canonical deduplication & negative filtering
    test_canonical_deduplication()

    # 6. Save combined test artifacts
    combined_jobs = wuzzuf_jobs + apify_jobs
    output_file = FIXTURES_DIR / "fetched_raw_jobs.json"
    IngestionEngine.save_results_to_json(combined_jobs, str(output_file))
    logger.info("\n✓ Successfully dumped %d fetched raw jobs to %s", len(combined_jobs), output_file)

    logger.info("\n============================================================")
    logger.info("               ALL INGESTION TESTS PASSED!                  ")
    logger.info("============================================================")

if __name__ == "__main__":
    run_all_tests()
