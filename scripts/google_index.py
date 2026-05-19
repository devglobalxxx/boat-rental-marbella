#!/usr/bin/env python3
"""Submit URLs to Google Indexing API.

Officially Google Indexing API is for JobPosting / BroadcastEvent, but the
endpoint accepts URL_UPDATED for any property where the calling service-account
is a verified Owner in Google Search Console. Many SEOs use this to nudge
re-crawls for recently changed pages.

Setup (one-time):
  1. Create a GCP project + enable "Indexing API".
  2. Create a service account, download JSON key to
     ~/.boatrentalmarbella-gsc.json  (or set GSC_SA_PATH env var).
  3. In Google Search Console, add the service-account email as an "Owner"
     of https://boatrentalinmarbella.com/.
  4. Sitemap submitted once in GSC dashboard.

Usage:
    python3 scripts/google_index.py                 # all sitemap URLs
    python3 scripts/google_index.py --changed       # URLs whose HTML changed last commit

Fails gracefully (logs + exit 0) if creds are missing.
"""
from __future__ import annotations
import argparse, json, os, pathlib, re, subprocess, sys, time
import urllib.request, urllib.error

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "site"
CONFIG = json.loads((ROOT / "config" / "keyword_map.json").read_text())
BASE_URL = CONFIG["site"]["base_url"].rstrip("/")

SA_PATH = pathlib.Path(os.environ.get(
    "GSC_SA_PATH",
    str(pathlib.Path.home() / ".boatrentalmarbella-gsc.json")
))

def all_sitemap_urls():
    sm = SITE_DIR / "sitemap.xml"
    return re.findall(r"<loc>([^<]+)</loc>", sm.read_text())

def changed_urls():
    try:
        out = subprocess.check_output(
            ["git", "diff", "HEAD~1", "HEAD", "--name-only"],
            cwd=ROOT, text=True
        )
    except subprocess.CalledProcessError:
        return all_sitemap_urls()
    urls = []
    for line in out.splitlines():
        if line.startswith("site/") and line.endswith("index.html"):
            rel = line[len("site/"):-len("index.html")]
            urls.append(f"{BASE_URL}/{rel}")
    return urls or all_sitemap_urls()

def get_token():
    """Exchange service-account JWT for OAuth access token (no google-auth dep)."""
    try:
        import jwt  # PyJWT
    except ImportError:
        print("PyJWT not installed — pip install PyJWT cryptography  (Google API hook skipped)")
        return None
    sa = json.loads(SA_PATH.read_text())
    now = int(time.time())
    claim = {
        "iss": sa["client_email"],
        "scope": "https://www.googleapis.com/auth/indexing",
        "aud": "https://oauth2.googleapis.com/token",
        "iat": now,
        "exp": now + 3600,
    }
    signed = jwt.encode(claim, sa["private_key"], algorithm="RS256")
    body = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": signed,
    }).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())["access_token"]

def publish_url(url, token):
    body = json.dumps({"url": url, "type": "URL_UPDATED"}).encode()
    req = urllib.request.Request(
        "https://indexing.googleapis.com/v3/urlNotifications:publish",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.read().decode()[:200]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--changed", action="store_true")
    ap.add_argument("--limit", type=int, default=20, help="Google Indexing API quota is 200/day; cap submissions per run")
    args = ap.parse_args()

    if not SA_PATH.exists():
        print(f"Google Indexing API: no service-account at {SA_PATH} — skipped (set up later; IndexNow still ran).")
        return 0
    token = get_token()
    if not token:
        return 0

    urls = changed_urls() if args.changed else all_sitemap_urls()
    urls = urls[:args.limit]
    if not urls:
        print("no urls")
        return 0
    print(f"Google Indexing API: submitting {len(urls)} URL(s)")
    ok = 0
    for u in urls:
        code, body = publish_url(u, token)
        marker = "✓" if 200 <= code < 300 else "✗"
        print(f"  {marker} {code}  {u}")
        if 200 <= code < 300:
            ok += 1
    print(f"Google Indexing API: {ok}/{len(urls)} accepted")
    return 0

if __name__ == "__main__":
    sys.exit(main())
