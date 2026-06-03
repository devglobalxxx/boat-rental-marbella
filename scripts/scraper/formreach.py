"""Contact-form outreach — submit the BoatHire24 pitch through operators' own
website contact forms. Lands in their PRIMARY inbox (not spam) and reaches
operators we have no email for.

Best-effort, polite, requests-based:
  • one submission per domain, deduped in a form_outreach table
  • detects + SKIPS CAPTCHA-protected forms (recaptcha / hcaptcha / turnstile)
  • heuristically maps name / email / subject / message / phone fields
  • localized pitch (reuses outreach templates) with the working list-your-boat URL
  • skips JS-only / AJAX forms it can't post to (logs them for browser follow-up)

Usage:
  python3 -m scripts.scraper.formreach --dry-run --limit 5     # preview targets+fields
  python3 -m scripts.scraper.formreach --limit 50              # submit 50
  python3 -m scripts.scraper.formreach --all --sleep 4
  python3 -m scripts.scraper.formreach --stats
"""
from __future__ import annotations
import argparse, json, re, time, random, urllib.parse
from bs4 import BeautifulSoup
from . import store, http as http_mod, outreach

SENDER_NAME  = "Andra Kiirkivi"
SENDER_EMAIL = "info@boathire24.com"
SENDER_PHONE = "+34 600 000 000"  # set to a real reachable number before live use

CAPTCHA_MARKERS = ("recaptcha", "g-recaptcha", "hcaptcha", "h-captcha",
                   "cf-turnstile", "turnstile", "captcha")

def ensure_schema(con):
    con.executescript("""
    CREATE TABLE IF NOT EXISTS form_outreach (
        domain       TEXT PRIMARY KEY,
        form_url     TEXT,
        submitted_at TEXT,
        status       TEXT,         -- submitted / captcha / no_form / js_form / failed / skipped
        http_status  INTEGER,
        fields_used  TEXT,
        error        TEXT
    );
    """)
    con.commit()

def already_done(con, domain):
    r = con.execute("SELECT status FROM form_outreach WHERE domain=?", (domain,)).fetchone()
    return r and r[0] in ("submitted", "captcha")  # don't retry success or captcha

def record(con, domain, form_url, status, http_status=None, fields=None, error=""):
    con.execute(
        "INSERT OR REPLACE INTO form_outreach(domain,form_url,submitted_at,status,http_status,fields_used,error) VALUES(?,?,?,?,?,?,?)",
        (domain, form_url, store.now(), status, http_status, json.dumps(fields or {}), error),
    )
    con.commit()

# ── field-mapping heuristics ────────────────────────────────────────────────
def classify_field(name, ftype, placeholder, label):
    blob = " ".join(x for x in (name, placeholder, label) if x).lower()
    if ftype in ("hidden", "submit", "button", "file"): return None
    if ftype == "email" or re.search(r"e?-?mail|correo|courriel", blob): return "email"
    if re.search(r"phone|tel|tél|teléfono|whats", blob): return "phone"
    if re.search(r"subject|asunto|objet|oggetto", blob): return "subject"
    if re.search(r"\b(name|nom|nombre|nome)\b|full.?name|your.?name", blob): return "name"
    if ftype == "textarea" or re.search(r"message|comment|mensaje|enquir|inquir|tu mensaje|votre message|how can we help", blob): return "message"
    return None

def build_message(rec, lang):
    # reuse the outreach plain-text body (concierge version) with working URL,
    # but STRIP the email-only "— You're receiving this… reply STOP" footer —
    # it makes no sense submitted through a web contact form.
    _, _, body = outreach.render(
        {"domain": rec["domain"], "company": rec.get("company",""), "city": rec.get("city",""), "country": rec.get("country","")},
        force_lang=lang,
    )
    lines = []
    for ln in body.splitlines():
        if ln.startswith("— ") or ln.startswith("-- "):
            break
        lines.append(ln)
    return "\n".join(lines).rstrip() + "\n"

