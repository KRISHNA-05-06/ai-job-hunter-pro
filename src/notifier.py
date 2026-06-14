"""
notifier.py - Sends beautiful HTML email digest with tiered job results
Includes source badges for LinkedIn, Indeed, Dice, ZipRecruiter
"""

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

logger = logging.getLogger(__name__)

GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", GMAIL_USER)

SOURCE_COLORS = {
    "LinkedIn":     ("#0C447C", "#E6F1FB"),
    "Indeed":       ("#085041", "#E1F5EE"),
    "Dice":         ("#3C3489", "#EEEDFE"),
    "ZipRecruiter": ("#712B13", "#FAECE7"),
    "Glassdoor":    ("#3B6D11", "#EAF3DE"),
}

TIER_META = {
    "T1": ("#0C447C", "#E6F1FB", "Tier 1 — Apply Now"),
    "T2": ("#3C3489", "#EEEDFE", "Tier 2 — Base Apply"),
}


def _source_badge(source: str) -> str:
    fg, bg = SOURCE_COLORS.get(source, ("#444", "#f0f0f0"))
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 8px;'
        f'border-radius:10px;font-size:11px;font-weight:700;">{source}</span>'
    )


def _tier_badge(tier: str) -> str:
    fg, bg, label = TIER_META.get(tier, ("#444", "#f0f0f0", tier))
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 10px;'
        f'border-radius:10px;font-size:12px;font-weight:700;">{label}</span>'
    )


def _job_card(job: dict) -> str:
    tier = job.get("tier", "T3")
    score = job.get("score", 0)
    source = job.get("source", "")
    matching = ", ".join(job.get("top_matching_skills") or []) or "—"
    missing = ", ".join(job.get("missing_skills") or []) or "none"
    salary = job.get("salary") or ""
    url = job.get("url") or "#"

    score_color = "#0C447C" if score >= 8 else "#3C3489" if score >= 5 else "#666"

    return f"""
<div style="border:1px solid #e0e0e0;border-radius:10px;padding:16px 18px;
            margin-bottom:12px;background:#ffffff;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;
              flex-wrap:wrap;gap:8px;">
    <div style="flex:1;min-width:0;">
      <a href="{url}" style="font-size:15px;font-weight:700;color:#0C447C;
                              text-decoration:none;line-height:1.3;">
        {job.get('title','')}
      </a>
      <div style="font-size:13px;color:#555;margin-top:3px;">
        {job.get('company','')}
        {f' &bull; {job.get("location","")}' if job.get('location') else ''}
      </div>
      {f'<div style="font-size:12px;color:#3B6D11;margin-top:2px;">{salary}</div>' if salary else ''}
    </div>
    <div style="text-align:right;flex-shrink:0;">
      <div style="font-size:24px;font-weight:800;color:{score_color};
                  line-height:1;">{score}<span style="font-size:13px;
                  color:#aaa;">/10</span></div>
      <div style="font-size:10px;color:#aaa;margin-top:1px;">fit score</div>
    </div>
  </div>

  <div style="margin-top:10px;display:flex;flex-wrap:wrap;gap:6px;
              align-items:center;">
    {_source_badge(source)}
    {_tier_badge(tier)}
    <span style="font-size:12px;color:#888;">
      Posted: {job.get('posted_at','recently')}
    </span>
  </div>

  <div style="margin-top:8px;font-size:12px;color:#555;line-height:1.5;">
    <strong>Reason:</strong> {job.get('reason','')}<br>
    <strong>Matching:</strong> {matching}<br>
    <strong>Missing:</strong> {missing}
  </div>

  <div style="margin-top:10px;">
    <a href="{url}"
       style="background:#0C447C;color:#fff;padding:7px 16px;border-radius:6px;
              text-decoration:none;font-size:13px;font-weight:600;">
      Apply &rarr;
    </a>
  </div>
</div>"""


def _platform_summary(tiers: dict) -> str:
    """Count jobs per source platform across T1+T2."""
    counts: dict[str, int] = {}
    for tier in ("T1", "T2"):
        for job in tiers.get(tier, []):
            src = job.get("source", "Other")
            counts[src] = counts.get(src, 0) + 1

    if not counts:
        return ""

    items = "".join(
        f'<span style="margin-right:16px;font-size:13px;">'
        f'{_source_badge(src)} <strong style="color:#333;">{n}</strong></span>'
        for src, n in sorted(counts.items())
    )
    return f'<div style="padding:10px 24px;background:#fafafa;flex-wrap:wrap;">{items}</div>'


