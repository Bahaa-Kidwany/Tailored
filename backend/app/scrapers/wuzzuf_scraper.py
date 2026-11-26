import re
import logging
from typing import List, Optional, Dict, Any
from urllib.parse import quote_plus, urljoin
import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import BaseJobSource
from app.models.job import RawJob

logger = logging.getLogger(__name__)

class WuzzufScraperSource(BaseJobSource):
    """
    Direct HTTP scraper for Wuzzuf (Egypt and MENA's primary white-collar job portal).
    Uses lightweight HTTP client and fast HTML parsing without browser overhead.
    """

    BASE_URL = "https://wuzzuf.net"
    SEARCH_URL = "https://wuzzuf.net/search/jobs/"
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    def __init__(self, fetch_full_details: bool = True, request_timeout: int = 15):
        self.fetch_full_details = fetch_full_details
        self.request_timeout = request_timeout
        self.headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
            "Referer": "https://wuzzuf.net/jobs/egypt",
        }

    def fetch_jobs(
        self, 
        keywords: List[str], 
        location: str,
        max_items: int = 20,
        **kwargs
    ) -> List[RawJob]:
        """
        Fetches jobs from Wuzzuf matching given keywords and location.
        """
        query_str = " ".join(keywords) if keywords else ""
        if not query_str:
            return []

        # Build search query
        search_params: Dict[str, Any] = {
            "q": query_str,
            "a": "hpb"
        }

        # Check if location contains country
        loc_lower = location.lower()
        if "saudi" in loc_lower or "riyadh" in loc_lower or "ksa" in loc_lower:
            search_params["filters[country][0]"] = "Saudi Arabia"
        elif "egypt" in loc_lower or "cairo" in loc_lower or "alexandria" in loc_lower:
            search_params["filters[country][0]"] = "Egypt"
        elif "uae" in loc_lower or "dubai" in loc_lower:
            search_params["filters[country][0]"] = "United Arab Emirates"

        logger.info("Scraping Wuzzuf with params=%s, max_items=%d", search_params, max_items)

        try:
            with httpx.Client(headers=self.headers, timeout=self.request_timeout, follow_redirects=True) as client:
                response = client.get(self.SEARCH_URL, params=search_params)
                if response.status_code != 200:
                    logger.warning("Wuzzuf search returned status code %d", response.status_code)
                    return []

                html = response.text
                card_jobs = self._parse_search_cards(html, client, max_items)
                logger.info("Successfully scraped %d jobs from Wuzzuf.", len(card_jobs))
                return card_jobs

        except Exception as exc:
            logger.error("Error scraping Wuzzuf: %s", exc, exc_info=True)
            return []

    def _parse_search_cards(self, html: str, client: httpx.Client, max_items: int) -> List[RawJob]:
        """Parses job listing cards from the Wuzzuf search results page."""
        raw_jobs: List[RawJob] = []
        soup = BeautifulSoup(html, "html.parser")

        # Wuzzuf cards typically have links matching /jobs/p/<id>-<slug>
        job_links = soup.find_all("a", href=re.compile(r"/jobs/p/"))
        seen_urls = set()

        for link_elem in job_links:
            if len(raw_jobs) >= max_items:
                break

            href = link_elem.get("href", "")
            if not href or href in seen_urls:
                continue

            full_url = urljoin(self.BASE_URL, href)
            seen_urls.add(href)
            seen_urls.add(full_url)

            title = link_elem.get_text(strip=True)
            if not title:
                continue

            # Extract job ID from URL (e.g. /jobs/p/12345-python-dev)
            match = re.search(r"/jobs/p/([0-9a-zA-Z]+)", href)
            job_id_str = match.group(1) if match else str(hash(full_url))

            # Find parent card container
            card = link_elem.find_parent("div", class_=re.compile(r"css-")) or link_elem.find_parent("div")
            company_name = "Unknown Company"
            location = "Egypt"
            teaser_description = ""

            if card:
                # Company name is usually in an anchor tag with /jobs/careers/
                company_elem = card.find("a", href=re.compile(r"/jobs/careers/"))
                if company_elem:
                    company_name = company_elem.get_text(strip=True).replace("-", " ")

                # Location is usually in a span inside card
                loc_elem = card.find("span", class_=re.compile(r"location|city|country", re.I))
                if loc_elem:
                    location = loc_elem.get_text(strip=True)
                else:
                    # Look for text with comma e.g. "Cairo, Egypt"
                    for span in card.find_all("span"):
                        span_text = span.get_text(strip=True)
                        if "egypt" in span_text.lower() or "cairo" in span_text.lower() or "saudi" in span_text.lower():
                            location = span_text
                            break

                # Extract card description snippet
                desc_elem = card.find("div", class_=re.compile(r"description|details", re.I))
                if desc_elem:
                    teaser_description = desc_elem.get_text(separator=" ", strip=True)

            # Fetch full page description if enabled
            if self.fetch_full_details:
                full_desc = self._fetch_full_job_description(client, full_url)
                if full_desc and len(full_desc) > 100:
                    raw_desc = full_desc
                else:
                    raw_desc = teaser_description or f"Position: {title} at {company_name}. Location: {location}."
            else:
                raw_desc = teaser_description or f"Position: {title} at {company_name}. Location: {location}."

            raw_jobs.append(
                RawJob(
                    source_type="wuzzuf",
                    source_id=f"wuzzuf_{job_id_str}",
                    title=title,
                    company_name=company_name,
                    location=location,
                    url=full_url,
                    raw_description=raw_desc,
                    source_metadata={"wuzzuf_id": job_id_str}
                )
            )

        return raw_jobs

    def _fetch_full_job_description(self, client: httpx.Client, url: str) -> Optional[str]:
        """Fetches full job description and requirements from the Wuzzuf single job page."""
        try:
            resp = client.get(url, timeout=self.request_timeout)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                collected = []
                for sec in soup.find_all("section"):
                    txt = sec.get_text(separator="\n", strip=True)
                    lower_txt = txt[:80].lower()
                    if any(header in lower_txt for header in [
                        "job description", "job requirements", "about the job", 
                        "what we expect", "responsibilities", "what we offer", "skills"
                    ]):
                        collected.append(txt)
                if collected:
                    return "\n\n".join(collected)[:10000]

                # Fallback to main or article element
                main_elem = soup.find("main") or soup.find("article")
                if main_elem:
                    return main_elem.get_text(separator="\n", strip=True)[:10000]
        except Exception as exc:
            logger.warning("Could not fetch full Wuzzuf description from %s: %s", url, exc)
        return None
