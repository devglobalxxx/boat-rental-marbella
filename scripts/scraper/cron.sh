#!/bin/bash
# Wrapper invoked by crontab. Cron's PATH is minimal — set it explicitly.
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin"
cd /Users/master/boat-rental-marbella || exit 1
mkdir -p logs
TS=$(date +"%Y-%m-%d %H:%M:%S")
case "$1" in
  scan)
    echo "[$TS] scan start" >> logs/cron.log
    /usr/bin/python3 -m scripts.scraper.followup scan >> logs/cron.log 2>&1
    /usr/bin/python3 -m scripts.scraper.sync_outreach_sheet >> logs/cron.log 2>&1
    echo "[$TS] scan done" >> logs/cron.log
    ;;
  followup)
    echo "[$TS] followup start" >> logs/cron.log
    # Drip-capped at 400/day (oldest-sent first) to protect sender-domain
    # reputation. The 404-recovery copy auto-applies to pre-2026-06-01 sends.
    /usr/bin/python3 -m scripts.scraper.followup send --limit 400 --sleep 3 >> logs/cron.log 2>&1
    /usr/bin/python3 -m scripts.scraper.sync_outreach_sheet >> logs/cron.log 2>&1
    echo "[$TS] followup done" >> logs/cron.log
    ;;
  cold)
    echo "[$TS] cold-send start" >> logs/cron.log
    # Email up to 400 fresh, never-contacted operators/day (oldest-confidence first),
    # suppression-checked. Drips new leads instead of spiking the domain.
    /usr/bin/python3 -m scripts.scraper.outreach_chunk --shard 0 --shards 1 --max 400 --sleep 3 >> logs/cron.log 2>&1
    /usr/bin/python3 -m scripts.scraper.sync_outreach_sheet >> logs/cron.log 2>&1
    echo "[$TS] cold-send done" >> logs/cron.log
    ;;
  maps)
    echo "[$TS] maps-seed start" >> logs/cron.log
    # Discover new operators worldwide (Google Maps Places). Runs until the daily API
    # quota is hit; url-dedup resumes from the next city on the following day.
    /usr/bin/python3 -m scripts.scraper.seed_maps --queries 10 >> logs/cron.log 2>&1
    echo "[$TS] maps-seed done" >> logs/cron.log
    ;;
  enrich)
    echo "[$TS] enrich start" >> logs/cron.log
    # Find email / contact-form / IG for 1/7 of the email-less leads each day (cycles weekly).
    /usr/bin/python3 -m scripts.scraper.enrich_chunk --shard "$(date +%w)" --shards 7 --workers 8 >> logs/cron.log 2>&1
    /usr/bin/python3 -m scripts.scraper.sync_outreach_sheet >> logs/cron.log 2>&1
    echo "[$TS] enrich done" >> logs/cron.log
    ;;
  getlisted)
    echo "[$TS] getlisted start" >> logs/cron.log
    # Re-engagement drip (400/day) to operators we emailed who never replied —
    # the zero-cost "get-listed" concierge angle. Excludes STOP/bounce/spam.
    /usr/bin/python3 -m scripts.scraper.getlisted_send --limit 400 --sleep 3 >> logs/cron.log 2>&1
    /usr/bin/python3 -m scripts.scraper.sync_outreach_sheet >> logs/cron.log 2>&1
    echo "[$TS] getlisted done" >> logs/cron.log
    ;;
  activate)
    echo "[$TS] activate start" >> logs/cron.log
    # Weekly nudge to boathire24.com users who signed up but have no active boat
    # listing yet (warmest leads). Pulls emails from Supabase auth.users.
    /usr/bin/python3 -m scripts.scraper.activation_drip --send --limit 200 --sleep 3 >> logs/cron.log 2>&1
    echo "[$TS] activate done" >> logs/cron.log
    ;;
  blogreach)
    echo "[$TS] blogreach start" >> logs/cron.log
    # Travel-blog partnership outreach (link-swap). Top up the pool from listicles +
    # a little DDG breadth, enrich, then drip a capped batch: contact form first
    # (email fallback on captcha/JS), plus direct email to guarantee volume.
    # Everything dedupes on leads.db, so a blog is never contacted twice.
    [ -f config/blog_listicles.txt ] && /usr/bin/python3 -m scripts.scraper.blogreach harvest-urls --file config/blog_listicles.txt >> logs/cron.log 2>&1
    /usr/bin/python3 -m scripts.scraper.blogreach discover --limit-kw 15 >> logs/cron.log 2>&1
    /usr/bin/python3 -m scripts.scraper.blogreach enrich --limit 300 --workers 12 >> logs/cron.log 2>&1
    /usr/bin/python3 -m scripts.scraper.blogreach push-sheet >> logs/cron.log 2>&1
    /usr/bin/python3 -m scripts.scraper.blogreach send-form --limit 60 >> logs/cron.log 2>&1
    /usr/bin/python3 -m scripts.scraper.blogreach send-email --any --limit 140 >> logs/cron.log 2>&1
    /usr/bin/python3 -m scripts.scraper.blogreach sync-sheet >> logs/cron.log 2>&1
    echo "[$TS] blogreach done" >> logs/cron.log
    ;;
  *) echo "usage: $0 {scan|followup|cold|maps|enrich|activate|getlisted|blogreach}"; exit 2 ;;
esac
