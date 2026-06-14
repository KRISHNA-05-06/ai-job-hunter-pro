"""
scraper.py - Apify-powered scraper for LinkedIn, Indeed, Dice, ZipRecruiter, Glassdoor
Pulls only jobs posted within the last hour across all 5 platforms
"""

import os
import time
import logging
from datetime import datetime, timezone, timedelta
from apify_client import ApifyClient

logger = logging.getLogger(__name__)

APIFY_TOKEN = os.environ["APIFY_API_TOKEN"]

SEARCH_QUERIES = [
    "Data Engineer",
    "AI Engineer",
    "ML Engineer",
    "Analytics Engineer",
    "Data Pipeline Engineer",
]

LOCATIONS = ["United States", "Remote"]

MAX_AGE_HOURS = 1


def get_client() -> ApifyClient:
    return ApifyClient(APIFY_TOKEN)


def posted_within(posted_at_str: str, hours: int = MAX_AGE_HOURS) -> bool:
    """Return True if job was posted within the last N hours."""
    if not posted_at_str:
        return True
    try:
        now = datetime.now(timezone.utc)
        text = str(posted_at_str).lower().strip()

        if "just now" in text or "moment" in text:
            return True
        if "minute" in text:
            return True
        if "hour" in text:
            num = int("".join(filter(str.isdigit, text)) or "1")
            return num <= hours
        if "day" in text or "week" in text or "month" in text:
            return False

        # Try ISO parse
        dt = datetime.fromisoformat(text.replace("z", "+00:00"))
        return (now - dt) <= timedelta(hours=hours)
    except Exception:
        return True  # include if unparseable


def normalize(job: dict) -> dict:
    """Strip None values and ensure all keys present."""
    defaults = {
        "source": "", "title": "", "company": "", "location": "",
        "posted_at": "", "url": "", "description": "", "salary": "",
        "job_type": "", "query": "",
    }
    return {k: job.get(k) or defaults[k] for k in defaults}


# ─────────────────────────────────────────────
# LinkedIn
# ─────────────────────────────────────────────
def scrape_linkedin(client: ApifyClient, query: str, location: str) -> list[dict]:
    logger.info(f"[LinkedIn] '{query}' in '{location}'")
    try:
        run = client.actor("curious_coder/linkedin-jobs-scraper").call(
            run_input={
                "queries": [{"query": query, "location": location}],
                "resultsLimit": 50,
                "timeFilter": "past24Hours",
                "proxy": {"useApifyProxy": True},
            }
        )
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        fresh = []
        for i in items:
            if not posted_within(i.get("postedAt", "")):
                continue
            fresh.append(normalize({
                "source": "LinkedIn",
                "title": i.get("title", ""),
                "company": i.get("companyName", ""),
                "location": i.get("location", ""),
                "posted_at": i.get("postedAt", ""),
                "url": i.get("jobUrl") or i.get("url", ""),
                "description": (i.get("description") or "")[:2000],
                "salary": i.get("salary", ""),
                "job_type": i.get("jobType", ""),
                "query": query,
            }))
        logger.info(f"[LinkedIn] {len(items)} total → {len(fresh)} fresh")
        return fresh
    except Exception as e:
        logger.error(f"[LinkedIn] Failed: {e}")
        return []


# ─────────────────────────────────────────────
# Indeed
# ─────────────────────────────────────────────
def scrape_indeed(client: ApifyClient, query: str, location: str) -> list[dict]:
    logger.info(f"[Indeed] '{query}' in '{location}'")
    try:
        run = client.actor("valig/indeed-jobs-scraper").call(
            run_input={
                "keyword": query,
                "location": location,
                "maxItems": 50,
                "datePosted": "last24hours",
                "proxy": {"useApifyProxy": True},
            }
        )
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        fresh = []
        for i in items:
            posted = i.get("datePosted") or i.get("postedAt", "")
            if not posted_within(posted):
                continue
            fresh.append(normalize({
                "source": "Indeed",
                "title": i.get("positionName") or i.get("title", ""),
                "company": i.get("company", ""),
                "location": i.get("location", ""),
                "posted_at": posted,
                "url": i.get("url") or i.get("jobUrl", ""),
                "description": (i.get("description") or "")[:2000],
                "salary": i.get("salary", ""),
                "job_type": i.get("jobType", ""),
                "query": query,
            }))
        logger.info(f"[Indeed] {len(items)} total → {len(fresh)} fresh")
        return fresh
    except Exception as e:
        logger.error(f"[Indeed] Failed: {e}")
        return []


