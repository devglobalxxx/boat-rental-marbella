"""Re-engagement campaign — the "get-listed concierge" angle to operators we
already emailed but who NEVER replied. Zero-cost, keep-100%, we add 15% on top.

Targets outreach.email rows that:
  - were successfully sent (status='sent')
  - never replied (replied=0/NULL)
  - are NOT suppressed: no STOP/unsubscribe, no bounce, no 'not interested',
    no failed send, not a noreply address, not a competitor domain
Dedups via its own `getlisted` table, so it is safe to re-run / resume.

  python3 -m scripts.scraper.getlisted_send --dry-run          # preview + count, sends nothing
  python3 -m scripts.scraper.getlisted_send --to-self          # one copy to info@boathire24.com
  python3 -m scripts.scraper.getlisted_send --limit 400 --sleep 3   # daily drip
  python3 -m scripts.scraper.getlisted_send --all --sleep 3
"""
from __future__ import annotations
import argparse, time
from . import store, outreach

FROM = "Mardo Soo <info@boathire24.com>"
SUBJECT = "List your boats on BoatHire24 — free, you keep 100%"
GET_LISTED_URL = "https://boathire24.com/get-listed"

BODY = """Hi,

Get your boats in front of thousands more renters — at zero cost to you.

Send us your website and the boats you charter. We list them on BoatHire24, market them, and bring you bookings. You keep 100% of your price — paid by the renter.

We add a 15% commission on top of your price — so you always receive exactly what you charge today.

Get started here:
{url}

Or just reply with your website and we'll build your listings for you.

Best regards,

Mardo Soo
Founder
BoatHire24.com

— You're receiving this because your email is publicly listed on {domain} as a boat rental contact. Reply STOP and we'll never email you again."""


def ensure_table(con):
    con.execute("""CREATE TABLE IF NOT EXISTS getlisted(
        domain TEXT, email TEXT, sent_at TEXT DEFAULT (datetime('now')),
        resend_id TEXT, status TEXT, error TEXT)""")
    con.commit()


def already_getlisted(con, email):
    return con.execute("SELECT 1 FROM getlisted WHERE email=? AND status='sent'", (email,)).fetchone() is not None


def candidates(con, limit=None):
    outreach.ensure_outreach_table(con)
    ensure_table(con)
    suppressed = outreach.hard_suppressed_emails(con)
    # emails that ever bounced / said STOP / not-interested / failed → never touch
    bad = {r[0] for r in con.execute(
        "SELECT DISTINCT email FROM outreach WHERE reply_class IN ('stop','bounce','no') OR status='failed'")}
    rows = con.execute("""SELECT DISTINCT domain, email FROM outreach
        WHERE status='sent' AND (replied IS NULL OR replied=0)
        ORDER BY domain""").fetchall()
    out, seen = [], set()
    for domain, email in rows:
        if not email or email in seen: continue
        e = email.lower()
        if e in suppressed or email in bad: continue
        if "noreply" in e or "no-reply" in e or "donotreply" in e: continue
        if domain in outreach.COMPETITOR_DOMAINS: continue
        if any(domain.endswith("." + c) for c in outreach.COMPETITOR_DOMAINS): continue
        if already_getlisted(con, email): continue
        seen.add(email)
        out.append({"domain": domain, "email": email})
        if limit and len(out) >= limit: break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--to-self", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--limit", type=int, default=400)
    ap.add_argument("--sleep", type=float, default=3.0)
    args = ap.parse_args()
    con = store.connect()
    cap = None if args.all else args.limit
    cands = candidates(con, limit=cap)
    print(f"get-listed re-engagement candidates: {len(cands)}"
          + (" (ALL)" if args.all else f" (cap {args.limit})"))
    if args.dry_run:
        c = cands[0] if cands else {"domain": "example.com", "email": "info@example.com"}
        print(f"\nFROM: {FROM}\nSUBJECT: {SUBJECT}\nTO (sample): {c['email']} ({c['domain']})\n")
        print(BODY.format(url=GET_LISTED_URL, domain=c["domain"]))
        print(f"\n(dry-run; {len(cands)} would receive)")
        return
    sent = failed = 0
    for i, c in enumerate(cands, 1):
        to = "info@boathire24.com" if args.to_self else c["email"]
        text = BODY.format(url=GET_LISTED_URL, domain=c["domain"])
        rid, err = outreach.resend_send(to, SUBJECT, text,
                                        html=outreach._text_to_html(text, c["domain"]), from_=FROM)
        st = "sent" if rid else "failed"
        con.execute("INSERT INTO getlisted(domain,email,resend_id,status,error) VALUES(?,?,?,?,?)",
                    (c["domain"], c["email"], rid, st, err or "")); con.commit()
        if rid: sent += 1
        else: failed += 1
        print(f"  [{i}/{len(cands)}] {'OK' if rid else 'XX'} {c['domain']:<32} -> {to}  {err or ''}", flush=True)
        if args.to_self and i >= 1: break
        time.sleep(args.sleep)
    print(f"\nDone. sent={sent} failed={failed}")


if __name__ == "__main__":
    main()
