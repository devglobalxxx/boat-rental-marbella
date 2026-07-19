#!/usr/bin/env bash
# Daily travel-blog partnership outreach for BoatHire24.
# Discovers a few fresh blogs, enriches, syncs the Google Sheet, and sends a
# capped daily batch (contact form first, email fallback). Safe to run daily:
# every step dedupes on the leads.db and never re-contacts a blog.
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
export PYTHONUNBUFFERED=1
LOG="logs/blogreach_cron.log"
mkdir -p logs
DAILY_CAP="${BLOGREACH_DAILY_CAP:-60}"   # total outreach/day (form + email)

run() { echo "=== $(date '+%F %T') $* ==="; python3 -m scripts.scraper.blogreach "$@"; }

{
  # 1) top up the pool from listicles (cheap, high-yield) + a little DDG breadth
  [ -f config/blog_listicles.txt ] && run harvest-urls --file config/blog_listicles.txt
  run discover --limit-kw 15
  # 2) enrich anything new
  run enrich --limit 300 --workers 10
  # 3) get new rows into the sheet
  run push-sheet
  # 4) send today's batch — forms first (with email fallback), then pure-email
  run send-form  --limit "$DAILY_CAP"
  run send-email --limit "$DAILY_CAP"
  # 5) reflect outcomes back into the sheet
  run sync-sheet
  run stats
} >> "$LOG" 2>&1
