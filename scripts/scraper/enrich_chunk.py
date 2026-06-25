"""Enrich a shard of email-less leads — find email / contact-form / Instagram /
Facebook / WhatsApp. Safe to run many in parallel (SQLite WAL).

  python3 -m scripts.scraper.enrich_chunk --shard 0 --shards 15
"""
from __future__ import annotations
import argparse, json
from concurrent.futures import ThreadPoolExecutor, as_completed
from . import store, enrich as E

def ensure_social(con):
    cols = {r[1] for r in con.execute("PRAGMA table_info(leads)")}
    for c in ("instagram","facebook","whatsapp"):
        if c not in cols:
            con.execute(f"ALTER TABLE leads ADD COLUMN {c} TEXT")
    con.commit()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, required=True)
    ap.add_argument("--shards", type=int, required=True)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--max-pages", type=int, default=7)
    ap.add_argument("--country", type=str, help="only enrich leads in this country code (e.g. AE)")
    args = ap.parse_args()
    con = store.connect(); ensure_social(con)
    # target: leads with NO email yet (phone-only Maps ops + others)
    q = "SELECT domain FROM leads WHERE (emails IS NULL OR emails IN ('','[]'))"
    params = ()
    if args.country:
        q += " AND country=?"; params = (args.country,)
    allrows = con.execute(q, params).fetchall()
    todo = [r[0] for r in allrows if hash(r[0]) % args.shards == args.shard]
    print(f"shard {args.shard}/{args.shards}: {len(todo)}/{len(allrows)} domains", flush=True)
    found_email = found_form = found_ig = 0
    def work(d):
        try: return d, E.enrich_domain(d, max_pages=args.max_pages), None
        except Exception as e: return d, None, f"{type(e).__name__}: {e}"
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for i, f in enumerate(as_completed([ex.submit(work, d) for d in todo]), 1):
            d, res, err = f.result()
            if err or res is None:
                store.save_enrichment(con, d, [], [], None, 0); continue
            # merge phones with existing (Maps gave us phones already)
            row = con.execute("SELECT phones FROM leads WHERE domain=?", (d,)).fetchone()
            old = []
            try: old = json.loads(row[0]) if row and row[0] else []
            except Exception: pass
            merged_phones = sorted(set(old + res["phones"]))
            store.save_enrichment(con, d, res["emails"], merged_phones, res["contact_form"], res["confidence"])
            con.execute("UPDATE leads SET instagram=?, facebook=?, whatsapp=? WHERE domain=?",
                        (res["instagram"], res["facebook"], res["whatsapp"], d)); con.commit()
            if res["emails"]: found_email += 1
            if res["contact_form"]: found_form += 1
            if res["instagram"]: found_ig += 1
            if i % 25 == 0:
                print(f"shard {args.shard}: {i}/{len(todo)} | email={found_email} form={found_form} ig={found_ig}", flush=True)
    print(f"shard {args.shard} DONE: email={found_email} form={found_form} ig={found_ig} of {len(todo)}", flush=True)

if __name__ == "__main__":
    main()
