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
#              suppression-checked) of follow-ups that are now due, then re-sync the sheet.
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin"
DIR="$(cd "$(dirname "$0")" && pwd)"
cd /Users/master/boat-rental-marbella || exit 1
mkdir -p logs
MARK="logs/.followup_last_run"
TODAY="$(date +%F)"

# Always: keep replies / opt-outs / the sheet fresh.
/bin/bash "$DIR/cron.sh" scan

# Once per day: send any follow-ups that have come due.
if [ "$(cat "$MARK" 2>/dev/null)" != "$TODAY" ]; then
  /bin/bash "$DIR/cron.sh" followup && echo "$TODAY" > "$MARK"
fi
