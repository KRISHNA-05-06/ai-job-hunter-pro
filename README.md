# AI Job Hunter Pro

Hourly job alerts from **LinkedIn + Indeed + Dice + ZipRecruiter**, scored by AI, delivered to your inbox every hour from 6am–10pm EST.

Built with **Apify** (scraping) + **Groq/Llama** (AI scoring) + **Gmail SMTP** (digest emails) + **GitHub Actions** (fully automated CI/CD).

---

## Architecture

```
Every hour (GitHub Actions cron)
         │
         ▼
┌─────────────────────────────────────┐
│  Apify Actors (parallel scraping)   │
│  • LinkedIn  (curious_coder actor)  │
│  • Indeed    (valig actor)          │
│  • Dice      (shahidirfan actor)    │
│  • ZipRecruiter (crawlerbros actor) │
└──────────────┬──────────────────────┘
               │ filter: posted < 1hr ago
               ▼
┌─────────────────────────────────────┐
│  Groq / Llama 3 (AI Scoring)        │
│  Score 1-10 per job                 │
│  T1 (8-10) │ T2 (5-7) │ T3/SKIP    │
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│  Gmail HTML Digest                  │
│  • Source badges per platform       │
│  • Fit score + matching skills      │
│  • Direct apply links               │
└─────────────────────────────────────┘
```

---

## Quick Setup

### 1. Clone the repo

```bash
git clone https://github.com/KRISHNA-05-06/ai-job-hunter-pro.git
cd ai-job-hunter-pro
cp .env.example .env
# Fill in your API keys in .env
```

### 2. Get API keys

| Key | Where |
|-----|-------|
| `APIFY_API_TOKEN` | [console.apify.com](https://console.apify.com/account/integrations) → Integrations |
| `GROQ_API_KEY` | [console.groq.com/keys](https://console.groq.com/keys) |
| `GMAIL_APP_PASSWORD` | Google Account → Security → App passwords → generate 16-char password |

### 3. Add GitHub Secrets

Go to your repo: **Settings → Secrets and variables → Actions → New repository secret**

Add these 5 secrets exactly:

| Secret name | Value |
|---|---|
| `APIFY_API_TOKEN` | your Apify token |
| `GROQ_API_KEY` | your Groq key |
| `GMAIL_USER` | srikrishnasaikota1@gmail.com |
| `GMAIL_APP_PASSWORD` | 16-char Gmail app password |
| `NOTIFY_EMAIL` | srikrishnasaikota1@gmail.com |

### 4. Push and go

```bash
git add .
git commit -m "feat: initial deploy"
git push origin main
```

GitHub Actions starts running automatically every hour. To test immediately: **Actions tab → AI Job Hunter Pro — Hourly → Run workflow**.

---

## Local Testing

```bash
pip install -r requirements.txt

# Copy and fill in .env
cp .env.example .env

python main.py
```

---

## Customization

**Change search queries** — edit `SEARCH_QUERIES` in `src/scraper.py`

**Change freshness window** — edit `MAX_AGE_HOURS` in `src/scraper.py` (default: 1 hour)

**Change schedule** — edit cron entries in `.github/workflows/hourly.yml`

**Update your profile** — edit `CANDIDATE_PROFILE` in `src/scorer.py`

---

## Cost Estimate (Apify)

| Platform | Per result | ~100 results/run | 17 runs/day |
|---|---|---|---|
| LinkedIn | $0.001 | $0.10 | ~$1.70 |
| Indeed | $0.0001 | $0.01 | ~$0.17 |
| Dice | $0.001 | $0.10 | ~$1.70 |
| ZipRecruiter | $0.002 | $0.20 | ~$3.40 |
| **Total** | | | **~$7/day** |

Apify free tier = $5/month. Starter plan at $49/month covers this comfortably.

---

## Stack

- Scraping: [Apify](https://apify.com)
- AI Scoring: [Groq](https://groq.com) (Llama 3 8B)
- Email: Gmail SMTP
- Automation: GitHub Actions
- Language: Python 3.11
