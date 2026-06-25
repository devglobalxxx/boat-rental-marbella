#!/bin/bash
# Daily BoatHire24 backlink drip (SEO + LLM optimised, image-rich articles).
#   graph.org   : 20/day  (auto-refill backlog when < 30 pending)
#   rentry.co   : 20/day  (auto-refill backlog when < 30 pending)
#   telegra.ph  : 3/day
#   LiveJournal : 3/day
#   JustPaste.it: NOT used
# Posts are staggered (a short sleep between each) rather than bursting, to keep a
# natural publishing footprint. Installed via com.boathire24.backlinks.plist.
cd /Users/master/boat-rental-marbella || exit 1
mkdir -p logs
LOG=logs/backlinks_daily.log
PY=/usr/bin/python3
STAGGER=${BACKLINKS_STAGGER:-35}   # seconds between individual posts
GRAPH_N=${GRAPH_N:-20}             # graph.org posts/day
RENTRY_N=${RENTRY_N:-20}           # rentry.co posts/day
REFILL_BELOW=30                    # generate more when pending < this
REFILL_N=30                        # how many to generate per refill

# pending = (#backlog files) - (#published) for a channel
_pending() {
  local dir="$1" state="$2" total pub
  total=$(ls "content/$dir/"*.json 2>/dev/null | wc -l | tr -d ' ')
  if [ -f "config/$state" ]; then
    pub=$($PY -c "import json;print(len(json.load(open('config/$state')).get('published',{})))")
  else pub=0; fi
  echo $(( total - pub ))
}

# post N articles to one channel, one at a time, sleeping between (staggered)
_drip() {
  local label="$1" script="$2" n="$3" i
  echo "--- $label (x$n, staggered ${STAGGER}s) ---"
  for ((i=1; i<=n; i++)); do
    $PY "scripts/$script" publish-next 1
    [ "$i" -lt "$n" ] && sleep "$STAGGER"
  done
}
# LiveJournal uses 'post-next' instead of 'publish-next'
_drip_lj() {
  local n="$1" i
  echo "--- LiveJournal (x$n, staggered ${STAGGER}s) ---"
  for ((i=1; i<=n; i++)); do
    $PY scripts/livejournal_post.py post-next 1
    [ "$i" -lt "$n" ] && sleep "$STAGGER"
  done
}

{
  echo "================ backlinks drip $(date '+%Y-%m-%d %H:%M:%S') ================"

  # POST FIRST (from the existing buffer, so posting never waits on generation),
  # THEN top up the backlog for the next run.
  echo "graph.org pending before: $(_pending graph_org graph_org_state.json)"
  _drip "graph.org" graph_org_publish.py "$GRAPH_N"
  echo "rentry.co pending before: $(_pending rentry rentry_state.json)"
  _drip "rentry.co" rentry_post.py "$RENTRY_N"

  # telegra.ph + LiveJournal: 3 each
  _drip "telegra.ph" telegraph_publish.py 3
  _drip_lj 3

  # Refill graph.org + rentry.co backlogs for tomorrow (best effort, after posting)
  gp=$(_pending graph_org graph_org_state.json)
  [ "$gp" -lt "$REFILL_BELOW" ] && { echo "refilling graph.org (+$REFILL_N)..."; $PY scripts/backlink_generate.py graph_org "$REFILL_N"; }
  rp=$(_pending rentry rentry_state.json)
  [ "$rp" -lt "$REFILL_BELOW" ] && { echo "refilling rentry.co (+$REFILL_N)..."; $PY scripts/backlink_generate.py rentry "$REFILL_N"; }

  echo "--- backlog levels ---"
  $PY scripts/graph_org_publish.py status | head -1
  $PY scripts/rentry_post.py status | head -1
  $PY scripts/telegraph_publish.py status | head -1
  $PY scripts/livejournal_post.py status | head -1
} >> "$LOG" 2>&1
