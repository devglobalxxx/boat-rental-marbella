#!/usr/bin/env python3
"""LiveJournal publisher for BoatHire24 backlink posts.

Uses LiveJournal's XML-RPC API (https://www.livejournal.com/interface/xmlrpc)
with challenge-response auth, so the account password is never sent over the
wire (only md5(challenge + md5(password))).

Credentials live in config/livejournal_account.json (gitignored), which YOU
create:  {"username": "yourljname", "password": "yourljpassword"}
Posts are drawn from the backlog content/livejournal/NNN-slug.json and tracked
in config/livejournal_state.json so the 3/day drip never repeats a post.

Usage:
  python3 scripts/livejournal_post.py check               # verify login works
  python3 scripts/livejournal_post.py post-next [N]        # post next N (default 3)
  python3 scripts/livejournal_post.py status
"""
import hashlib
import json
import pathlib
import re
import sys
import xmlrpc.client
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
BACKLOG = ROOT / "content" / "livejournal"
ACCT = ROOT / "config" / "livejournal_account.json"
STATE = ROOT / "config" / "livejournal_state.json"
ENDPOINT = "https://www.livejournal.com/interface/xmlrpc"


def _md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def _creds():
    if not ACCT.exists():
        sys.exit(f"Missing {ACCT}. Create it with "
                 '{"username":"...","password":"..."} (gitignored).')
    c = json.loads(ACCT.read_text())
    if not c.get("username") or not c.get("password"):
        sys.exit(f"{ACCT} must contain username and password.")
    return c["username"], c["password"]


def _server():
    return xmlrpc.client.ServerProxy(ENDPOINT)


def _auth(server, password):
    """Return the auth fields for a challenge-response call."""
    ch = server.LJ.XMLRPC.getchallenge()["challenge"]
    return {
        "auth_method": "challenge",
        "auth_challenge": ch,
        "auth_response": _md5(ch + _md5(password)),
    }


def check():
    user, pw = _creds()
    s = _server()
    res = s.LJ.XMLRPC.login({"username": user, "ver": 1, **_auth(s, pw)})
    name = res.get("fullname", user)
    print(f"LOGIN OK as {user} ({name}). Usejournals: {res.get('usejournals', [])}")


def _minify_html(html: str) -> str:
    # collapse whitespace between tags so LiveJournal renders the HTML cleanly
    html = re.sub(r">\s+<", "><", html.strip())
    return re.sub(r"\s+", " ", html)


def post_one(path: pathlib.Path) -> str:
    user, pw = _creds()
    art = json.loads(path.read_text())
    body = _minify_html(art["html"])
    now = datetime.now()
    s = _server()
    req = {
        "username": user,
        "ver": 1,
        "lineendings": "unix",
        "subject": art["title"][:255],
        "event": body,
        "security": "public",
        "year": now.year, "mon": now.month, "day": now.day,
        "hour": now.hour, "min": now.minute,
        "props": {"opt_preformatted": True, "taglist": art.get("tags", "")},
        **_auth(s, pw),
    }
    res = s.LJ.XMLRPC.postevent(req)
    return res.get("url") or f"itemid:{res.get('itemid')}"


def load_state():
    return json.loads(STATE.read_text()) if STATE.exists() else {"published": {}}


def save_state(st):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st, indent=1, ensure_ascii=False))


def post_next(n: int):
    st = load_state()
    done = set(st["published"])
    pending = sorted(p for p in BACKLOG.glob("*.json") if p.stem not in done)
    if not pending:
        print("Backlog empty or all posted. Generate more into content/livejournal/.")
        return
    for p in pending[:n]:
        try:
            url = post_one(p)
            st["published"][p.stem] = {
                "url": url,
                "title": json.loads(p.read_text())["title"],
                "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            save_state(st)
            print(f"POSTED {p.stem} -> {url}")
        except Exception as e:  # noqa: BLE001
            print(f"FAILED {p.stem}: {e}", file=sys.stderr)
    rem = len([p for p in BACKLOG.glob('*.json') if p.stem not in st['published']])
    print(f"\nposted; {rem} left in backlog")


def status():
    st = load_state()
    done = st["published"]
    total = len(list(BACKLOG.glob("*.json"))) if BACKLOG.exists() else 0
    print(f"LiveJournal: {len(done)} posted / {total} in backlog / {total - len(done)} pending")
    for k, v in list(done.items())[-10:]:
        print(f"  {v.get('at','')[:10]}  {v['url']}  {v.get('title','')[:50]}")


def main():
    a = sys.argv[1:]
    if not a:
        status(); return
    if a[0] == "check":
        check()
    elif a[0] == "post-next":
        post_next(int(a[1]) if len(a) > 1 else 3)
    elif a[0] == "status":
        status()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
