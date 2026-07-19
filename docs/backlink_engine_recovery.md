# Backlink engine recovery runbook (2026-07-19)

Diagnosed from a `nunnu` machine that has this repo cloned but cannot reach `master`
(no SSH configured, no local Python packages, no `.env`) — everything below has to be
run **on `master`** (`/Users/master/boat-rental-marbella`), by whoever has terminal
access there (per `docs/AGENT_HANDOFF.md`, that's most likely Mardo).

## 1. Pull the fix that's already pushed but not live

Commit `8b9193ee` (2026-07-18 23:57, "SEO/LLM audit fixes ... off-page drip repaired")
decoupled `graph_org_publish.py` from a stale `tp.get_token()` import into
`telegraph_publish.py` that no longer existed. The 2026-07-19 09:30 cron run still hit
the old `AttributeError: module 'tp' has no attribute 'get_token'` — meaning master's
checkout was still on the pre-fix commit when that run fired.

```bash
cd /Users/master/boat-rental-marbella
git status                # check for uncommitted local changes first — the daily
                           # cron does `git add -A && push`, so there may be pending
                           # work; stash or commit before pulling if so
git pull origin main
git log -1 --oneline      # should show 2c5a4163 or later
```

## 2. Verify the fix actually works (dry, no real posting)

```bash
python3 scripts/graph_org_publish.py status
# should print "graph.org: N published / M in backlog / P pending" with no traceback

python3 scripts/telegraph_publish.py --dry-run --n 1
# should generate + log a dry-run article, no traceback
```

If either still errors, the bug is deeper than the token-lookup fix — capture the
traceback and it's a fresh diagnosis, not a re-run of this same issue.

## 3. Refill the LiveJournal backlog (currently 0 pending)

```bash
python3 scripts/backlink_generate.py livejournal 30
python3 scripts/livejournal_post.py status
```

## 4. Run the daily drip manually once to confirm end-to-end

```bash
BACKLINKS_NO_SKIP=1 BACKLINKS_NO_DELAY=1 bash scripts/backlinks_daily.sh
tail -40 logs/backlinks_daily.log
cat logs/backlinks_status.json
```

Expect non-zero `published` counts for graph_org and telegraph, no `ALERT:` line.
Once confirmed, the existing launchd schedule (`com.boathire24.backlinks.plist`) takes
over again automatically — no need to change the schedule itself.

## 5. Resume blogreach guest-post outreach (separate from the above — do NOT combine)

1,895 discovered blogs have a contact email; only ~222 have actually been contacted
(213 form submissions frozen since 2026-06-04, 9 resumed 2026-07-19 via the newer
`blog_outreach` path). This is real outbound email/form-submission to third parties —
**get explicit sign-off on batch size before running**, this isn't a "just run it" step.

```bash
cd /Users/master/boat-rental-marbella
sqlite3 data/scraper/leads.db "select count(*) from blogs where emails != '' and emails is not null and domain not in (select domain from blog_outreach) and domain not in (select domain from form_outreach);"
# ^ shows how many enriched blogs have NEVER been contacted by either pipeline —
#   this is the real untapped backlog, decide the batch size from this number

python3 scripts/scraper/blogreach.py sendform --limit <N> --dry-run   # preview first
python3 scripts/scraper/blogreach.py sendform --limit <N>             # then live
```

(Check `scripts/scraper/blogreach.py --help` for the exact current subcommand/flag
names before running — this repo snapshot may drift from what's on master.)

## Why this file exists

`nunnu` (this machine) has no execution path to any of the above — no SSH to master,
no Python packages, no `.env`/API keys. This doc is the handoff so a session running
*on* master (or a human with terminal access there) can pick this up without
re-deriving the diagnosis. Delete or update this file once steps 1-4 are confirmed
working and step 5 has an agreed batch size.
