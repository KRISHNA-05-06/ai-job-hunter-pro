#!/bin/bash
# setup_github.sh
# Run this once to create the GitHub repo and push all code
# Usage: GITHUB_TOKEN=your_token bash setup_github.sh

set -e

REPO_NAME="ai-job-hunter-pro"
GITHUB_USERNAME="KRISHNA-05-06"
GITHUB_TOKEN="${GITHUB_TOKEN}"

if [ -z "$GITHUB_TOKEN" ]; then
  echo "ERROR: Set GITHUB_TOKEN environment variable first"
  echo "Get token at: https://github.com/settings/tokens/new"
  echo "Scopes needed: repo (full control)"
  echo ""
  echo "Usage: GITHUB_TOKEN=your_token bash setup_github.sh"
  exit 1
fi

echo "Creating GitHub repo: ${GITHUB_USERNAME}/${REPO_NAME}..."

# Create the repo via GitHub API
curl -s -X POST \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/user/repos \
  -d "{
    \"name\": \"${REPO_NAME}\",
    \"description\": \"Hourly job alerts from LinkedIn, Indeed, Dice, ZipRecruiter — powered by Apify + Groq + GitHub Actions\",
    \"private\": false,
    \"auto_init\": false
  }" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if 'html_url' in data:
    print('Repo created:', data['html_url'])
elif 'errors' in data:
    print('Error:', data['errors'])
    sys.exit(1)
else:
    print('Response:', data)
"

echo ""
echo "Initializing git and pushing code..."

cd "$(dirname "$0")"

git init
git add .
git commit -m "feat: initial deploy — AI Job Hunter Pro

- LinkedIn, Indeed, Dice, ZipRecruiter via Apify actors
- Groq/Llama AI scoring (1-10 fit score, T1/T2/T3 tiers)
- Hourly HTML email digest with source badges + apply links
- GitHub Actions CI/CD: runs every hour 6am-10pm EST
- Manual trigger workflow for instant testing"

git branch -M main
git remote add origin "https://${GITHUB_TOKEN}@github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"
git push -u origin main

echo ""
echo "================================================================"
echo "Done! Repo live at: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}"
echo ""
echo "NEXT STEP: Add 5 GitHub Secrets at:"
echo "https://github.com/${GITHUB_USERNAME}/${REPO_NAME}/settings/secrets/actions"
echo ""
echo "  APIFY_API_TOKEN"
echo "  GROQ_API_KEY"
echo "  GMAIL_USER"
echo "  GMAIL_APP_PASSWORD"
echo "  NOTIFY_EMAIL"
echo ""
echo "Then trigger a manual test at:"
echo "https://github.com/${GITHUB_USERNAME}/${REPO_NAME}/actions"
echo "================================================================"