# ─────────────────────────────────────────────
# Dice
# ─────────────────────────────────────────────
def scrape_dice(client: ApifyClient, query: str) -> list[dict]:
    """Dice is US tech-focused, no location filter needed."""
    logger.info(f"[Dice] '{query}'")
    try:
        run = client.actor("shahidirfan/Dice-Job-Scraper").call(
            run_input={
                "keyword": query,
                "maxResults": 50,
                "datePosted": "ONE_DAY",   # last 24hrs, we filter further
            }
        )
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        fresh = []
        for i in items:
            posted = i.get("postedDate") or i.get("postedAt") or i.get("date", "")
            if not posted_within(posted):
                continue
            fresh.append(normalize({
                "source": "Dice",
                "title": i.get("title") or i.get("jobTitle", ""),
                "company": i.get("company") or i.get("companyName", ""),
                "location": i.get("location", ""),
                "posted_at": posted,
                "url": i.get("url") or i.get("jobUrl") or i.get("applyUrl", ""),
                "description": (i.get("description") or i.get("jobDescription") or "")[:2000],
                "salary": i.get("salary") or i.get("compensation", ""),
                "job_type": i.get("employmentType") or i.get("jobType", ""),
                "query": query,
            }))
        logger.info(f"[Dice] {len(items)} total → {len(fresh)} fresh")
        return fresh
    except Exception as e:
        logger.error(f"[Dice] Failed: {e}")
        return []


# ─────────────────────────────────────────────
# ZipRecruiter
# ─────────────────────────────────────────────
def scrape_ziprecruiter(client: ApifyClient, query: str, location: str) -> list[dict]:
    logger.info(f"[ZipRecruiter] '{query}' in '{location}'")
    try:
        run = client.actor("crawlerbros/ziprecruiter-scraper-pro").call(
            run_input={
                "search": query,
                "location": location,
                "maxItems": 50,
                "daysAgo": 1,   # last 24hrs, we filter further to 1hr
            }
        )
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        fresh = []
        for i in items:
            posted = i.get("postedAt") or i.get("datePosted") or i.get("posted_time", "")
            if not posted_within(posted):
                continue
            fresh.append(normalize({
                "source": "ZipRecruiter",
                "title": i.get("title") or i.get("jobTitle", ""),
                "company": i.get("company") or i.get("hiring_company", {}).get("name", ""),
                "location": i.get("location") or f"{i.get('city', '')}, {i.get('state', '')}".strip(", "),
                "posted_at": posted,
                "url": i.get("url") or i.get("job_url", ""),
                "description": (i.get("description") or i.get("jobDescription") or "")[:2000],
                "salary": i.get("salary") or i.get("salary_interval", ""),
                "job_type": i.get("jobType") or i.get("employment_type", ""),
                "query": query,
            }))
        logger.info(f"[ZipRecruiter] {len(items)} total → {len(fresh)} fresh")
        return fresh
    except Exception as e:
        logger.error(f"[ZipRecruiter] Failed: {e}")
        return []


# ─────────────────────────────────────────────
# Glassdoor
# ─────────────────────────────────────────────
def scrape_glassdoor(client: ApifyClient, query: str, location: str) -> list[dict]:
    logger.info(f"[Glassdoor] '{query}' in '{location}'")
    try:
        run = client.actor("valig/glassdoor-jobs-scraper").call(
            run_input={
                "keyword": query,
                "location": location,
                "maxItems": 50,
                "datePosted": "last24hours",
                "proxy": {"useApifyProxy": True},
            }
        )
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        fresh = []
        for i in items:
            posted = i.get("datePosted") or i.get("postedAt") or i.get("postingDate", "")
            if not posted_within(posted):
                continue
            fresh.append(normalize({
                "source": "Glassdoor",
                "title": i.get("jobTitle") or i.get("title", ""),
                "company": i.get("employer", {}).get("name", "") or i.get("company", ""),
                "location": i.get("location", ""),
                "posted_at": posted,
                "url": i.get("jobUrl") or i.get("url", ""),
                "description": (i.get("description") or i.get("jobDescription") or "")[:2000],
                "salary": i.get("salary") or i.get("payPeriod", ""),
                "job_type": i.get("jobType") or i.get("employmentType", ""),
                "query": query,
            }))
        logger.info(f"[Glassdoor] {len(items)} total → {len(fresh)} fresh")
        return fresh
    except Exception as e:
        logger.error(f"[Glassdoor] Failed: {e}")
        return []


# ─────────────────────────────────────────────
# Main orchestrator
# ─────────────────────────────────────────────
def scrape_all_jobs() -> list[dict]:
    """Run all 5 scrapers, deduplicate by URL, return fresh jobs."""
    client = get_client()
    all_jobs: list[dict] = []

    for query in SEARCH_QUERIES:
        for location in LOCATIONS:
            all_jobs.extend(scrape_linkedin(client, query, location))
            all_jobs.extend(scrape_indeed(client, query, location))
            all_jobs.extend(scrape_ziprecruiter(client, query, location))
            all_jobs.extend(scrape_glassdoor(client, query, location))
            time.sleep(1)

        # Dice is US-only, no location loop needed
        all_jobs.extend(scrape_dice(client, query))
        time.sleep(1)

    # Deduplicate by URL
    seen: set[str] = set()
    unique: list[dict] = []
    for job in all_jobs:
        key = job["url"].strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(job)

    logger.info(f"Total unique fresh jobs across all 5 platforms: {len(unique)}")
    return unique
