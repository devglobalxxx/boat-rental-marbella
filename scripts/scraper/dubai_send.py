"""Send the Dubai / UAE boat-rental operator outreach — reuses outreach.py
(Resend send, suppression, STOP footer, personalized list URL). Filters leads
to country='AE' (Dubai, Abu Dhabi, Ras al Khaimah, Fujairah).

  python3 -m scripts.scraper.dubai_send --dry-run
  python3 -m scripts.scraper.dubai_send --to-self --limit 2
  python3 -m scripts.scraper.dubai_send --all --sleep 3
"""
from __future__ import annotations
import argparse, json, time, random
from . import store, outreach


def candidates(con, limit=None):
    outreach.ensure_outreach_table(con)
    suppressed = outreach.hard_suppressed_emails(con)
    cur = con.execute("""SELECT domain,company,city,country,emails FROM leads
        WHERE country='AE' AND emails IS NOT NULL AND emails NOT IN ('','[]')
        ORDER BY confidence DESC""")
    out = []
    for domain, company, city, country, emails_j in cur:
        if domain in outreach.COMPETITOR_DOMAINS:
            continue
        try:
            emails = json.loads(emails_j) if emails_j else []
        except Exception:
            continue
        email = outreach.best_email_for_domain(emails, domain)
        if not email or email.lower() in suppressed:
            continue
        if outreach.already_sent(con, domain, email):
            continue
        out.append({"domain": domain, "company": company or "", "city": city or "",
                    "country": country or "", "email": email})
        if limit and len(out) >= limit:
            break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--to-self", action="store_true")
    ap.add_argument("--sleep", type=float, default=3.0)
    args = ap.parse_args()
    con = store.connect()
    recs = candidates(con, limit=None if args.all else args.limit)
    print(f"UAE candidates: {len(recs)}")
    if args.dry_run:
        for r in recs[:3]:
            lang, subj, body = outreach.render(r, force_lang="en")
            print(f"\n=== {r['domain']} → {r['email']} ({r['city']}) ===\nSubject: {subj}\n{body}")
        print(f"\n(dry-run; showed first 3 of {len(recs)})")
        return
    sent = failed = 0
    for i, r in enumerate(recs, 1):
        lang, subj, body = outreach.render(r, force_lang="en")
        target = "info@boathire24.com" if args.to_self else r["email"]
        rid, err = outreach.resend_send(target, subj, body,
                                        html=outreach._text_to_html(body, r["domain"]))
        if rid:
            outreach.record(con, r["domain"], r["email"], lang, subj, rid, "sent"); sent += 1
            print(f"  [{i:>3}/{len(recs)}] OK {r['domain']:<30} -> {target} ({r['city']})", flush=True)
        else:
            outreach.record(con, r["domain"], r["email"], lang, subj, None, "failed", err or ""); failed += 1
            print(f"  [{i:>3}/{len(recs)}] XX {r['domain']:<30} {err}", flush=True)
        time.sleep(args.sleep + random.random())
    print(f"\nDone. sent={sent} failed={failed}")


if __name__ == "__main__":
    main()