def _build_html(tiers: dict, run_time: str) -> str:
    t1 = tiers.get("T1", [])
    t2 = tiers.get("T2", [])
    total = sum(len(tiers.get(t, [])) for t in ("T1", "T2", "T3", "SKIP"))

    t1_html = "".join(_job_card(j) for j in t1) or (
        '<p style="color:#aaa;font-style:italic;font-size:13px;">'
        'No Tier 1 matches this hour.</p>'
    )
    t2_html = "".join(_job_card(j) for j in t2) or (
        '<p style="color:#aaa;font-style:italic;font-size:13px;">'
        'No Tier 2 matches this hour.</p>'
    )

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
</head>
<body style="margin:0;padding:20px;background:#f2f2f2;
             font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
<div style="max-width:660px;margin:0 auto;border-radius:12px;
            overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.08);">

  <!-- Header -->
  <div style="background:#0C447C;padding:20px 24px;color:#fff;">
    <div style="font-size:22px;font-weight:800;letter-spacing:-.3px;">
      AI Job Hunter Pro
    </div>
    <div style="font-size:13px;opacity:.8;margin-top:3px;">
      Hourly digest &bull; {run_time} &bull; LinkedIn + Indeed + Dice + ZipRecruiter + Glassdoor
    </div>
  </div>

  <!-- Stats bar -->
  <div style="background:#E6F1FB;padding:14px 24px;display:flex;gap:28px;flex-wrap:wrap;">
    <div>
      <span style="font-size:28px;font-weight:800;color:#0C447C;">{len(t1)}</span>
      <span style="font-size:12px;color:#185FA5;margin-left:4px;">Tier 1</span>
    </div>
    <div>
      <span style="font-size:28px;font-weight:800;color:#3C3489;">{len(t2)}</span>
      <span style="font-size:12px;color:#534AB7;margin-left:4px;">Tier 2</span>
    </div>
    <div>
      <span style="font-size:28px;font-weight:800;color:#888;">{total}</span>
      <span style="font-size:12px;color:#aaa;margin-left:4px;">scanned</span>
    </div>
  </div>

  <!-- Platform breakdown -->
  {_platform_summary(tiers)}

  <!-- Job cards -->
  <div style="background:#fff;padding:20px 24px;">

    <h2 style="font-size:15px;font-weight:700;color:#0C447C;margin:0 0 14px;
               border-bottom:2px solid #E6F1FB;padding-bottom:8px;">
      Tier 1 &mdash; Strong Fit (Score 8-10) &mdash; Tailor &amp; Apply
    </h2>
    {t1_html}

    <h2 style="font-size:15px;font-weight:700;color:#3C3489;margin:20px 0 14px;
               border-bottom:2px solid #EEEDFE;padding-bottom:8px;">
      Tier 2 &mdash; Decent Fit (Score 5-7) &mdash; Base Resume Apply
    </h2>
    {t2_html}

  </div>

  <!-- Footer -->
  <div style="background:#f7f7f7;padding:12px 24px;font-size:11px;
              color:#aaa;text-align:center;border-top:1px solid #eee;">
    AI Job Hunter Pro &bull; Apify + Groq + GitHub Actions &bull;
    Runs every hour 6am&ndash;10pm EST
  </div>

</div>
</body>
</html>"""


def send_email(tiers: dict) -> None:
    t1_count = len(tiers.get("T1", []))
    t2_count = len(tiers.get("T2", []))

    if t1_count + t2_count == 0:
        logger.info("No T1/T2 jobs this run — skipping email")
        return

    run_time = datetime.now().strftime("%b %d, %Y %I:%M %p")
    subject = (
        f"[Job Alert] {t1_count} strong + {t2_count} decent matches — {run_time}"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = NOTIFY_EMAIL
    msg.attach(MIMEText(_build_html(tiers, run_time), "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, NOTIFY_EMAIL, msg.as_string())
        logger.info(f"Email sent: {subject}")
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        raise
