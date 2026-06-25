"""Dubai-launch operator outreach (Mardo Soo) — the complimentary-experience /
content-feature offer. Reuses outreach.py for Resend send, suppression, STOP
footer. Filters leads to country='AE'.

  python3 -m scripts.scraper.dubai_launch_send --dry-run
  python3 -m scripts.scraper.dubai_launch_send --to-self --limit 1
  python3 -m scripts.scraper.dubai_launch_send --all --sleep 3
"""
from __future__ import annotations
import argparse, json, time, random
from . import store, outreach

FROM = "Mardo Soo <info@boathire24.com>"
SUBJECT = "Featuring your boat in our BoatHire24 Dubai launch"

BODY = """Hi,

My name is Mardo, founder of BoatHire24.com, a global boat rental marketplace.

We are currently expanding our Dubai inventory and are looking to feature selected boat operators on our platform. There is no onboarding fee, no listing fee, and we only earn a commission on completed bookings.

As part of our Dubai launch, we are creating promotional content showcasing local boat rental experiences. We would love to feature your boat in our content and on BoatHire24.

Would you be open to providing a complimentary 1-hour experience for our team? In return, we will:

• Create professional photo and video content of your boat
• Publish the content across BoatHire24 and our social channels
• Feature your company profile and listings on BoatHire24
• Feature your company in our Dubai section for 3 months
• Consider your listings for featured placement during our Dubai expansion

You can list your boat here in about 5 minutes:
https://boathire24.com/list-your-boat

We are currently meeting with operators in Dubai this week and would be happy to stop by and discuss the opportunity in person.

Looking forward to hearing from you.

Best regards,

Mardo Soo
Founder
BoatHire24.com

— You're receiving this because your email is publicly listed on {domain} as a boat rental contact. Reply STOP and we'll never email you again."""

SIG_HTML = """
<table cellpadding="0" cellspacing="0" style="font-family:-apple-system,sans-serif;font-size:14px;color:#1a1a1a;margin-top:8px;">
  <tr><td style="padding-top:18px;border-top:1px solid #e5e5e5;">
    <strong style="color:#07101e;font-size:15px;">Mardo Soo</strong><br>
    <span style="color:#666;font-size:13px;">Founder · BoatHire24</span><br>
    <a href="https://boathire24.com" style="color:#c9a84e;text-decoration:none;font-size:13px;">boathire24.com</a>
  </td></tr>
  <tr><td style="padding-top:14px;font-size:11px;color:#999;line-height:1.5;">
    © 2026 BoatHire24 · You're receiving this because your email is publicly listed on {domain} as a boat-rental contact. Reply <strong>STOP</strong> and we'll never email you again.
  </td></tr>
</table>"""


def to_html(domain):
    import urllib.parse
    lines = []
    for line in BODY.splitlines():
        if line.startswith("— "):
            break
        lines.append(line)
    # drop trailing signature lines (re-added as HTML block)
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
        out.append({"domain": domain, "company": company or "", "city": city or "", "email": email})
        if limit and len(out) >= limit:
            break
    return out


def send_one(con, r, to_self=False):
    target = "info@boathire24.com" if to_self else r["email"]
    text = BODY.format(domain=r["domain"])
    html = to_html(r["domain"])
    # use outreach.resend_send but override FROM via monkey hook
    import urllib.request, urllib.error
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
    print(f"UAE candidates: {len(recs)}")
    if args.dry_run:
        r = recs[0] if recs else {"domain": "example-dubai-yacht.com"}
        print(f"\nFROM: {FROM}\nSUBJECT: {SUBJECT}\nTO (sample): {r.get('email','-')} ({r['domain']})\n")
        print(BODY.format(domain=r["domain"]))
        print(f"\n(dry-run; {len(recs)} would receive)")
        return
    sent = failed = 0
    for i, r in enumerate(recs, 1):
        rid, err = send_one(con, r, to_self=args.to_self)
        if rid:
            if not args.to_self:
                outreach.record(con, r["domain"], r["email"], "en", SUBJECT, rid, "sent")
            sent += 1
            print(f"  [{i:>3}/{len(recs)}] OK {r['domain']:<30} -> {'self' if args.to_self else r['email']}", flush=True)
        else:
            if not args.to_self:
                outreach.record(con, r["domain"], r["email"], "en", SUBJECT, None, "failed", err or "")
            failed += 1
            print(f"  [{i:>3}/{len(recs)}] XX {r['domain']:<30} {err}", flush=True)
        time.sleep(args.sleep + random.random())
    print(f"\nDone. sent={sent} failed={failed}")


if __name__ == "__main__":
    main()
