"""Activation drip for boathire24.com — find users who SIGNED UP but have NO
active boat listing, and nudge them to finish (warmest leads).

Reads Supabase creds from /Users/master/boat-rental-platform/.env.local.
auth.users holds emails (admin API); boats holds listings (PostgREST).

  python3 -m scripts.scraper.activation_drip --audit          # counts + sample, sends nothing
  python3 -m scripts.scraper.activation_drip --dry-run        # preview the email
  python3 -m scripts.scraper.activation_drip --send --limit 50
"""
from __future__ import annotations
import argparse, json, os, pathlib, time, urllib.request, urllib.error
from . import store, outreach

PLATFORM_ENV = pathlib.Path("/Users/master/boat-rental-platform/.env.local")

def _env():
    d = {}
    if PLATFORM_ENV.exists():
        for line in PLATFORM_ENV.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("="); d[k.strip()] = v.strip().strip('"').strip("'")
    url = d.get("NEXT_PUBLIC_SUPABASE_URL") or d.get("SUPABASE_URL")
    key = d.get("SUPABASE_SERVICE_ROLE_KEY")
    return url, key

def _get(url, key, path):
    req = urllib.request.Request(url.rstrip("/") + path,
        headers={"apikey": key, "Authorization": f"Bearer {key}", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def list_auth_users(url, key):
    users = []
    page = 1
    while True:
        batch = _get(url, key, f"/auth/v1/admin/users?per_page=200&page={page}")
        us = batch.get("users", batch) if isinstance(batch, dict) else batch
        if not us: break
        for u in us:
            users.append({"id": u.get("id"), "email": (u.get("email") or "").lower(),
                          "created_at": u.get("created_at"),
                          "name": (u.get("user_metadata") or {}).get("full_name", "")})
        if len(us) < 200: break
        page += 1
    return users

def boats_by_host(url, key):
    rows = _get(url, key, "/rest/v1/boats?select=host_id,status")
    from collections import defaultdict
    d = defaultdict(list)
    for b in rows: d[b["host_id"]].append(b.get("status"))
    return d

def find_unlisted(url, key):
    users = list_auth_users(url, key)
    hb = boats_by_host(url, key)
    out = []
    for u in users:
        statuses = hb.get(u["id"], [])
        has_active = any(s == "active" for s in statuses)
        if not has_active and u["email"]:
            out.append({**u, "boats": len(statuses), "drafts": sum(1 for s in statuses if s == "draft")})
    return out, len(users), len(hb)

SUBJECT = "You're one step from your first BoatHire24 booking"
def body(u):
    nm = (u.get("name") or "").split()[0] if u.get("name") else ""
    nc = f" {nm}" if nm else ""
    started = "You started a listing but haven't published it yet" if u.get("drafts") else "You created your account but haven't added a boat yet"
    return f"""Hi{nc},

{started} — so renters can't find you on BoatHire24 yet.

Want us to finish it for you? Reply with a link to your boat (or your website) and our team will build the full listing — photos, pricing, calendar — and get it live for you. Free, and you only pay a small commission when you actually get a booking.

Or finish it yourself in ~5 minutes here:
https://boathire24.com/host/listings/new

Anything blocking you? Just reply and I'll help.

Best,
Mardo Soo
CEO, BoatHire24
WhatsApp: +372 5815 5779
info@boathire24.com"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--send", action="store_true")
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--to-self", action="store_true")
    ap.add_argument("--sleep", type=float, default=2.0)
    args = ap.parse_args()
    url, key = _env()
    if not url or not key:
        print("ERROR: Supabase URL/SERVICE_ROLE_KEY not found in .env.local"); return
    unlisted, total_users, total_hosts_with_boats = find_unlisted(url, key)
    print(f"Total signed-up users: {total_users}")
    print(f"Users with >=1 boat row: {total_hosts_with_boats}")
    print(f"SIGNED UP but NO ACTIVE listing: {len(unlisted)}  "
          f"(of those, {sum(1 for u in unlisted if u['drafts'])} have an unfinished draft)")
    if args.audit:
        for u in unlisted[:10]:
            print(f"  - {u['email']:<40} boats={u['boats']} drafts={u['drafts']} joined={u['created_at'][:10] if u['created_at'] else '?'}")
        return
    if args.dry_run:
        if unlisted:
            print(f"\n--- sample email ---\nSubject: {SUBJECT}\n{body(unlisted[0])}")
        return
    if args.send:
        con = store.connect(); outreach.ensure_outreach_table(con)
        supp = outreach.hard_suppressed_emails(con)
        sent = 0
        for u in unlisted[:args.limit]:
            if u["email"] in supp: continue
            target = "info@boathire24.com" if args.to_self else u["email"]
            rid, err = outreach.resend_send(target, SUBJECT, body(u),
                                            html=outreach._text_to_html(body(u), "boathire24.com"))
            tag = "activation" if rid else "activation-failed"
            con.execute("INSERT OR REPLACE INTO outreach(domain,email,sent_at,lang,subject,resend_id,status) VALUES(?,?,?,?,?,?,?)",
                        (f"signup:{u['id'][:8]}", u["email"], store.now(), "en", SUBJECT, rid, "sent" if rid else "failed")); con.commit()
            sent += 1 if rid else 0
            print(f"  {'✓' if rid else '✗'} {target}  {err or rid}")
            time.sleep(args.sleep)
        print(f"\nActivation emails sent: {sent}")

if __name__ == "__main__":
    main()
