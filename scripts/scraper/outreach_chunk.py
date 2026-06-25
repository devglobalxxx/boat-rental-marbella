"""Send cold outreach for a shard of unsent candidates. Parallel-safe.

  python3 -m scripts.scraper.outreach_chunk --shard 0 --shards 6 --max 60
"""
from __future__ import annotations
import argparse, time, random
from . import store, outreach

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, required=True)
    ap.add_argument("--shards", type=int, required=True)
    ap.add_argument("--sleep", type=float, default=1.5)
    ap.add_argument("--max", type=int, default=200)
    ap.add_argument("--to-self", action="store_true")
    args = ap.parse_args()
    con = store.connect(); outreach.ensure_outreach_table(con)
    allrecs = outreach.candidates(con)
    mine = [r for r in allrecs if hash(r["domain"]) % args.shards == args.shard][:args.max]
    print(f"shard {args.shard}/{args.shards}: {len(mine)} to send", flush=True)
    sent = failed = 0
    for i, r in enumerate(mine, 1):
        lang, subj, body = outreach.render(r)
        target = "info@boathire24.com" if args.to_self else r["email"]
        rid, err = outreach.resend_send(target, subj, body, html=outreach._text_to_html(body, r["domain"]))
        if rid:
            outreach.record(con, r["domain"], r["email"], lang, subj, rid, "sent"); sent += 1
        else:
            outreach.record(con, r["domain"], r["email"], lang, subj, None, "failed", err or ""); failed += 1
        if i % 10 == 0:
            print(f"shard {args.shard}: {i}/{len(mine)} sent={sent} failed={failed}", flush=True)
        time.sleep(args.sleep + random.random() * 0.5)
    print(f"shard {args.shard} DONE: sent={sent} failed={failed}", flush=True)

if __name__ == "__main__":
    main()
