#!/usr/bin/env python3
"""Telegra.ph publisher for BoatHire24 backlink articles.

Telegra.ph exposes a free public HTTP API (https://telegra.ph/api) so we can
publish without any browser or login. We keep a backlog of ready-to-publish
article JSONs in content/telegraph/ and drip 3/day to telegra.ph, each carrying
contextual backlinks to https://boathire24.com.

Account token is created once and cached in config/telegraph_account.json.
Published pages are tracked in config/telegraph_state.json so the drip never
repeats an article.

Usage:
  python3 scripts/telegraph_publish.py publish-next [N]   # publish next N from backlog (default 3)
  python3 scripts/telegraph_publish.py publish <file.json>
  python3 scripts/telegraph_publish.py status
"""
import json
import pathlib
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent
BACKLOG = ROOT / "content" / "telegraph"
ACCT = ROOT / "config" / "telegraph_account.json"
STATE = ROOT / "config" / "telegraph_state.json"
API = "https://api.telegra.ph/"

# Tags telegra.ph accepts. Anything else is unwrapped (children kept).
ALLOWED = {"a", "aside", "b", "blockquote", "br", "code", "em", "figcaption",
           "figure", "h3", "h4", "hr", "i", "img", "li", "ol", "p", "pre",
           "s", "strong", "u", "ul", "video"}
# Map common heading/format tags onto telegra.ph's supported set.
REMAP = {"h1": "h3", "h2": "h3", "h5": "h4", "h6": "h4", "div": "p", "span": None}


def api(method, **params):
    payload = {k: (json.dumps(v) if isinstance(v, (list, dict)) else v)
               for k, v in params.items()}
    data = urllib.parse.urlencode(payload).encode()
    req = urllib.request.Request(API + method, data=data)
    res = json.load(urllib.request.urlopen(req, timeout=45))
    if not res.get("ok"):
        raise RuntimeError(f"telegraph {method} failed: {res.get('error')}")
    return res["result"]


def get_token() -> str:
    if ACCT.exists():
        return json.loads(ACCT.read_text())["access_token"]
    acct = api("createAccount", short_name="BoatHire24",
               author_name="BoatHire24", author_url="https://boathire24.com")
    ACCT.parent.mkdir(parents=True, exist_ok=True)
    ACCT.write_text(json.dumps(acct, indent=1))
    print(f"created telegraph account -> {ACCT}")
    return acct["access_token"]


class _Nodes(HTMLParser):
    """Convert a subset of HTML into telegra.ph Node array."""

    def __init__(self):
        super().__init__()
        self.root = []
        self.stack = [self.root]

    def _tag(self, tag):
        tag = REMAP.get(tag, tag)
        return tag

    def handle_starttag(self, tag, attrs):
        tag = self._tag(tag)
        if tag is None:  # span -> unwrap
            return
        if tag not in ALLOWED:
            return
        node = {"tag": tag}
        a = {}
        for k, v in attrs:
            if k in ("href", "src"):
                a[k] = v
        if a:
            node["attrs"] = a
        if tag not in ("br", "hr", "img"):
            node["children"] = []
        self.stack[-1].append(node)
        if "children" in node:
            self.stack.append(node["children"])

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        tag = self._tag(tag)
        if tag is None or tag not in ALLOWED or tag in ("br", "hr", "img"):
            return
        if len(self.stack) > 1:
            self.stack.pop()

    def handle_data(self, data):
        text = data.replace("\n", " ")
        if text.strip() == "" and not text.strip(" "):
            # keep single spaces between inline elements, drop pure-whitespace blocks
            if text == "" or text.isspace() and len(text) > 1:
                return
        if text:
            self.stack[-1].append(text)


def html_to_nodes(html: str) -> list:
    p = _Nodes()
    p.feed(html)
    p.close()
    return p.root


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"published": {}}


def save_state(s: dict):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(s, indent=1, ensure_ascii=False))


def publish_article(path: pathlib.Path, token: str) -> str:
    art = json.loads(path.read_text())
    nodes = art.get("nodes") or html_to_nodes(art["html"])
    if not nodes:
        raise RuntimeError(f"{path.name}: empty content")
    page = api("createPage", access_token=token,
               title=art["title"][:256],
               author_name=art.get("author_name", "BoatHire24"),
               author_url=art.get("author_url", "https://boathire24.com"),
               content=nodes, return_content="false")
    return page["url"]


def cmd_publish_next(n: int):
    token = get_token()
    state = load_state()
    done = set(state["published"])
    pending = sorted(p for p in BACKLOG.glob("*.json") if p.stem not in done)
    if not pending:
        print("Backlog empty or all published. Generate more articles into content/telegraph/.")
        return
    batch = pending[:n]
    for p in batch:
        try:
            url = publish_article(p, token)
            state["published"][p.stem] = {
                "url": url,
                "title": json.loads(p.read_text())["title"],
                "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            save_state(state)
            print(f"PUBLISHED {p.stem} -> {url}")
        except Exception as e:  # noqa: BLE001
            print(f"FAILED {p.stem}: {e}", file=sys.stderr)
    rem = len([p for p in BACKLOG.glob('*.json') if p.stem not in state['published']])
    print(f"\n{len(batch)} published; {rem} left in backlog")


def cmd_status():
    state = load_state()
    done = state["published"]
    total = len(list(BACKLOG.glob("*.json"))) if BACKLOG.exists() else 0
    print(f"Telegraph: {len(done)} published / {total} in backlog / {total - len(done)} pending")
    for k, v in list(done.items())[-10:]:
        print(f"  {v.get('at','')[:10]}  {v['url']}  {v.get('title','')[:50]}")


def main():
    args = sys.argv[1:]
    if not args:
        cmd_status(); return
    if args[0] == "publish-next":
        cmd_publish_next(int(args[1]) if len(args) > 1 else 3)
    elif args[0] == "publish":
        print(publish_article(pathlib.Path(args[1]), get_token()))
    elif args[0] == "status":
        cmd_status()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
