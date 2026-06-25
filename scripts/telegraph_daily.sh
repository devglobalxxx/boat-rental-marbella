#!/bin/bash
# Daily telegra.ph drip: publish 3 BoatHire24 backlink articles from the backlog.
# Installed via com.boathire24.telegraph.plist (runs once a day).
cd /Users/master/boat-rental-marbella || exit 1
mkdir -p logs
{
  echo "===== telegraph drip $(date '+%Y-%m-%d %H:%M:%S') ====="
  /usr/bin/python3 scripts/telegraph_publish.py publish-next 3
  # Warn when the backlog is running low so it can be topped up in a session.
  PENDING=$(/usr/bin/python3 scripts/telegraph_publish.py status | head -1)
  echo "$PENDING"
  case "$PENDING" in
    *"/ 0 pending"*|*"/ 1 pending"*|*"/ 2 pending"*|*"/ 3 pending"*|*"/ 4 pending"*|*"/ 5 pending"*)
      echo "LOW BACKLOG: regenerate more articles into content/telegraph/ soon." ;;
  esac
} >> logs/telegraph_post.log 2>&1
