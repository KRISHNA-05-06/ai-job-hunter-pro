"""
scorer.py - AI job fit scoring via Groq (Llama 3)
Scores each job 1-10 and tiers into T1/T2/T3/SKIP
"""

import os
import json
import logging
from groq import Groq

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.environ["GROQ_API_KEY"]

CANDIDATE_PROFILE = """
Name: Sri Krishna Sai Kota
Targets: Data Engineer, AI Engineer, ML Engineer, Analytics Engineer
Experience: ~2 years internship (Data Engineering)
Education: M.S. Computer Science, University of South Florida (Tampa, FL)
Work auth: F-1 OPT — ~3 years, zero employer action needed
Location: Tampa FL, open to full US relocation, remote preferred

Core stack:
  Python, SQL, PySpark, Apache Spark 4.0, Delta Lake
  Apache Kafka (streaming), Apache Airflow (orchestration)
  Snowflake, ClickHouse (warehouses), dbt (transforms)
  AWS (S3, Lambda, Glue, EC2), basic GCP
  Docker (13-service compose), FastAPI
  Groq/Llama, OpenAI (LLM integration)
  Isolation Forest (anomaly detection), Chart.js

Key projects:
  - Real-Time AI Event Intelligence Pipeline
    (Kafka + ClickHouse + Airflow + dbt + PySpark + FastAPI + Chart.js, 13 Docker services)
  - PySpark ETL Pipeline Optimization (61% runtime reduction)
  - Grocery ETL Pipeline (PySpark + Spark 4.0)
  - Containerized ETL Pipeline (Docker + PostgreSQL)
  - AI Job Hunter (Groq/Llama, GitHub Actions, Apify)
"""

HARD_SKIP_PHRASES = [
    "us citizens only",
    "us citizen only",
    "citizens only",
    "security clearance",
    "active clearance",
    "ts/sci",
    "secret clearance",
    "top secret",
]

SCORE_PROMPT = """You are a precise job fit evaluator. Score this job for the candidate below.

CANDIDATE:
{profile}

JOB:
Title: {title}
Company: {company}
Location: {location}
Source: {source}
Description: {description}

SCORING:
- 0 = hard skip (citizens only / clearance / 6+ yrs required / wrong domain like defense/Epic/SAP)
- 1-4 = poor fit (Tier 3, skip)
- 5-7 = decent fit (Tier 2, base resume apply)
- 8-10 = strong fit (Tier 1, tailored apply)

Consider:
+ Stack match: Python/PySpark/Kafka/Airflow/Snowflake/dbt/AWS/Docker/ClickHouse
+ Experience level: entry/junior/mid = good; senior 5+ yrs = likely mismatch
+ Domain: data engineering, AI/ML, cloud, analytics = good; defense/SAP/Epic = skip
+ Location: remote/hybrid/anywhere US = bonus
- Penalize if requires 4+ years of specific tool experience candidate lacks

Respond ONLY in valid JSON, no markdown, no extra text:
{{"score":<int 0-10>,"tier":"T1"|"T2"|"T3"|"SKIP","reason":"<one sentence>","top_matching_skills":["skill1","skill2"],"missing_skills":["skill1"]}}"""


def score_job(job: dict) -> dict:
    """Score a single job. Returns the job dict with scoring fields added."""
    client = Groq(api_key=GROQ_API_KEY)

    # Fast pre-filter for hard skip phrases
    combined = (job.get("title", "") + " " + job.get("description", "")).lower()
    for phrase in HARD_SKIP_PHRASES:
        if phrase in combined:
            job.update({
                "score": 0, "tier": "SKIP",
                "reason": f"Auto-skip: '{phrase}' found in listing",
                "top_matching_skills": [], "missing_skills": [],
            })
            return job

    prompt = SCORE_PROMPT.format(
        profile=CANDIDATE_PROFILE,
        title=job.get("title", ""),
        company=job.get("company", ""),
        location=job.get("location", ""),
        source=job.get("source", ""),
        description=job.get("description", "")[:1500],
    )

    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=300,
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown fences if present
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
        job.update(result)
    except Exception as e:
        logger.warning(f"Scoring failed for '{job.get('title')}' @ '{job.get('company')}': {e}")
        job.update({
            "score": 5, "tier": "T2",
            "reason": "Scoring error — defaulted to T2",
            "top_matching_skills": [], "missing_skills": [],
        })

    return job


def score_all_jobs(jobs: list[dict]) -> dict:
    """Score all jobs and bucket into tiers."""
    tiers: dict[str, list] = {"T1": [], "T2": [], "T3": [], "SKIP": []}

    for i, job in enumerate(jobs):
        logger.info(
            f"Scoring [{i+1}/{len(jobs)}] {job.get('source','?')} | "
            f"{job.get('title','?')} @ {job.get('company','?')}"
        )
        scored = score_job(job)
        tier = scored.get("tier", "T3")
        tiers.setdefault(tier, []).append(scored)

    logger.info(
        f"Scoring done — T1:{len(tiers['T1'])} "
        f"T2:{len(tiers['T2'])} "
        f"T3:{len(tiers['T3'])} "
        f"SKIP:{len(tiers['SKIP'])}"
    )
    return tiers
