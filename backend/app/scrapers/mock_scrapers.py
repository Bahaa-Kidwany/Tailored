from typing import List
import uuid
from app.models.domain_models import RawJob
from app.scrapers.base import BaseJobSource

class LinkedInMockSource(BaseJobSource):
    """Mock implementation of a LinkedIn scraper."""
    
    def fetch_jobs(self, keywords: List[str], location: str) -> List[RawJob]:
        print(f"[LinkedInScraper] Fetching jobs for keywords: {keywords} in {location}")
        
        # Mocking a response
        return [
            RawJob(
                source_id=f"linkedin_{uuid.uuid4().hex[:8]}",
                title="Senior Data Scientist",
                url="https://linkedin.com/jobs/view/123",
                raw_description="We are looking for a Senior Data Scientist with 5+ years of Python, SQL, and ML experience. Remote work is allowed.",
                company_name="TechCorp Inc.",
                location=location
            ),
            RawJob(
                source_id=f"linkedin_{uuid.uuid4().hex[:8]}",
                title="Junior Python Developer",
                url="https://linkedin.com/jobs/view/124",
                raw_description="Entry level role for a Python developer. Must know basics of web dev. On-site in Cairo.",
                company_name="StartupX",
                location=location
            )
        ]

class WuzzufMockSource(BaseJobSource):
    """Mock implementation of a Wuzzuf scraper."""
    
    def fetch_jobs(self, keywords: List[str], location: str) -> List[RawJob]:
        print(f"[WuzzufScraper] Fetching jobs for keywords: {keywords} in {location}")
        
        return [
            RawJob(
                source_id=f"wuzzuf_{uuid.uuid4().hex[:8]}",
                title="Data Analyst",
                url="https://wuzzuf.net/jobs/p/123",
                raw_description="Data Analyst needed. Skills: SQL, Excel, basic Python. 1 year experience required. Hybrid.",
                company_name="DataCo",
                location=location
            )
        ]
