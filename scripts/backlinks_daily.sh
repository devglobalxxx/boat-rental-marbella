#!/bin/bash
# Daily BoatHire24 backlink drip (SEO + LLM optimised, image-rich articles).
#   graph.org   : 2-6/day randomized  (auto-refill backlog when < 30 pending)
#   rentry.co   : KILLED 2026-07-06 — rentry serves every paste with noindex,
#                 so all 305 published articles carry zero SEO value. Budget
#                 redirected to owner link-backs + citations instead.
#   telegra.ph  : 1-3/day randomized
#   LiveJournal : 1-3/day randomized
#   JustPaste.it: NOT used
#
# Anti-footprint measures (SEO audit 2026-07): volumes are randomized per run,
# ~15% of days are skipped entirely, and the run starts after a random delay of
# up to 45 min so publishes never stamp the same minute daily. These pages are
# treated as discovery/LLM-visibility content, not ranking links — do NOT scale
# the volumes back up.
#
# Failure alerting: the run writes logs/backlinks_status.json and exits 1 with a
# loud ALERT line when nothing was published despite a pending backlog (this is
# what let the June 2026 breakage run silent for 3 weeks).
# Installed via com.boathire24.backlinks.plist.
cd /Users/master/boat-rental-marbella || exit 1
mkdir -p logs
LOG=logs/backlinks_daily.log
PY=/usr/bin/python3
STAGGER=${BACKLINKS_STAGGER:-35}   # base seconds between individual posts
REFILL_BELOW=30                    # generate more when pending < this
REFILL_N=30                        # how many to generate per refill

# Randomized daily volumes (override with env for manual runs/testing)
GRAPH_N=${GRAPH_N:-$((RANDOM % 5 + 2))}         # 2-6
TELEGRAPH_N=${TELEGRAPH_N:-$((RANDOM % 3 + 1))} # 1-3
LJ_N=${LJ_N:-$((RANDOM % 3 + 1))}               # 1-3

# published count for a channel state file (graph_org_state.json etc.)
_published_count() {
  local state="$1"
  if [ -f "config/$state" ]; then
    $PY -c "import json;print(len(json.load(open('config/$state')).get('published',{})))"
  else echo 0; fi
}

# pending = (#backlog files) - (#published) for a channel
_pending() {
  local dir="$1" state="$2" total pub
  total=$(ls "content/$dir/"*.json 2>/dev/null | wc -l | tr -d ' ')
  pub=$(_published_count "$state")
  echo $(( total - pub ))
}

# telegraph ledger lives in logs/, not config/, and holds a list not a dict
_telegraph_count() {
  $PY -c "import json,pathlib;p=pathlib.Path('logs/telegraph_published.json');print(len(json.load(p.open()).get('published',[])) if p.exists() else 0)"
}

# post N articles via a channel script, one at a time, sleeping between (staggered + jitter)
_drip_graph() {
  local n="$1" i
  echo "--- graph.org (x$n, staggered) ---"
  for ((i=1; i<=n; i++)); do
    $PY scripts/graph_org_publish.py publish-next 1
    [ "$i" -lt "$n" ] && sleep $((STAGGER + RANDOM % 60))
  done
}
_drip_telegraph() {
  local n="$1" i
  echo "--- telegra.ph (x$n, staggered) ---"
  for ((i=1; i<=n; i++)); do
    $PY scripts/telegraph_publish.py --n 1
    [ "$i" -lt "$n" ] && sleep $((STAGGER + RANDOM % 60))
  done
}
_drip_lj() {
  local n="$1" i
  echo "--- LiveJournal (x$n, staggered) ---"
  for ((i=1; i<=n; i++)); do
    $PY scripts/livejournal_post.py post-next 1
    [ "$i" -lt "$n" ] && sleep $((STAGGER + RANDOM % 60))
  done
}

{
  echo "================ backlinks drip $(date '+%Y-%m-%d %H:%M:%S') ================"

  # ~15% of days: publish nothing at all (cadence noise)
  if [ -z "$BACKLINKS_NO_SKIP" ] && (( RANDOM % 100 < 15 )); then
    echo "skip day (randomized cadence) — nothing published"
    $PY -c "import json,datetime;json.dump({'date':datetime.date.today().isoformat(),'skipped':True,'published':{'graph_org':0,'telegraph':0,'livejournal':0}},open('logs/backlinks_status.json','w'),indent=1)"
    exit 0
  fi

  # random start delay up to 45 min so runs never stamp the same minute
  if [ -z "$BACKLINKS_NO_DELAY" ]; then
    D=$((RANDOM % 2700))
    echo "random start delay: ${D}s"
    sleep "$D"
  fi

  GP_BEFORE=$(_published_count graph_org_state.json)
  TG_BEFORE=$(_telegraph_count)
  LJ_BEFORE=$(_published_count livejournal_state.json)
  GP_PENDING=$(_pending graph_org graph_org_state.json)
  LJ_PENDING=$(_pending livejournal livejournal_state.json)
  echo "graph.org pending before: $GP_PENDING · LJ pending before: $LJ_PENDING"
  echo "volumes today: graph=$GRAPH_N telegraph=$TELEGRAPH_N lj=$LJ_N"

  # POST FIRST (from the existing buffer, so posting never waits on generation),
  # THEN top up the backlog for the next run.
  _drip_graph "$GRAPH_N"
  # rentry.co channel killed (noindex — zero SEO value); see header comment.
  _drip_telegraph "$TELEGRAPH_N"
  _drip_lj "$LJ_N"

  # Refill graph.org backlog for tomorrow (best effort, after posting)
  gp=$(_pending graph_org graph_org_state.json)
  [ "$gp" -lt "$REFILL_BELOW" ] && { echo "refilling graph.org (+$REFILL_N)..."; $PY scripts/backlink_generate.py graph_org "$REFILL_N"; }

  GP_NEW=$(( $(_published_count graph_org_state.json) - GP_BEFORE ))
  TG_NEW=$(( $(_telegraph_count) - TG_BEFORE ))
  LJ_NEW=$(( $(_published_count livejournal_state.json) - LJ_BEFORE ))
  TOTAL_NEW=$(( GP_NEW + TG_NEW + LJ_NEW ))

  $PY -c "import json,datetime,sys;json.dump({'date':datetime.date.today().isoformat(),'skipped':False,'published':{'graph_org':int(sys.argv[1]),'telegraph':int(sys.argv[2]),'livejournal':int(sys.argv[3])}},open('logs/backlinks_status.json','w'),indent=1)" "$GP_NEW" "$TG_NEW" "$LJ_NEW"

  echo "--- published this run: graph=$GP_NEW telegraph=$TG_NEW lj=$LJ_NEW ---"
  echo "--- backlog levels ---"
  $PY scripts/graph_org_publish.py status | head -1
  echo "telegra.ph: $(_telegraph_count) published (generated on demand, no backlog)"
  $PY scripts/livejournal_post.py status | head -1

  if [ "$TOTAL_NEW" -eq 0 ] && { [ "$GP_PENDING" -gt 0 ] || [ "$LJ_PENDING" -gt 0 ]; }; then
    echo "ALERT: 0 articles published this run despite pending backlog — investigate logs/backlinks_daily.log"
    exit 1
  fi
} >> "$LOG" 2>&1
