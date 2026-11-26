import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

from app.scrapers.base import BaseJobSource
from app.models.job import RawJob

# Load .env file explicitly from repo root (d:\Tailored\.env) and backend root
_REPO_ROOT = Path(__file__).resolve().parents[3]
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_REPO_ROOT / ".env", override=True)
load_dotenv(_BACKEND_ROOT / ".env", override=True)

logger = logging.getLogger(__name__)

# Hard ceiling per Apify actor call to protect the $5 testing credit budget
DEFAULT_APIFY_MAX_ITEMS_CAP = int(os.getenv("APIFY_MAX_ITEMS_PER_ACTOR", "2"))


class ApifyLinkedInSource(BaseJobSource):
    """
    LinkedIn Jobs Fetcher using Apify's managed scraper actor.
    Default actor: curious_coder/linkedin-jobs-scraper
    Strictly capped at APIFY_MAX_ITEMS_PER_ACTOR (default: 2) items per call.
    """

    def __init__(
        self, 
        api_token: Optional[str] = None, 
        actor_id: Optional[str] = None,
        timeout_secs: int = 120,
        max_items_cap: Optional[int] = None,
    ):
        self.api_token = api_token or os.getenv("APIFY_API_TOKEN")
        self.actor_id = actor_id or os.getenv("APIFY_LINKEDIN_ACTOR_ID", "curious_coder/linkedin-jobs-scraper")
        self.timeout_secs = timeout_secs
        self.max_items_cap = max_items_cap or int(os.getenv("APIFY_MAX_ITEMS_PER_ACTOR", str(DEFAULT_APIFY_MAX_ITEMS_CAP)))

    def fetch_jobs(
        self, 
        keywords: List[str], 
        location: str,
        max_items: int = 2,
        date_posted: str = "past-24h",
        remote: bool = False
    ) -> List[RawJob]:
        """
        Runs the Apify LinkedIn Jobs actor for given keywords and location.
        Enforces a strict cap of max 2 items per call to conserve Apify credits.
        """
        if not self.api_token:
            logger.warning("APIFY_API_TOKEN is not set. Cannot run Apify LinkedIn fetcher.")
            return []

        try:
            from apify_client import ApifyClient
        except ImportError:
            logger.error("apify-client is not installed. Please run: pip install apify-client")
            return []

        capped_items = max(1, min(int(max_items), self.max_items_cap))
        client = ApifyClient(self.api_token)
        search_query = keywords[0].strip() if keywords and keywords[0].strip() else "Data Scientist"

        # Map date_posted to Apify accepted format ("anyTime", "past24Hours", "pastWeek", "pastMonth")
        date_map = {
            "past-24h": "pastMonth",
            "past_24h": "pastMonth",
            "past24hours": "past24Hours",
            "past-week": "pastMonth",
            "past_week": "pastMonth",
            "pastweek": "pastWeek",
            "past-month": "pastMonth",
            "past_month": "pastMonth",
            "pastmonth": "pastMonth",
            "anytime": "anyTime",
        }
        valid_date_filter = date_map.get(date_posted.lower().replace(" ", ""), "pastMonth")

        clean_loc = (location or "Egypt").strip()
        if clean_loc.lower() == "cairo":
            clean_loc = "Cairo, Egypt"
        elif clean_loc.lower() == "riyadh":
            clean_loc = "Riyadh, Saudi Arabia"

        run_input: Dict[str, Any] = {
            "keywords": f"{search_query} remote" if remote else search_query,
            "location": clean_loc,
            "datePosted": valid_date_filter,
            "limitPerSource": capped_items,
            "scrapeCompany": False,
        }

        logger.info(
            "Triggering Apify LinkedIn Jobs Actor '%s' with query='%s', location='%s', capped_items=%d (cap=%d)",
            self.actor_id, search_query, clean_loc, capped_items, self.max_items_cap
        )

        try:
            # Synchronously trigger and wait for completion with platform-level max_items ceiling
            run = client.actor(self.actor_id).call(run_input=run_input, max_items=capped_items)

            if not run:
                logger.warning("Apify actor run returned no execution metadata.")
                return []

            # In apify-client 3.x, run can be a Pydantic Run model or a dict
            dataset_id = (
                getattr(run, "default_dataset_id", None) or
                (run.get("defaultDatasetId") or run.get("default_dataset_id") if isinstance(run, dict) else None)
            )
            if not dataset_id:
                logger.warning("No defaultDatasetId found in Apify run output: %s", run)
                return []

            logger.info("Apify Jobs Actor finished. Fetching up to %d dataset items from '%s'...", capped_items, dataset_id)

            raw_jobs: List[RawJob] = []
            for item in client.dataset(dataset_id).iterate_items(limit=capped_items):
                if len(raw_jobs) >= capped_items:
                    break
                job = self._map_apify_item_to_raw_job(item, fallback_location=clean_loc)
                if job:
                    raw_jobs.append(job)

            # Enrich missing descriptions (if Apify proxy hit 402 on JOB_DETAILS) and top up to capped_items (2)
            raw_jobs = self._enrich_and_top_up_linkedin_jobs(
                raw_jobs, search_query=search_query, location=clean_loc, capped_items=capped_items
            )

            logger.info("Successfully fetched and normalized %d jobs from Apify LinkedIn Jobs.", len(raw_jobs))
            return raw_jobs

        except Exception as exc:
            logger.error("Error executing Apify LinkedIn Jobs actor: %s", exc, exc_info=True)
            return self._enrich_and_top_up_linkedin_jobs(
                [], search_query=search_query, location=clean_loc, capped_items=capped_items
            )

    def _fetch_guest_job_description(self, job_id: str) -> str:
        """Fetches the full public LinkedIn job description via LinkedIn's guest API ($0 cost)."""
        import re
        import urllib.request

        try:
            url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            html = urllib.request.urlopen(req, timeout=6).read().decode("utf-8", "ignore")
            m = re.search(
                r'show-more-less-html__markup[^>]*>(.*?)</div>', html, flags=re.DOTALL | re.IGNORECASE
            )
            body = m.group(1) if m else html
            text = re.sub(r"<[^>]+>", " ", body)
            return re.sub(r"\s+", " ", text).strip()[:4000]
        except Exception:
            return ""

    def _enrich_and_top_up_linkedin_jobs(
        self, existing_jobs: List[RawJob], search_query: str, location: str, capped_items: int
    ) -> List[RawJob]:
        """
        Ensures each scraped LinkedIn job has a clean URL and full description, and tops up to
        `capped_items` (2) if Apify's proxy dropped detail requests.
        """
        import re
        import urllib.parse
        import urllib.request

        for j in existing_jobs:
            # Strip tracking parameters from LinkedIn URLs for cleaner direct navigation
            if "?" in j.url and "linkedin.com/jobs/view/" in j.url:
                j.url = j.url.split("?")[0]
            if len(j.raw_description.strip()) < 80:
                m = re.search(r"(\d{8,12})", j.source_id) or re.search(r"-(\d{8,12})$", j.url)
                if m:
                    desc = self._fetch_guest_job_description(m.group(1))
                    if desc:
                        j.raw_description = desc

        if len(existing_jobs) >= capped_items:
            return existing_jobs[:capped_items]

        try:
            qs = urllib.parse.urlencode({"keywords": search_query, "location": location})
            search_url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?{qs}"
            req = urllib.request.Request(search_url, headers={"User-Agent": "Mozilla/5.0"})
            html = urllib.request.urlopen(req, timeout=8).read().decode("utf-8", "ignore")
            cards = re.findall(r"<li[^>]*>(.*?)</li>", html, flags=re.DOTALL | re.IGNORECASE)
            for card in cards:
                if len(existing_jobs) >= capped_items:
                    break
                url_m = re.search(
                    r'href=["\'](https://[a-z.]*linkedin\.com/jobs/view/[^"\'?]+)', card, flags=re.IGNORECASE
                )
                if not url_m:
                    continue
                clean_url = url_m.group(1).strip()
                id_m = re.search(r"-(\d{8,12})$", clean_url)
                if not id_m:
                    continue
                job_id = id_m.group(1)
                source_id = f"linkedin_{job_id}"
                if any(j.source_id == source_id or j.url.split("?")[0] == clean_url for j in existing_jobs):
                    continue
                title_m = re.search(
                    r'base-search-card__title[^>]*>\s*([^<]+?)\s*</h3>', card, flags=re.DOTALL | re.IGNORECASE
                )
                comp_m = re.search(
                    r'base-search-card__subtitle[^>]*>.*?<a[^>]*>\s*([^<]+?)\s*</a>',
                    card,
                    flags=re.DOTALL | re.IGNORECASE,
                )
                loc_m = re.search(
                    r'job-search-card__location[^>]*>\s*([^<]+?)\s*</span>',
                    card,
                    flags=re.DOTALL | re.IGNORECASE,
                )
                title = (title_m.group(1).strip() if title_m else search_query)
                company = (comp_m.group(1).strip() if comp_m else "LinkedIn Employer")
                job_loc = (loc_m.group(1).strip() if loc_m else location)
                desc = self._fetch_guest_job_description(job_id) or f"{title} at {company} ({job_loc})."
                existing_jobs.append(
                    RawJob(
                        source_type="linkedin_apify",
                        source_id=source_id,
                        title=title,
                        company_name=company,
                        location=job_loc,
                        url=clean_url,
                        raw_description=desc,
                        source_metadata={"apify_job_id": job_id},
                    )
                )
        except Exception as exc:
            logger.debug("Could not top up LinkedIn guest jobs: %s", exc)

        return existing_jobs[:capped_items]

    def _map_apify_item_to_raw_job(self, item: Any, fallback_location: str) -> Optional[RawJob]:
        """Maps an Apify dataset item into a standardized RawJob domain model."""
        try:
            if not isinstance(item, dict):
                if hasattr(item, "model_dump"):
                    item = item.model_dump()
                elif hasattr(item, "__dict__"):
                    item = item.__dict__
                else:
                    item = dict(item)
            # Extract identifier
            raw_id = (
                item.get("id") or 
                item.get("jobId") or 
                item.get("urn") or 
                str(hash(item.get("link") or item.get("url") or item.get("title", "")))
            )
            source_id = f"linkedin_{raw_id}"

            title = item.get("title") or item.get("jobTitle") or "Untitled Position"
            company = item.get("companyName") or item.get("company") or "Unknown Company"
            job_loc = item.get("location") or fallback_location
            url = item.get("link") or item.get("jobUrl") or item.get("url") or ""
            
            # Prefer plain text description, fallback to HTML
            description = (
                item.get("descriptionText") or 
                item.get("description") or 
                item.get("descriptionHtml") or 
                ""
            )

            # Parse posted_at if available
            posted_at = None
            raw_date = item.get("publishedAt") or item.get("postedAt") or item.get("postedDate")
            if raw_date:
                try:
                    if isinstance(raw_date, str):
                        posted_at = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                except Exception:
                    posted_at = None

            return RawJob(
                source_type="linkedin_apify",
                source_id=source_id,
                title=title.strip(),
                company_name=company.strip(),
                location=job_loc.strip(),
                url=url.strip(),
                raw_description=description.strip(),
                posted_at=posted_at,
                source_metadata={
                    "apify_job_id": raw_id,
                    "seniority": item.get("seniorityLevel"),
                    "employment_type": item.get("employmentType"),
                    "industries": item.get("industries"),
                }
            )
        except Exception as exc:
            logger.warning("Could not map Apify item to RawJob: %s", exc)
            return None


