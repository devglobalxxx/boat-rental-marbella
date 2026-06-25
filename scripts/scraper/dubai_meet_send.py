"""Dubai in-person follow-up (Mardo Soo) — "I'm in Dubai this week, let's meet".

A warm 2nd touch to UAE operators (country='AE') to convert via a face-to-face
meeting while the founder is on the ground. Reuses outreach.py for the Resend send,
hard-suppression (STOP/opt-out), competitor filter and best-email picking. Dedups via
its own `dubai_meet` table, so it is safe to re-run / resume.

  python3 -m scripts.scraper.dubai_meet_send --dry-run        # preview + count, sends nothing
  python3 -m scripts.scraper.dubai_meet_send --to-self        # send one copy to info@boathire24.com
  python3 -m scripts.scraper.dubai_meet_send --all --sleep 3  # real send to all UAE candidates
"""
from __future__ import annotations
import argparse, json, time, random
from . import store, outreach
from .dubai_launch_send import SIG_HTML  # reuse the Mardo signature block

FROM = "Mardo Soo <info@boathire24.com>"
SUBJECT = "In Dubai this week — can we meet about your boats?"

BODY = """Hi,

This is Mardo, founder of BoatHire24.com — I reached out recently about featuring your boats on our platform.

I'm in Dubai in person this week, and I'd love to meet you face to face — 15 minutes at your marina or over a coffee — to show you how BoatHire24 works and get your boats listed.

It's free to list: no onboarding fee, no listing fee, and we only earn a small commission on completed bookings. As part of our Dubai launch we're also creating professional photo and video content of featured boats.

Are you free in the next few days? Just reply with a day and time that suits you and I'll come to you.

Best regards,

Mardo Soo
Founder
BoatHire24.com

— You're receiving this because your email is publicly listed on {domain} as a boat rental contact. Reply STOP and we'll never email you again."""


def to_html(domain):
    lines = []
    for line in BODY.splitlines():
        if line.startswith("— "):
            break
        lines.append(line)
    while lines and lines[-1].strip() in ("", "BoatHire24.com", "Founder", "Mardo Soo"):
        lines.pop()
    if lines and lines[-1].rstrip(",") == "Best regards":
        lines.pop()
    while lines and lines[-1].strip() == "":
        lines.pop()
    body_html = ""
    for line in lines:
        s = line.strip()
        if s == "":
            body_html += "<br>"
        elif s.startswith("http://") or s.startswith("https://"):
            disp = s.split("://", 1)[1]
            body_html += f'<p style="margin:0 0 14px;"><a href="{s}" style="color:#c9a84e;font-weight:600;text-decoration:none;">{disp} →</a></p>'
        elif s.startswith("- ") or s.startswith("• "):
            body_html += f'<p style="margin:0 0 6px 14px;line-height:1.5;color:#1a1a1a;">• {s[2:]}</p>'
        else:
            body_html += f'<p style="margin:0 0 12px;line-height:1.55;color:#1a1a1a;">{s}</p>'
    return f"""<!doctype html><html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f6f6f4;font-family:-apple-system,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f6f6f4;padding:30px 16px;"><tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:10px;padding:32px;max-width:600px;"><tr><td style="font-size:15px;color:#1a1a1a;">
{body_html}{SIG_HTML.format(domain=domain)}
</td></tr></table></td></tr></table></body></html>"""


def ensure_meet_table(con):
    con.execute("""CREATE TABLE IF NOT EXISTS dubai_meet(
        domain TEXT, email TEXT, sent_at TEXT DEFAULT (datetime('now')),
        resend_id TEXT, status TEXT, error TEXT)""")
    con.commit()


def already_meet_sent(con, domain):
    return con.execute("SELECT 1 FROM dubai_meet WHERE domain=? AND status='sent'", (domain,)).fetchone() is not None


def record_meet(con, domain, email, rid, status, error=""):
    con.execute("INSERT INTO dubai_meet(domain,email,resend_id,status,error) VALUES(?,?,?,?,?)",
                (domain, email, rid, status, error))
    con.commit()


def candidates(con, limit=None):
    outreach.ensure_outreach_table(con)
    ensure_meet_table(con)
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
        if already_meet_sent(con, domain):
            continue
        out.append({"domain": domain, "company": company or "", "city": city or "", "email": email})
        if limit and len(out) >= limit:
            break
    return out


def send_one(con, r, to_self=False):
    import urllib.request, urllib.error
    target = "info@boathire24.com" if to_self else r["email"]
    text = BODY.format(domain=r["domain"])
    html = to_html(r["domain"])
    payload = {"from": FROM, "to": [target], "reply_to": outreach.REPLY_TO,
               "subject": SUBJECT, "text": text, "html": html}
    body = json.dumps(payload).encode()
    req = urllib.request.Request("https://api.resend.com/emails", data=body, method="POST",
        headers={"Authorization": f"Bearer {outreach.RESEND_KEY}", "Content-Type": "application/json",
                 "User-Agent": "BoatHire24-Outreach/1.0", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode()).get("id"), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.read().decode()[:200]}"
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--limit", type=int, default=300)
    ap.add_argument("--to-self", action="store_true")
    ap.add_argument("--sleep", type=float, default=3.0)
    args = ap.parse_args()
    con = store.connect()
    recs = candidates(con, limit=None if args.all else args.limit)
    print(f"UAE meet-followup candidates: {len(recs)}")
    if args.dry_run:
        r = recs[0] if recs else {"domain": "example-dubai-yacht.com", "email": "-"}
        print(f"\nFROM: {FROM}\nSUBJECT: {SUBJECT}\nTO (sample): {r.get('email','-')} ({r['domain']})\n")
        print(BODY.format(domain=r["domain"]))
        print(f"\n(dry-run; {len(recs)} would receive)")
        return
    sent = failed = 0
    for i, r in enumerate(recs, 1):
        rid, err = send_one(con, r, to_self=args.to_self)
        if rid:
            if not args.to_self:
                record_meet(con, r["domain"], r["email"], rid, "sent")
            sent += 1
            print(f"  [{i:>3}/{len(recs)}] OK {r['domain']:<30} -> {'self' if args.to_self else r['email']}", flush=True)
        else:
            if not args.to_self:
                record_meet(con, r["domain"], r["email"], None, "failed", err or "")
            failed += 1
            print(f"  [{i:>3}/{len(recs)}] XX {r['domain']:<30} {err}", flush=True)
        time.sleep(args.sleep + random.random())
    print(f"\nDone. sent={sent} failed={failed}")


if __name__ == "__main__":
    main()
