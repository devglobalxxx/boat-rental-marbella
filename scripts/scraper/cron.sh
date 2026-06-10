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
  *) echo "usage: $0 {scan|followup|cold}"; exit 2 ;;
esac
