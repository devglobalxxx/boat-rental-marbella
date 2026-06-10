#!/bin/bash
# launchd guard for the BoatHire24 listing-outreach campaign.
#
# Invoked by ~/Library/LaunchAgents/com.boathire24.outreach.plist — fires hourly
# (StartInterval) plus on load and on wake, mirroring the daily-content agent. This
# is robust to the laptop sleeping through any fixed time (macOS cron never fired
# here at all; launchd does).
#
#   scan     : every invocation — poll Gmail, suppress opt-outs, auto-onboard
#              "interested" leads, and re-sync the leads Google Sheet. Cheap + idempotent.
#   followup : at most once per calendar day — drip-capped send (<=400/day, oldest first,
#              suppression-checked) of follow-ups now due, then re-sync the sheet.
#   cold     : at most once per calendar day — drip-capped cold outreach (<=400/day) to
#              new, never-contacted providers worldwide, then re-sync the sheet.
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin"
DIR="$(cd "$(dirname "$0")" && pwd)"
cd /Users/master/boat-rental-marbella || exit 1
mkdir -p logs
TODAY="$(date +%F)"
FMARK="logs/.followup_last_run"
CMARK="logs/.cold_last_run"

# Always: keep replies / opt-outs / the sheet fresh.
/bin/bash "$DIR/cron.sh" scan

# Once per day: send follow-ups that have come due.
if [ "$(cat "$FMARK" 2>/dev/null)" != "$TODAY" ]; then
  /bin/bash "$DIR/cron.sh" followup && echo "$TODAY" > "$FMARK"
fi

# Once per day: cold outreach to new, never-contacted providers.
if [ "$(cat "$CMARK" 2>/dev/null)" != "$TODAY" ]; then
  /bin/bash "$DIR/cron.sh" cold && echo "$TODAY" > "$CMARK"
fi