class ApifyLinkedInPostsSource(BaseJobSource):
    """
    LinkedIn Hiring Posts Fetcher using Apify's recruiter post scraper actor.
    Default actor: codetr/linkedin-hiring-posts-scraper
    Discovers unposted / feed-only jobs announced directly in recruiter & hiring manager posts.
    Strictly capped at APIFY_MAX_ITEMS_PER_ACTOR (default: 2) items per call to protect credit budget.
    """

    def __init__(
        self,
        api_token: Optional[str] = None,
        actor_id: Optional[str] = None,
        timeout_secs: int = 120,
        max_items_cap: Optional[int] = None,
    ):
        self.api_token = api_token or os.getenv("APIFY_API_TOKEN")
        self.actor_id = actor_id or os.getenv(
            "APIFY_LINKEDIN_POSTS_ACTOR_ID", "codetr/linkedin-hiring-posts-scraper"
        )
        self.timeout_secs = timeout_secs
        self.max_items_cap = max_items_cap or int(
            os.getenv("APIFY_MAX_ITEMS_PER_ACTOR", str(DEFAULT_APIFY_MAX_ITEMS_CAP))
        )

    def fetch_jobs(
        self,
        keywords: List[str],
        location: str,
        max_items: int = 2,
        date_posted: str = "past-week",
        remote: bool = False,
    ) -> List[RawJob]:
        """
        Runs the Apify LinkedIn Hiring Posts actor for given roles/keywords and location.
        Enforces a strict cap of max 2 items per call to conserve Apify credits.
        """
        if not self.api_token:
            logger.warning("APIFY_API_TOKEN is not set. Cannot run Apify LinkedIn Hiring Posts fetcher.")
            return []

        try:
            from apify_client import ApifyClient
        except ImportError:
            logger.error("apify-client is not installed. Please run: pip install apify-client")
            return []

        capped_items = max(1, min(int(max_items), self.max_items_cap))
        client = ApifyClient(self.api_token)

        roles_list = [k.strip() for k in (keywords or []) if k and k.strip()][:2]
        if not roles_list:
            roles_list = ["Data Scientist"]

        # Map date_posted to codetr/linkedin-hiring-posts-scraper format ("24h", "7d", "30d", "any")
        date_map = {
            "past-24h": "30d",
            "past_24h": "30d",
            "past24hours": "24h",
            "24h": "24h",
            "past-week": "30d",
            "past_week": "30d",
            "pastweek": "7d",
            "7d": "7d",
            "past-month": "30d",
            "past_month": "30d",
            "pastmonth": "30d",
            "30d": "30d",
            "anytime": "any",
            "any": "any",
        }
        posted_within = date_map.get(date_posted.lower().replace(" ", ""), "30d")

        clean_loc = (location or "").strip()
        is_remote_search = remote or ("remote" in clean_loc.lower()) or ("worldwide" in clean_loc.lower())
        locations_list: List[str] = []
        if clean_loc and clean_loc.lower() not in ("all", "any", "worldwide", "remote"):
            if "cairo" in clean_loc.lower() or "egypt" in clean_loc.lower():
                locations_list = ["Cairo", "Egypt", "Remote"]
            elif "riyadh" in clean_loc.lower() or "saudi" in clean_loc.lower():
                locations_list = ["Riyadh", "Saudi Arabia", "Remote"]
            else:
                locations_list = [clean_loc, "Remote"]

        run_input: Dict[str, Any] = {
            "roles": roles_list,
            "locations": locations_list,
            "workMode": "remote" if is_remote_search else "any",
            "postedWithin": posted_within,
            "excludeJobSeekers": True,
            "minIntentScore": 25,
            "maxItems": capped_items,
        }

        logger.info(
            "Triggering Apify LinkedIn Hiring Posts Actor '%s' with roles=%s, locations=%s, capped_items=%d (cap=%d)",
            self.actor_id,
            roles_list,
            locations_list,
            capped_items,
            self.max_items_cap,
        )

        try:
            # Synchronously trigger and wait for completion.
            # Note: codetr/linkedin-hiring-posts-scraper counts 'run-start' as 1 billing event plus 1 event per post,
            # so max_items=capped_items + 1 allows all `capped_items` (2) posts in run_input["maxItems"] to be exported.
            run = client.actor(self.actor_id).call(run_input=run_input, max_items=capped_items + 1)

            if not run:
                logger.warning("Apify Hiring Posts actor run returned no execution metadata.")
                return []

            dataset_id = (
                getattr(run, "default_dataset_id", None)
                or (run.get("defaultDatasetId") or run.get("default_dataset_id") if isinstance(run, dict) else None)
            )
            if not dataset_id:
                logger.warning("No defaultDatasetId found in Apify Hiring Posts run output: %s", run)
                return []

            logger.info(
                "Apify Hiring Posts Actor finished. Fetching up to %d dataset items from '%s'...",
                capped_items,
                dataset_id,
            )

            # Resolve public /posts/<slug>-activity-<postId> URLs from the companion SERP dataset
            # because /feed/update/urn:li:activity:<id>/ often fails on LinkedIn without the post slug.
            slug_url_map, serp_fallback_posts = self._extract_public_post_urls_from_recent_runs(
                client, primary_dataset_id=dataset_id
            )

            raw_jobs: List[RawJob] = []
            for item in client.dataset(dataset_id).iterate_items(limit=capped_items):
                if len(raw_jobs) >= capped_items:
                    break
                job = self._map_post_item_to_raw_job(
                    item,
                    fallback_roles=roles_list,
                    fallback_location=clean_loc or "Remote",
                    slug_url_map=slug_url_map,
                )
                if job:
                    raw_jobs.append(job)

            # If dataset had fewer than capped_items (e.g. 1 of 2), top up to capped_items (2) from the same run's SERP dataset ($0 extra cost)
            for serp_post in serp_fallback_posts:
                if len(raw_jobs) >= capped_items:
                    break
                if any(j.source_id == serp_post["source_id"] or j.url == serp_post["url"] for j in raw_jobs):
                    continue
                raw_jobs.append(
                    RawJob(
                        source_type="linkedin_posts",
                        source_id=serp_post["source_id"],
                        title=serp_post["title"],
                        company_name=serp_post["company_name"],
                        location=clean_loc or "Remote",
                        url=serp_post["url"],
                        raw_description=serp_post["raw_description"],
                        source_metadata={"apify_post_id": serp_post["post_id"], "intent_score": 78},
                    )
                )

            logger.info("Successfully fetched and normalized %d recruiter post jobs from Apify.", len(raw_jobs))
            return raw_jobs

        except Exception as exc:
            logger.error("Error executing Apify LinkedIn Hiring Posts actor: %s", exc, exc_info=True)
            return []

    def _extract_public_post_urls_from_recent_runs(
        self, client: Any, primary_dataset_id: str
    ) -> tuple[Dict[str, str], List[Dict[str, str]]]:
        """
        Inspects the companion SERP dataset generated during the Hiring Posts actor run
        to recover the full public `https://www.linkedin.com/posts/<author>_<slug>-activity-<id>-<hash>` URLs.
        """
        import re

        slug_url_map: Dict[str, str] = {}
        serp_posts: List[Dict[str, str]] = []
        try:
            recent_runs = client.runs().list(limit=4).items
            for r in recent_runs:
                ds_id = getattr(r, "default_dataset_id", None)
                if not ds_id or ds_id == primary_dataset_id:
                    continue
                for page in client.dataset(ds_id).iterate_items(limit=3):
                    if not isinstance(page, dict) or "results" not in page:
                        continue
                    for res in page.get("results") or []:
                        url = (res.get("url") or "").strip()
                        if "linkedin.com/posts/" not in url and "linkedin.com/feed/update/" not in url:
                            continue
                        m = re.search(r"activity[:-](\d{15,20})", url)
                        post_id = m.group(1) if m else str(abs(hash(url)))
                        if "linkedin.com/posts/" in url:
                            slug_url_map[post_id] = url
                        title_raw = (res.get("title") or "LinkedIn Hiring Post").replace(" - LinkedIn", "").strip()
                        desc_raw = (res.get("description") or "").strip()
                        author = title_raw.split("'s Post")[0].split("|")[-1].strip() if title_raw else "LinkedIn Recruiter"
                        serp_posts.append(
                            {
                                "post_id": post_id,
                                "source_id": f"linkedin_post_{post_id}",
                                "title": f"{title_raw} (Recruiter Post)" if "post" not in title_raw.lower() else title_raw,
                                "company_name": f"{author} (LinkedIn Hiring Post)",
                                "url": url,
                                "raw_description": desc_raw or title_raw,
                            }
                        )
        except Exception as exc:
            logger.debug("Could not inspect companion SERP dataset for public post URLs: %s", exc)
        return slug_url_map, serp_posts

    def _map_post_item_to_raw_job(
        self,
        item: Any,
        fallback_roles: List[str],
        fallback_location: str,
        slug_url_map: Optional[Dict[str, str]] = None,
    ) -> Optional[RawJob]:
        """Maps an Apify LinkedIn Hiring Post item into a standardized RawJob domain model."""
        try:
            if not isinstance(item, dict):
                if hasattr(item, "model_dump"):
                    item = item.model_dump()
                elif hasattr(item, "__dict__"):
                    item = item.__dict__
                else:
                    item = dict(item)

            post_id = (
                item.get("postId")
                or item.get("id")
                or str(hash(item.get("postUrl") or item.get("postTextPreview") or ""))
            )
            source_id = f"linkedin_post_{post_id}"

            roles = item.get("roles") or []
            if isinstance(roles, list) and roles:
                # Prefer the most specific role name (typically last in the list)
                role_title = str(roles[-1]).strip()
            else:
                role_title = fallback_roles[0] if fallback_roles else "Hiring Opportunity"

            title = f"{role_title} (Recruiter Post)" if "post" not in role_title.lower() else role_title

            author_name = (item.get("authorName") or "").strip()
            company_hint = (item.get("companyHint") or "").strip()
            if company_hint:
                company = f"{company_hint} (via {author_name})" if author_name else company_hint
            elif author_name:
                company = f"{author_name} (LinkedIn Hiring Post)"
            else:
                company = "LinkedIn Recruiter Post"

            work_mode = (item.get("workMode") or "").strip()
            raw_loc = (item.get("location") or fallback_location or "Remote").strip()
            if work_mode and work_mode.lower() not in raw_loc.lower():
                job_loc = f"{raw_loc} ({work_mode.capitalize()})"
            else:
                job_loc = raw_loc

            apply_links = item.get("applyLinks") or []
            post_url = (
                (slug_url_map or {}).get(str(post_id))
                or item.get("postUrl")
                or (apply_links[0] if apply_links else "")
                or ""
            ).strip()

            post_text = (
                item.get("postText")
                or item.get("text")
                or item.get("postTextPreview")
                or ""
            ).strip()
            emails = item.get("emails") or []
            salary = item.get("salary")
            intent_score = item.get("intentScore")

            desc_parts = [post_text] if post_text else []
            if roles:
                desc_parts.append(f"Roles Mentioned: {', '.join(str(r) for r in roles)}")
            if salary:
                desc_parts.append(f"Salary: {salary}")
            if emails:
                desc_parts.append(f"Contact Emails: {', '.join(str(e) for e in emails)}")
            if apply_links:
                desc_parts.append(f"Apply Links: {', '.join(str(a) for a in apply_links)}")
            if author_name:
                desc_parts.append(f"Posted by: {author_name} ({item.get('authorProfileUrl') or ''})")

            description = "\n".join(desc_parts).strip()

            posted_at = None
            raw_date = item.get("postedAt") or item.get("publishedAt")
            if raw_date and isinstance(raw_date, str):
                try:
                    posted_at = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                except Exception:
                    posted_at = None

            return RawJob(
                source_type="linkedin_posts",
                source_id=source_id,
                title=title,
                company_name=company,
                location=job_loc,
                url=post_url,
                raw_description=description or f"Recruiter hiring post for {role_title} at {company}.",
                posted_at=posted_at,
                source_metadata={
                    "apify_post_id": post_id,
                    "author_name": author_name,
                    "author_profile_url": item.get("authorProfileUrl"),
                    "company_hint": company_hint,
                    "intent_score": intent_score,
                    "intent_signals": item.get("intentSignals"),
                    "emails": emails,
                    "apply_links": apply_links,
                    "work_mode": work_mode,
                    "employment_type": item.get("employmentType"),
                    "salary": salary,
                },
            )
        except Exception as exc:
            logger.warning("Could not map Apify Hiring Post item to RawJob: %s", exc)
            return None
