#!/bin/bash
# launchd guard for the BoatHire24 listing-outreach campaign.
#
# Invoked by ~/Library/LaunchAgents/com.boathire24.outreach.plist — fires hourly
# (StartInterval) plus on load and on wake, mirroring the daily-content agent. Robust
# to the laptop sleeping through any fixed time (macOS cron never fired here; launchd does).
#
# Every fire:
#   scan     : poll Gmail, suppress opt-outs, auto-onboard "interested", re-sync the sheet.
# Once per calendar day, in pipeline order (discover -> reach -> contact):
#   maps     : discover new operators worldwide via Google Maps (quota-capped; dedup resumes next day).
#   enrich   : find email / contact-form / IG for 1/7 of email-less leads (cycles weekly).
#   followup : drip-capped follow-ups now due.
#   cold     : drip-capped cold outreach to newly-reachable providers.
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin"
DIR="$(cd "$(dirname "$0")" && pwd)"
cd /Users/master/boat-rental-marbella || exit 1
mkdir -p logs
TODAY="$(date +%F)"

# run_daily <marker-file> <cron.sh subcommand> — run at most once per calendar day.
run_daily() {
  if [ "$(cat "$1" 2>/dev/null)" != "$TODAY" ]; then
    /bin/bash "$DIR/cron.sh" "$2" && echo "$TODAY" > "$1"
  fi
}

# Always: keep replies / opt-outs / the sheet fresh.
/bin/bash "$DIR/cron.sh" scan

# Once per day: discover -> find emails -> follow up -> cold outreach.
run_daily logs/.maps_last_run     maps
run_daily logs/.enrich_last_run   enrich
run_daily logs/.followup_last_run followup
run_daily logs/.cold_last_run     cold
run_daily logs/.blogreach_last_run blogreach
