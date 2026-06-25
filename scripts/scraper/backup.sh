#!/bin/bash
cd /Users/master/boat-rental-marbella || exit 1
B=~/boathire24-pipeline-backup
mkdir -p "$B"
cp -r scripts/scraper "$B/scraper" 2>/dev/null
cp config/scraper_sheet.json "$B/" 2>/dev/null
/usr/bin/sqlite3 data/scraper/leads.db ".dump" > "$B/leads_db.sql" 2>/dev/null
tar -czf ~/boathire24-pipeline-backup.tar.gz -C "$B" . 2>/dev/null
