#!/usr/bin/env python3
"""Publish landing pages from content/*.json to the Boat Rental In Marbella
Blogger blog (id 5347820828408620730) as Blogger PAGES — 2 per day by default.

Each page renders body_html + FAQ + a canonical backlink to the live page on
boatrentalinmarbella.com. Throttled + aborts cleanly on a 403/quota block.

Setup (one-time):
  GOOGLE_CREDENTIALS in .env -> OAuth Desktop client_secret JSON
  python3 scripts/post_blogger_pages.py --login        # browser, log in as blog owner
  python3 scripts/post_blogger_pages.py --list-blogs   # confirm the id

Usage:
  python3 scripts/post_blogger_pages.py --limit 2
"""
from __future__ import annotations
import argparse, datetime, json, os, pathlib, re, sys, time

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
POSTED = ROOT / "config" / "blogger_pages_posted.json"
TOKEN = pathlib.Path.home() / ".boatrentalmarbella-blogger-token.json"
LOG_DIR = ROOT / "logs"; LOG_DIR.mkdir(exist_ok=True)
LOG = LOG_DIR / "post_blogger_pages.log"
BASE = "https://boatrentalinmarbella.com"
SCOPES = ["https://www.googleapis.com/auth/blogger"]


def log(m: str):
    line = f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {m}"
    print(line, flush=True)
    with LOG.open("a") as f:
        f.write(line + "\n")


def load_env():
    for p in (ROOT / ".env", ROOT / ".env.local"):
        if not p.exists():
            continue
        for line in p.read_text().splitlines():
            for k in ("BLOGGER_BLOG_ID", "GOOGLE_CREDENTIALS"):
                if line.startswith(k + "=") and not os.environ.get(k):
                    os.environ[k] = line.split("=", 1)[1].strip().strip('"').strip("'")


def get_credentials(interactive: bool):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    creds = None
    if TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif interactive:
            from google_auth_oauthlib.flow import InstalledAppFlow
            cp = os.environ.get("GOOGLE_CREDENTIALS")
            if not cp or not pathlib.Path(cp).exists():
                sys.exit(f"ERROR: GOOGLE_CREDENTIALS not found: {cp}")
            flow = InstalledAppFlow.from_client_secrets_file(cp, SCOPES)
            creds = flow.run_local_server(port=0)
        else:
            return None
        TOKEN.write_text(creds.to_json())
    return creds


def blogger(creds):
    from googleapiclient.discovery import build
    return build("blogger", "v3", credentials=creds, cache_discovery=False)


def render(item: dict) -> str:
    page, data = item["page"], item["data"]
    slug = page["slug"]
    parts = []
    if data.get("hero_img"):
        parts.append(f'<p><img src="{data["hero_img"]}" alt="{data.get("hero_alt", page["title"])}" '
                     f'style="max-width:100%;height:auto" /></p>')
    parts.append(data.get("body_html", ""))
    for f in (data.get("faq") or []):
        if "<h2>Frequently" not in "".join(parts):
            parts.append("<h2>Frequently asked questions</h2>")
        parts.append(f"<h3>{f.get('q', '')}</h3><p>{f.get('a', '')}</p>")
    parts.append(f'<p><em>Originally published on '
                 f'<a href="{BASE}/{slug}/" rel="canonical">Boat Rental Marbella</a>. '
                 f'Compare boats at <a href="{BASE}/">boatrentalinmarbella.com</a>.</em></p>')
    html = "\n".join(parts)
    return re.sub(r'href="/(?!/)', f'href="{BASE}/', html)


def load_landings() -> list[dict]:
    out = []
    for fp in sorted(CONTENT.glob("*.json")):
        try:
            d = json.loads(fp.read_text())
        except Exception:
            continue
        if d.get("kind") == "blog" or "page" not in d:
            continue
        out.append(d)
    return out


def load_posted() -> set:
    try:
        return set(json.loads(POSTED.read_text()))
    except Exception:
        return set()


def save_posted(s: set):
    POSTED.write_text(json.dumps(sorted(s), indent=2) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--login", action="store_true")
    ap.add_argument("--list-blogs", action="store_true")
    ap.add_argument("--limit", type=int, default=2)
    args = ap.parse_args()
    load_env()

    if args.login:
        get_credentials(interactive=True)
        log("login OK — token saved")
        return 0

    creds = get_credentials(interactive=False)
    if not creds:
        log("no credentials — run --login. Skipped.")
        return 0
    svc = blogger(creds)

    if args.list_blogs:
        for b in svc.blogs().listByUser(userId="self").execute().get("items", []):
            log(f"  {b['id']}  {b.get('name')}  {b.get('url')}")
        return 0

    blog_id = os.environ.get("BLOGGER_BLOG_ID", "").strip()
    if not blog_id:
        log("BLOGGER_BLOG_ID not set. Skipped.")
        return 0

    posted = load_posted()
    todo = [d for d in load_landings() if d["page"]["slug"] not in posted][:args.limit]
    if not todo:
        log("nothing new to publish.")
        return 0

    log(f"publishing {len(todo)} page(s) to blog {blog_id}")
    ok = 0
    for d in todo:
        slug = d["page"]["slug"]
        body = {"kind": "blogger#page", "title": d["page"]["title"], "content": render(d)}
        try:
            res = svc.pages().insert(blogId=blog_id, body=body, isDraft=False).execute()
            posted.add(slug); save_posted(posted); ok += 1
            log(f"  ✓ {res.get('url')}")
            time.sleep(6)
        except Exception as e:
            msg = str(e)
            if "403" in msg or "forbidden" in msg.lower() or "permission" in msg.lower():
                log(f"  WRITE-BLOCKED (quota): stopping. {msg[:120]}")
                break
            log(f"  ✗ {slug}: {type(e).__name__}: {msg[:120]}")
    log(f"published {ok}/{len(todo)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
