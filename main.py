"""
main.py - Orchestrates scrape → score → notify pipeline
Run via GitHub Actions hourly or locally with python main.py
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from src.scraper import scrape_all_jobs
from src.scorer import score_all_jobs
from src.notifier import send_email

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("main")


def save_results(tiers: dict) -> None:
    Path("data").mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    path = Path(f"data/jobs_{ts}.json")
    path.write_text(json.dumps(tiers, indent=2, default=str))
    logger.info(f"Results saved → {path}")


def main() -> None:
    logger.info("=" * 60)
    logger.info("AI Job Hunter Pro — pipeline starting")
    logger.info("Sources: LinkedIn | Indeed | Dice | ZipRecruiter | Glassdoor")
    logger.info("=" * 60)

    # 1. Scrape
    logger.info("STEP 1: Scraping all platforms...")
    jobs = scrape_all_jobs()
    logger.info(f"Found {len(jobs)} unique fresh jobs")

    if not jobs:
        logger.info("No fresh jobs this hour. Exiting.")
        return

    # 2. Score
    logger.info("STEP 2: AI scoring with Groq/Llama...")
    tiers = score_all_jobs(jobs)

    # 3. Save
    save_results(tiers)

    # 4. Notify
    logger.info("STEP 3: Sending email digest...")
    send_email(tiers)

    logger.info("Pipeline complete.")
    logger.info(
        f"Summary → T1:{len(tiers.get('T1',[]))} "
        f"T2:{len(tiers.get('T2',[]))} "
        f"T3:{len(tiers.get('T3',[]))} "
        f"SKIP:{len(tiers.get('SKIP',[]))}"
    )


if __name__ == "__main__":
    main()
