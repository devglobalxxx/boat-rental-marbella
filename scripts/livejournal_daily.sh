#!/bin/bash
# Daily LiveJournal drip: post 3 BoatHire24 backlink articles from the backlog.
cd /Users/master/boat-rental-marbella || exit 1
mkdir -p logs
{
  echo "===== livejournal drip $(date '+%Y-%m-%d %H:%M:%S') ====="
  /usr/bin/python3 scripts/livejournal_post.py post-next 3
  /usr/bin/python3 scripts/livejournal_post.py status | head -1
} >> logs/livejournal_post.log 2>&1
