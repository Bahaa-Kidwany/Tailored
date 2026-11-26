import re
import logging
from typing import Any, Dict, List
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

class CompanyCrawler:
    """Crawls company websites for about/careers pages to provide context for document tailoring."""

    @staticmethod
    def clean_html(html: str) -> str:
        text = re.sub(r"(?is)<script.*?>.*?</script>", " ", html)
        text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
        text = re.sub(r"(?s)<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def extract_links(html: str, base_url: str) -> List[str]:
        matches = re.findall(r'href=["\']([^"\']+)["\']', html, re.IGNORECASE)
        links: List[str] = []
        for href in matches:
            if href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
                continue
            links.append(urljoin(base_url, href))
        return links

    def crawl_company_context(self, website_url: str | None) -> Dict[str, Any]:
        if not website_url:
            return {"pages": [], "summary_text": ""}
            
        try:
            import urllib.request
            req = urllib.request.Request(
                website_url, 
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(req, timeout=8) as response:
                html = response.read().decode("utf-8", errors="ignore")
                final_url = response.geturl()
        except Exception as exc:
            logger.warning("Could not crawl company URL %s: %s", website_url, exc)
            return {"pages": [], "summary_text": "", "error": str(exc)}

        pages: List[Dict[str, str]] = []
        root_host = urlparse(final_url).netloc.lower()
        candidates = self.extract_links(html, final_url)
        preferred_terms = ("about", "company", "mission", "team", "careers", "product")
        selected_urls: List[str] = [final_url]
        
        for url in candidates:
            lowered = url.lower()
            if any(term in lowered for term in preferred_terms) and urlparse(url).netloc.lower() == root_host:
                normalized = url.split("#", 1)[0]
                if normalized not in selected_urls:
                    selected_urls.append(normalized)
            if len(selected_urls) >= 4:
                break

        for url in selected_urls[:4]:
            try:
                if url == final_url:
                    page_html = html
                else:
                    sub_req = urllib.request.Request(
                        url, 
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                    )
                    with urllib.request.urlopen(sub_req, timeout=5) as sub_res:
                        page_html = sub_res.read().decode("utf-8", errors="ignore")
                text = self.clean_html(page_html)[:5000]
                if text:
                    pages.append({"url": url, "text_excerpt": text})
            except Exception:
                continue

        summary_text = "\n\n".join(f"URL: {page['url']}\n{page['text_excerpt']}" for page in pages)
        return {"pages": pages, "summary_text": summary_text[:12000]}

company_crawler = CompanyCrawler()
