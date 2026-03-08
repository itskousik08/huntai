"""
HuntAI Lead Scraping Engine
Uses Apify API to collect business leads from multiple sources.
"""

import httpx
import time
import json
from typing import List, Dict, Optional
from database.db import log_activity


class ApifyScraper:
    """Scrapes leads using Apify actors."""

    APIFY_BASE = "https://api.apify.com/v2"

    # Apify actor IDs for different sources
    ACTORS = {
        "google_maps":   "nwua9Gu5YkAT85Mxw",  # Google Maps Scraper
        "linkedin":      "2SyF0bVxmgGr8IVCZ",  # LinkedIn Company Scraper
        "website_scraper": "BYndoFGSMjLDcBnYB", # Website Contact Scraper
    }

    def __init__(self, api_key: str, config=None):
        self.api_key = api_key
        self.config = config
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def scrape_google_maps(self, query: str, location: str, max_results: int = 20) -> List[Dict]:
        """Scrape businesses from Google Maps."""
        search_query = f"{query} in {location}" if location else query
        
        run_input = {
            "searchStringsArray": [search_query],
            "maxCrawledPlacesPerSearch": max_results,
            "language": "en",
            "exportPlaceUrls": False,
            "includeHistogram": False,
            "includeOpeningHours": False,
            "includePeopleAlsoSearch": False,
        }

        results = self._run_actor("google_maps", run_input)
        return [self._normalize_google_maps(r) for r in results if r]

    def scrape_startup_directories(self, industry: str, location: str, max_results: int = 20) -> List[Dict]:
        """Scrape from startup/company directories using generic web scraper."""
        sources = [
            f"https://www.ycombinator.com/companies?industry={industry.lower()}",
            f"https://www.crunchbase.com/search/organizations/field/organizations/facet_ids/company",
        ]

        leads = []
        for url in sources[:1]:  # Limit API calls
            run_input = {
                "startUrls": [{"url": url}],
                "maxPagesPerCrawl": 3,
                "maxResultsPerCrawl": max_results,
            }
            results = self._run_actor("website_scraper", run_input)
            for r in results:
                lead = self._normalize_generic(r, source="startup_directory")
                if lead.get('company_name') or lead.get('email'):
                    leads.append(lead)

        return leads[:max_results]

    def _run_actor(self, actor_key: str, run_input: dict, timeout: int = 120) -> List[Dict]:
        """Run an Apify actor and wait for results."""
        actor_id = self.ACTORS.get(actor_key)
        if not actor_id:
            return []

        try:
            # Start the actor run
            start_url = f"{self.APIFY_BASE}/acts/{actor_id}/runs"
            resp = httpx.post(start_url, headers=self.headers, json=run_input, timeout=30)
            if resp.status_code not in (200, 201):
                log_activity("scraper_error", f"Apify actor {actor_key} start failed: {resp.status_code}")
                return []

            run_data = resp.json().get('data', {})
            run_id = run_data.get('id')
            if not run_id:
                return []

            log_activity("scraper_start", f"Apify actor {actor_key} started: run_id={run_id}")

            # Poll until finished
            poll_url = f"{self.APIFY_BASE}/actor-runs/{run_id}"
            deadline = time.time() + timeout
            while time.time() < deadline:
                time.sleep(5)
                status_resp = httpx.get(poll_url, headers=self.headers, timeout=10)
                status = status_resp.json().get('data', {}).get('status', '')
                if status in ('SUCCEEDED', 'FAILED', 'ABORTED', 'TIMED-OUT'):
                    break

            if status != 'SUCCEEDED':
                log_activity("scraper_error", f"Apify run {run_id} ended with status: {status}")
                return []

            # Fetch dataset
            dataset_id = status_resp.json().get('data', {}).get('defaultDatasetId')
            if not dataset_id:
                return []

            items_url = f"{self.APIFY_BASE}/datasets/{dataset_id}/items?format=json"
            items_resp = httpx.get(items_url, headers=self.headers, timeout=30)
            return items_resp.json() if isinstance(items_resp.json(), list) else []

        except Exception as e:
            log_activity("scraper_error", f"Apify scraper error: {str(e)}")
            return []

    def _normalize_google_maps(self, raw: dict) -> Dict:
        """Normalize Google Maps result to standard lead format."""
        return {
            "company_name":   raw.get("title") or raw.get("name", ""),
            "email":          self._extract_email(raw),
            "website":        raw.get("website", ""),
            "location":       self._format_location(raw),
            "industry":       raw.get("categoryName") or raw.get("categories", [""])[0] if raw.get("categories") else "",
            "employee_count": "",
            "description":    raw.get("description", ""),
            "year_founded":   "",
            "phone":          raw.get("phone", ""),
            "source":         "google_maps",
            "raw":            raw,
        }

    def _normalize_generic(self, raw: dict, source: str = "web") -> Dict:
        """Normalize generic web scraper result."""
        return {
            "company_name":   raw.get("name") or raw.get("company", ""),
            "email":          self._extract_email(raw),
            "website":        raw.get("url") or raw.get("website", ""),
            "location":       raw.get("location", ""),
            "industry":       raw.get("industry", ""),
            "employee_count": raw.get("employees") or raw.get("size", ""),
            "description":    raw.get("description", ""),
            "year_founded":   raw.get("founded", ""),
            "source":         source,
            "raw":            raw,
        }

    def _extract_email(self, raw: dict) -> str:
        """Extract email from various fields."""
        for key in ('email', 'emails', 'contactEmail', 'email1'):
            val = raw.get(key, '')
            if isinstance(val, list):
                return val[0] if val else ''
            if val and '@' in str(val):
                return str(val)
        return ''

    def _format_location(self, raw: dict) -> str:
        city = raw.get("city", "")
        state = raw.get("state", "")
        country = raw.get("country", "")
        parts = [p for p in [city, state, country] if p]
        return ", ".join(parts)


class MockScraper:
    """Mock scraper for testing without Apify credits."""

    def scrape_google_maps(self, query, location, max_results=10):
        import random
        industries = ["SaaS", "E-commerce", "FinTech", "HealthTech", "EdTech", "Retail"]
        leads = []
        for i in range(min(max_results, 5)):
            company = f"{query.title()} Solutions {i+1}"
            leads.append({
                "company_name": company,
                "email": f"contact@{company.lower().replace(' ', '')}.com",
                "website": f"https://{company.lower().replace(' ', '')}.com",
                "location": location,
                "industry": random.choice(industries),
                "employee_count": random.choice(["1-10", "11-50", "51-200"]),
                "description": f"{company} provides {query} services to businesses.",
                "year_founded": str(random.randint(2015, 2023)),
                "source": "mock",
            })
        return leads

    def scrape_startup_directories(self, industry, location, max_results=10):
        return self.scrape_google_maps(industry, location, max_results)


def get_scraper(api_key: str, config=None, mock: bool = False):
    """Factory function to get the appropriate scraper."""
    if mock or not api_key:
        return MockScraper()
    return ApifyScraper(api_key, config)
