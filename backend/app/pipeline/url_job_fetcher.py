import os
import re
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import httpx
from bs4 import BeautifulSoup

from app.models.job import RawJob

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

class UrlJobFetcher:
    """
    Fetches and extracts raw job posting content from any web URL,
    with specialized extractors for LinkedIn job postings, LinkedIn recruiter posts (Embed API & Apify),
    Wuzzuf, and standard career sites.
    """

    def __init__(self, request_timeout: int = 12):
        self.timeout = request_timeout
        self.headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        }

    @staticmethod
    def normalize_url(raw_url: str) -> str:
        """Cleans and normalizes URLs, removing tracking tags and ensuring https schema."""
        url = raw_url.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"

        try:
            parsed = urlparse(url)
            # Filter out tracking query params
            tracking_keys = {
                "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
                "refid", "trackingid", "trk", "midToken", "trkEmail", "eid", "rcm"
            }
            query_dict = parse_qs(parsed.query, keep_blank_values=True)
            cleaned_query = {k: v for k, v in query_dict.items() if k.lower() not in tracking_keys}
            flat_query = []
            for k, vs in cleaned_query.items():
                for v in vs:
                    flat_query.append((k, v))

            clean_parsed = parsed._replace(query=urlencode(flat_query))
            return urlunparse(clean_parsed)
        except Exception:
            return url

    def _resolve_redirects(self, url: str) -> str:
        """Resolves shortened or redirected URLs (e.g. lnkd.in, bit.ly) to the canonical destination."""
        url_low = url.lower()
        if any(short in url_low for short in ["lnkd.in", "bit.ly", "t.co", "tinyurl.com"]):
            try:
                with httpx.Client(headers=self.headers, follow_redirects=True, timeout=8) as client:
                    resp = client.head(url)
                    target = str(resp.url)
                    if target and target != url:
                        logger.info("UrlJobFetcher: resolved shortened URL '%s' -> '%s'", url, target)
                        return self.normalize_url(target)
            except Exception as e:
                logger.debug("Could not resolve redirect for '%s': %s", url, e)
        return url

    def _is_linkedin_post(self, url: str) -> bool:
        """Determines if a LinkedIn URL represents a recruiter/feed post rather than a standard job card."""
        u = url.lower()
        return any(k in u for k in [
            "/posts/", "/feed/update/", "/feed/", "activity-", "activity:", "urn:li:activity", "urn:li:share"
        ])

    def _is_valid_job_content(self, job: Optional[RawJob]) -> bool:
        """Guards against LinkedIn login walls, authwall errors, and empty text."""
        if not job:
            return False
        title_low = job.title.lower()
        desc_low = job.raw_description.lower()
        # Detect authwalls and sign-in pages
        if any(k in title_low for k in ["sign in", "login", "join linkedin", "security verification", "authwall"]):
            return False
        if any(k in desc_low[:250] for k in ["sign in to view", "sign in to see", "welcome back", "enter the code"]):
            return False
        if len(job.raw_description.strip()) < 35:
            return False
        return True

    def fetch_job(self, raw_url: str) -> RawJob:
        """
        Main entrypoint: parses URL, selects appropriate extractor, and returns a RawJob.
        """
        url = self.normalize_url(raw_url)
        url = self._resolve_redirects(url)
        url_lower = url.lower()

        logger.info("UrlJobFetcher: fetching job posting from '%s'", url)

        # 1. Specialized LinkedIn extractor
        if "linkedin.com" in url_lower or "lnkd.in" in url_lower:
            try:
                job = self._fetch_linkedin(url)
                if job and self._is_valid_job_content(job):
                    return job
            except Exception as exc:
                logger.warning("LinkedIn fetcher warning for '%s': %s", url, exc)

        # 2. Specialized Wuzzuf extractor
        if "wuzzuf.net" in url_lower:
            try:
                job = self._fetch_wuzzuf(url)
                if job:
                    return job
            except Exception as exc:
                logger.warning("Wuzzuf fetcher warning for '%s': %s", url, exc)

        # 3. Generic web page extractor (Greenhouse, Lever, Workday, Company websites)
        try:
            job = self._fetch_generic(url)
            if job:
                return job
        except Exception as exc:
            logger.warning("Generic URL fetcher warning for '%s': %s", url, exc)

        # 4. Ultimate fallback: synthesize from URL structure
        return self._fallback_from_url(url)

    def _fetch_linkedin(self, url: str) -> Optional[RawJob]:
        """
        Routes LinkedIn URLs to either recruiter post extractor or job listing extractor.
        """
        if self._is_linkedin_post(url):
            return self._fetch_linkedin_recruiter_post(url)
        return self._fetch_linkedin_job_listing(url)

    def _extract_activity_id(self, url: str) -> Optional[str]:
        """Extracts LinkedIn Activity or Share ID (15-20 digits) from post URL."""
        m = re.search(r"activity[:-](\d{15,20})", url)
        if m:
            return m.group(1)
        m2 = re.search(r"(?:urn:li:(?:activity|share):)(\d{15,20})", url)
        if m2:
            return m2.group(1)
        m3 = re.search(r"(\d{16,20})", url)
        if m3:
            return m3.group(1)
        return None

    def _fetch_linkedin_recruiter_post(self, url: str) -> Optional[RawJob]:
        """
        Extracts recruiter hiring posts without hitting LinkedIn's authwall:
        1. Uses LinkedIn's public Embed API (instant, no login).
        2. Falls back to Apify Google SERP search if Embed API is unavailable.
        3. Falls back to URL slug heuristic if network is offline.
        """
        # Extract Activity / Post ID (15-20 digits)
        activity_id = self._extract_activity_id(url)

        # 1. Try LinkedIn Public Embed API
        if activity_id:
            embed_job = self._fetch_linkedin_embed(activity_id, url)
            if embed_job and self._is_valid_job_content(embed_job):
                return embed_job

        # 2. Try Apify API (Google Search SERP scraper for LinkedIn posts)
        apify_job = self._fetch_linkedin_post_via_apify(url, activity_id)
        if apify_job and self._is_valid_job_content(apify_job):
            return apify_job

        # 3. Fallback: synthesize clean recruiter post from URL slug
        return self._fallback_linkedin_post(url, activity_id)

    def _fetch_linkedin_embed(self, activity_id: str, original_url: str) -> Optional[RawJob]:
        """
        Fetches full recruiter post text and author details via LinkedIn's official public embed endpoint.
        """
        embed_url = f"https://www.linkedin.com/embed/feed/update/urn:li:activity:{activity_id}"
        try:
            with httpx.Client(headers=self.headers, follow_redirects=True, timeout=self.timeout) as client:
                resp = client.get(embed_url)
                if resp.status_code != 200:
                    return None

                soup = BeautifulSoup(resp.text, "html.parser")
                raw_title = soup.title.get_text(strip=True) if soup.title else ""

                # Extract author from profile link or page title
                author_name = ""
                author_profile = ""
                for a in soup.find_all("a", href=True):
                    href = a.get("href", "")
                    if "/in/" in href:
                        if not author_profile:
                            author_profile = href.split("?")[0]
                        txt = a.get_text(strip=True)
                        if txt and len(txt) > 2 and not author_name:
                            author_name = txt

                if not author_name and " | " in raw_title:
                    author_name = raw_title.split(" | ")[-1].strip()

                # Extract post content text
                content_elem = soup.find(class_=re.compile(
                    r"attributed-text-segment-list__content|feed-shared-update-v2__description|share-update-card__update-text|attributed-text-segment-list__container",
                    re.I
                ))
                post_text = content_elem.get_text(separator="\n", strip=True) if content_elem else ""

                if not post_text or len(post_text) < 30:
                    main = soup.find("main") or soup.find("article") or soup.find("body")
                    if main:
                        post_text = main.get_text(separator="\n", strip=True)

                if not post_text or len(post_text) < 30 or "sign in to view" in post_text.lower():
                    return None

                # Extract candidate job role from post text or headline
                role = ""
                m_role = re.search(
                    r"(?:we(?:'re|\s+are)?\s+hiring(?:\s*:)?|hiring\s+(?:a|an)?|position\s*:|role\s*:|looking\s+for\s+(?:a|an)?)\s*([A-Za-z0-9\s/&+\-_()]+)",
                    post_text,
                    re.I
                )
                if m_role:
                    candidate_role = m_role.group(1).split("\n")[0].split("|")[0].split(" - ")[0].strip()
                    candidate_role = re.sub(r"^[^\w]+|[^\w)]+$", "", candidate_role)
                    if 3 < len(candidate_role) < 80:
                        role = candidate_role

                if not role and " | " in raw_title:
                    candidate_title = raw_title.split(" | ")[0].replace("...", "").strip()
                    candidate_title = re.sub(
                        r"^(?:we(?:'re|\s+are)?\s+hiring(?:\s*:)?\s*|hiring\s*:?\s*)",
                        "",
                        candidate_title,
                        flags=re.I
                    ).strip()
                    if 3 < len(candidate_title) < 80:
                        role = candidate_title

                if not role:
                    parsed = urlparse(original_url)
                    slug = parsed.path.strip("/").split("/")[-1]
                    slug_clean = re.sub(r"-activity-\d+.*", "", slug)
                    slug_clean = re.sub(r"^[a-zA-Z0-9]+_", "", slug_clean)
                    words = [w.capitalize() for w in re.sub(r"[-_]+", " ", slug_clean).split() if not w.isdigit()]
                    if words:
                        role = " ".join(words[:6])

                if not role:
                    role = "Recruiter Hiring Opportunity"

                title = f"{role} (Recruiter Post)" if "post" not in role.lower() else role
                company = f"{author_name} (LinkedIn Hiring Post)" if author_name else "LinkedIn Recruiter"

                # Detect location
                location = "Worldwide (Remote / Hybrid)"
                loc_match = re.search(r"(?:location\s*:|based\s+in\s*:?)\s*([^\n\r,]+(?:,\s*[^\n\r]+)?)", post_text, re.I)
                if loc_match:
                    location = loc_match.group(1).strip()
                elif "remote" in post_text.lower():
                    location = "Remote"
                elif any(c in post_text.lower() for c in ["cairo", "egypt", "giza"]):
                    location = "Cairo, Egypt"
                elif any(c in post_text.lower() for c in ["riyadh", "saudi", "dubai", "uae"]):
                    location = "Riyadh, Saudi Arabia"

                return RawJob(
                    source_type="linkedin_posts",
                    source_id=f"linkedin_post_{activity_id}",
                    title=title,
                    company_name=company,
                    location=location,
                    url=original_url,
                    raw_description=post_text,
                    source_metadata={
                        "activity_id": activity_id,
                        "author_name": author_name,
                        "author_profile": author_profile,
                        "ingestion_method": "linkedin_embed_api"
                    }
                )
        except Exception as exc:
            logger.warning("LinkedIn Embed API fetch error for activity %s: %s", activity_id, exc)
            return None

    def _fetch_linkedin_post_via_apify(self, original_url: str, activity_id: Optional[str]) -> Optional[RawJob]:
        """
        Fetches recruiter post metadata using Apify Google SERP search when direct fetch hits an authwall.
        """
        token = os.getenv("APIFY_API_TOKEN")
        if not token:
            logger.warning("No APIFY_API_TOKEN available for Apify LinkedIn post fetch.")
            return None

        try:
            from apify_client import ApifyClient
            client = ApifyClient(token)

            search_query = f'site:linkedin.com "{activity_id}"' if activity_id else f'"{original_url}"'
            logger.info("UrlJobFetcher: executing Apify SERP search for '%s'", search_query)

            run = client.actor("scraperlink/google-search-results-serp-scraper").call(
                run_input={
                    "keyword": search_query,
                    "limit": "10",
                    "include_merged": False,
                    "maxPagesPerQuery": 1
                },
                max_items=1
            )
            if not run:
                return None

            dataset_id = getattr(run, "default_dataset_id", None) or (
                run.get("defaultDatasetId") if isinstance(run, dict) else None
            )
            if not dataset_id:
                return None

            items = list(client.dataset(dataset_id).iterate_items(limit=1))
            if not items or "results" not in items[0]:
                return None

            results = items[0]["results"]
            if not results:
                return None

            first = results[0]
            raw_t = first.get("title", "LinkedIn Hiring Post").replace(" - LinkedIn", "").strip()
            desc = first.get("description", "")
            post_url = first.get("url") or original_url

            author = "LinkedIn Recruiter"
            if "'s Post" in raw_t:
                author = raw_t.split("'s Post")[0].strip()
            elif " | " in raw_t:
                author = raw_t.split(" | ")[-1].strip()

            role = raw_t.split("'s Post")[0].split(" | ")[0].strip()
            title = f"{role} (Recruiter Post)" if "post" not in role.lower() else role
            company = f"{author} (LinkedIn Hiring Post)"

            sid = activity_id or str(abs(hash(original_url)) % 10000000)
            return RawJob(
                source_type="linkedin_posts",
                source_id=f"linkedin_post_{sid}",
                title=title,
                company_name=company,
                location="Remote / Hybrid",
                url=post_url,
                raw_description=desc or f"{title} at {company}. View full post: {post_url}",
                source_metadata={
                    "activity_id": sid,
                    "author_name": author,
                    "ingestion_method": "apify_serp_api"
                }
            )
        except Exception as exc:
            logger.warning("Apify SERP fetch error for '%s': %s", original_url, exc)
            return None

    def _fallback_linkedin_post(self, original_url: str, activity_id: Optional[str]) -> RawJob:
        """
        Synthesizes a clean candidate job record from a LinkedIn post URL slug without authwall error.
        """
        parsed = urlparse(original_url)
        path_parts = [p for p in parsed.path.strip("/").split("/") if p]
        slug = path_parts[-1] if path_parts else "opportunity"

        slug_clean = re.sub(r"-activity-\d+.*", "", slug)
        author_part = slug_clean.split("_")[0] if "_" in slug_clean else ""
        content_part = slug_clean.split("_")[1] if "_" in slug_clean else slug_clean

        words = [w.capitalize() for w in re.sub(r"[-_]+", " ", content_part).split() if not w.isdigit()]
        filtered_words = [w for w in words if w.lower() not in ["hey", "folks", "we", "were", "are", "hiring", "now"]]

        title = " ".join(filtered_words) if filtered_words else "Recruiter Hiring Opportunity"
        author_name = author_part.capitalize() if author_part else "LinkedIn Recruiter"

        sid = activity_id or str(abs(hash(original_url)) % 10000000)
        return RawJob(
            source_type="linkedin_posts",
            source_id=f"linkedin_post_{sid}",
            title=f"{title} (Recruiter Post)",
            company_name=f"{author_name} (LinkedIn Hiring Post)",
            location="Remote / Hybrid",
            url=original_url,
            raw_description=(
                f"Position: {title} (LinkedIn Recruiter Hiring Post).\n"
                f"Posted by: {author_name}.\n"
                f"Source listing: {original_url}\n\n"
                "This role was directly ingested from your provided LinkedIn recruiter post URL. "
                "Tailored will match your active candidate personas and extract core requirements."
            ),
            source_metadata={"activity_id": sid, "ingestion_method": "url_slug_post_synthesis"}
        )

    def _fetch_linkedin_job_listing(self, url: str) -> Optional[RawJob]:
        """
        Extracts public LinkedIn job postings using LinkedIn guest API or public HTML.
        """
        job_id_match = re.search(r"/jobs/(?:view/)?([0-9]+)", url) or re.search(r"currentJobId=([0-9]+)", url)
        job_id = job_id_match.group(1) if job_id_match else None

        title = "LinkedIn Job Role"
        company = "LinkedIn Employer"
        location = "Global / Remote"
        description = ""

        # Try LinkedIn guest endpoint first (unauthenticated public API)
        if job_id:
            guest_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
            try:
                with httpx.Client(headers=self.headers, follow_redirects=True, timeout=self.timeout) as client:
                    resp = client.get(guest_url)
                    if resp.status_code == 200 and resp.text:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        title_elem = soup.find("h2", class_="top-card-layout__title") or soup.find("h1")
                        if title_elem:
                            title = title_elem.get_text(strip=True)

                        comp_elem = soup.find(class_="topcard__org-name-link") or soup.find(class_="topcard__flavor")
                        if comp_elem:
                            company = comp_elem.get_text(strip=True)

                        loc_elem = soup.find(class_="topcard__flavor--bullet")
                        if loc_elem:
                            location = loc_elem.get_text(strip=True)

                        desc_elem = soup.find(class_="show-more-less-html__markup") or soup.find("div", class_="description__text")
                        if desc_elem:
                            description = desc_elem.get_text(separator="\n", strip=True)

                        if description and len(description) > 40:
                            job = RawJob(
                                source_type="linkedin",
                                source_id=f"linkedin_ingested_{job_id}",
                                title=title,
                                company_name=company,
                                location=location,
                                url=url,
                                raw_description=description,
                                source_metadata={"job_id": job_id, "ingestion_method": "linkedin_guest_api"}
                            )
                            if self._is_valid_job_content(job):
                                return job
            except Exception as e:
                logger.debug("LinkedIn guest API fetch error: %s", e)

        # Fallback to direct page request with authwall check
        with httpx.Client(headers=self.headers, follow_redirects=True, timeout=self.timeout) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                og_title = soup.find("meta", property="og:title")
                if og_title and og_title.get("content"):
                    raw_t = og_title["content"].strip()
                    parts = raw_t.split(" at ")
                    if len(parts) >= 2:
                        title = parts[0].strip()
                        company = parts[1].split("|")[0].strip()
                    else:
                        title = raw_t.split("|")[0].strip()

                og_desc = soup.find("meta", property="og:description")
                if og_desc and og_desc.get("content"):
                    description = og_desc["content"].strip()

                sid = job_id or str(abs(hash(url)) % 10000000)
                job = RawJob(
                    source_type="linkedin",
                    source_id=f"linkedin_ingested_{sid}",
                    title=title,
                    company_name=company,
                    location=location,
                    url=url,
                    raw_description=description or f"Position: {title} at {company}. View full role: {url}",
                    source_metadata={"job_id": sid, "ingestion_method": "linkedin_og_meta"}
                )
                if self._is_valid_job_content(job):
                    return job

        return None

    def _fetch_wuzzuf(self, url: str) -> Optional[RawJob]:
        """
        Extracts public Wuzzuf job postings.
        """
        match = re.search(r"/jobs/p/([0-9a-zA-Z]+)", url)
        wuzzuf_id = match.group(1) if match else str(abs(hash(url)) % 10000000)

        with httpx.Client(headers=self.headers, follow_redirects=True, timeout=self.timeout) as client:
            resp = client.get(url)
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.text, "html.parser")

            # Extract Title
            title_elem = soup.find("h1") or soup.find("meta", property="og:title")
            if hasattr(title_elem, "get_text"):
                title = title_elem.get_text(strip=True)
            elif title_elem and title_elem.get("content"):
                title = title_elem["content"].split("Jobs in")[0].strip()
            else:
                title = "Wuzzuf Job Posting"

            # Extract Company
            company_elem = soup.find("a", href=re.compile(r"/jobs/careers/"))
            if company_elem:
                company = company_elem.get_text(strip=True).replace("-", " ")
            else:
                og_site = soup.find("meta", property="og:site_name")
                company = og_site["content"].strip() if og_site and og_site.get("content") else "Egyptian Employer"

            # Extract Location
            location = "Cairo, Egypt"
            for span in soup.find_all("span"):
                span_text = span.get_text(strip=True)
                if any(k in span_text.lower() for k in ["egypt", "cairo", "giza", "alexandria", "saudi", "riyadh"]):
                    location = span_text
                    break

            # Extract Description & Requirements
            sections = []
            for sec in soup.find_all(["section", "div"]):
                txt = sec.get_text(separator="\n", strip=True)
                txt_lower = txt[:90].lower()
                if any(hdr in txt_lower for hdr in [
                    "job description", "job requirements", "about the job",
                    "what we expect", "responsibilities", "skills", "experience needed"
                ]):
                    sections.append(txt)

            if sections:
                description = "\n\n".join(sections)[:9000]
            else:
                main_elem = soup.find("main") or soup.find("article")
                description = main_elem.get_text(separator="\n", strip=True)[:9000] if main_elem else ""

            return RawJob(
                source_type="wuzzuf",
                source_id=f"wuzzuf_ingested_{wuzzuf_id}",
                title=title,
                company_name=company,
                location=location,
                url=url,
                raw_description=description or f"Position: {title} at {company}. Location: {location}.",
                source_metadata={"wuzzuf_id": wuzzuf_id, "ingestion_method": "wuzzuf_direct_page"}
            )

    def _fetch_generic(self, url: str) -> Optional[RawJob]:
        """
        Generic HTML parser for career sites (Greenhouse, Lever, Workday, etc.).
        """
        with httpx.Client(headers=self.headers, follow_redirects=True, timeout=self.timeout) as client:
            resp = client.get(url)
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.text, "html.parser")

            # Title
            og_title = soup.find("meta", property="og:title")
            h1 = soup.find("h1")
            if og_title and og_title.get("content"):
                title = og_title["content"].strip()
            elif h1:
                title = h1.get_text(strip=True)
            elif soup.title:
                title = soup.title.string.strip()
            else:
                title = "Job Opportunity"

            # Company
            domain = urlparse(url).netloc.replace("www.", "")
            og_site = soup.find("meta", property="og:site_name")
            if og_site and og_site.get("content"):
                company = og_site["content"].strip()
            else:
                domain_parts = domain.split(".")
                company = domain_parts[0].capitalize() if domain_parts else "Hiring Company"

            # Location
            location = "Worldwide (Remote / Hybrid)"
            loc_elem = soup.find(class_=re.compile(r"location|workplace|city", re.I))
            if loc_elem:
                location = loc_elem.get_text(strip=True)

            # Description
            main = soup.find("main") or soup.find("article") or soup.find("div", id=re.compile(r"job|content|desc", re.I))
            if main:
                description = main.get_text(separator="\n", strip=True)[:10000]
            else:
                og_desc = soup.find("meta", property="og:description")
                description = og_desc["content"].strip() if og_desc and og_desc.get("content") else ""

            uid = str(abs(hash(url)) % 10000000)
            return RawJob(
                source_type="web",
                source_id=f"web_ingested_{uid}",
                title=title,
                company_name=company,
                location=location,
                url=url,
                raw_description=description or f"Role: {title} at {company}. Apply at: {url}",
                source_metadata={"domain": domain, "ingestion_method": "generic_web_fetch"}
            )

    def _fallback_from_url(self, url: str) -> RawJob:
        """
        Synthesizes a clean candidate job record from the URL slug when network is blocked or offline.
        """
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        parts = [p for p in path.split("/") if p and not p.isdigit()]

        slug = parts[-1] if parts else "opportunity"
        words = re.sub(r"[-_]+", " ", slug).split()
        clean_words = [w.capitalize() for w in words if not w.isdigit()]
        title = " ".join(clean_words) if clean_words else "Ingested Career Opportunity"

        domain = parsed.netloc.replace("www.", "")
        company = domain.split(".")[0].capitalize() if domain else "Company"

        is_post = self._is_linkedin_post(url)
        is_linkedin = "linkedin" in url.lower() or "lnkd.in" in url.lower()
        is_wuzzuf = "wuzzuf" in url.lower()

        src_type = "linkedin_posts" if is_post else "linkedin" if is_linkedin else "wuzzuf" if is_wuzzuf else "web"
        uid = str(abs(hash(url)) % 10000000)
        return RawJob(
            source_type=src_type,
            source_id=f"{src_type}_ingested_{uid}",
            title=f"{title} (Recruiter Post)" if is_post and "post" not in title.lower() else title,
            company_name=f"{company} (LinkedIn Hiring Post)" if is_post else company,
            location="Remote / Hybrid",
            url=url,
            raw_description=(
                f"Position: {title} at {company}.\n"
                f"Source listing: {url}\n\n"
                "This role was directly ingested from your provided URL link. "
                "Tailored will match your active candidate personas and extract core requirements."
            ),
            source_metadata={"ingestion_method": "url_slug_synthesis"}
        )

url_job_fetcher = UrlJobFetcher()