def submit_form(con, rec):
    domain = rec["domain"]; url = rec["form_url"]
    if not url:
        record(con, domain, url, "no_form"); return "no_form"
    r = http_mod.get(url)
    if not r or r.status_code != 200:
        record(con, domain, url, "failed", http_status=(r.status_code if r else None), error="page fetch failed"); return "failed"
    html = r.text
    if any(m in html.lower() for m in CAPTCHA_MARKERS):
        record(con, domain, url, "captcha"); return "captcha"
    soup = BeautifulSoup(html, "lxml")
    # pick the form most likely to be a contact form (has a textarea or email input)
    forms = soup.find_all("form")
    target = None
    for f in forms:
        if f.find("textarea") or f.find("input", {"type": "email"}):
            target = f; break
    if not target and forms:
        target = forms[0]
    if not target:
        record(con, domain, url, "no_form"); return "no_form"

    action = target.get("action") or url
    action = urllib.parse.urljoin(url, action)
    method = (target.get("method") or "post").lower()

    lang = outreach.pick_lang(rec.get("country"))
    msg = build_message(rec, lang)
    subject = f"Add your {rec.get('city') or 'boat'} boats to BoatHire24"

    data = {}; mapped = {}
    for el in target.find_all(["input", "textarea", "select"]):
        nm = el.get("name")
        if not nm: continue
        ftype = (el.get("type") or el.name).lower()
        if ftype in ("submit", "button"): continue
        if ftype == "hidden":
            data[nm] = el.get("value", ""); continue
        label = ""
        if el.get("id"):
            lab = soup.find("label", {"for": el.get("id")})
            if lab: label = lab.get_text(" ", strip=True)
        role = classify_field(nm, ftype, el.get("placeholder",""), label)
        if role == "email": data[nm] = SENDER_EMAIL; mapped["email"] = nm
        elif role == "name": data[nm] = SENDER_NAME; mapped["name"] = nm
        elif role == "phone": data[nm] = SENDER_PHONE; mapped["phone"] = nm
        elif role == "subject": data[nm] = subject; mapped["subject"] = nm
        elif role == "message": data[nm] = msg; mapped["message"] = nm
        elif el.name == "select":
            opt = el.find("option", value=True)
            if opt: data[nm] = opt.get("value")
        else:
            data[nm] = el.get("value", "")

    # require at least an email + message field, else it's probably a JS form
    if "message" not in mapped or "email" not in mapped:
        record(con, domain, url, "js_form", fields=mapped, error="no mappable email/message field"); return "js_form"

    headers = {"Referer": url, "User-Agent": random.choice(http_mod.UAS)}
    try:
        import requests
        if method == "get":
            resp = requests.get(action, params=data, headers=headers, timeout=20)
        else:
            resp = requests.post(action, data=data, headers=headers, timeout=20)
        ok = resp.status_code in (200, 201, 302, 303)
        record(con, domain, url, "submitted" if ok else "failed",
               http_status=resp.status_code, fields=mapped,
               error="" if ok else f"HTTP {resp.status_code}")
        return "submitted" if ok else "failed"
    except Exception as e:
        record(con, domain, url, "failed", fields=mapped, error=f"{type(e).__name__}: {e}")
        return "failed"

def candidates(con, limit=None, shard=None, shards=None):
    cur = con.execute("""
        SELECT domain, company, city, country, contact_form
        FROM leads WHERE contact_form IS NOT NULL AND contact_form != ''
        ORDER BY confidence DESC
    """)
    out = []
    for domain, company, city, country, form in cur:
        if already_done(con, domain): continue
        if domain in outreach.COMPETITOR_DOMAINS: continue
        if any(domain.endswith("." + c) for c in outreach.COMPETITOR_DOMAINS): continue
        if shards and (hash(domain) % shards) != shard: continue
        out.append({"domain": domain, "company": company or "", "city": city or "",
                    "country": country or "", "form_url": form})
        if limit and len(out) >= limit: break
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--sleep", type=float, default=4.0)
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--shard", type=int)
    ap.add_argument("--shards", type=int)
    args = ap.parse_args()
    con = store.connect(); ensure_schema(con)

    if args.stats:
        print("form_outreach status:")
        for s, n in con.execute("SELECT status, COUNT(*) FROM form_outreach GROUP BY status ORDER BY COUNT(*) DESC"):
            print(f"  {s:<12} {n}")
        return

    recs = candidates(con, limit=None if args.all else args.limit,
                      shard=args.shard, shards=args.shards)
    print(f"Form candidates: {len(recs)}" + (f" (shard {args.shard}/{args.shards})" if args.shards else ""))
    if args.dry_run:
        for r in recs[:5]:
            lang = outreach.pick_lang(r["country"])
            print(f"\n=== {r['domain']}  ({r['city']}, {r['country']}, {lang}) ===\n  form: {r['form_url']}")
        print(f"\n(dry-run; first 5 of {len(recs)} — run without --dry-run to submit)")
        return

    from collections import Counter
    res = Counter()
    for i, r in enumerate(recs, 1):
        status = submit_form(con, r)
        res[status] += 1
        print(f"  [{i:>4}/{len(recs)}] {r['domain']:<38} → {status}", flush=True)
        time.sleep(args.sleep + random.random())
    print(f"\nDone. {dict(res)}")

if __name__ == "__main__":
    main()
