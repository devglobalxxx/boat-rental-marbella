#!/usr/bin/env python3
"""graph.org publisher (Telegraph's sister domain, same API backend).

Keeps its OWN backlog (content/graph_org/) and state (config/graph_org_state.json)
and reports graph.org URLs. Content is UNIQUE from the telegra.ph backlog to
avoid duplicate content. Backlink drip to https://boathire24.com.

Uses its OWN Telegraph account (.graphorg_token, author BoatHire24) — never the
telegraph_publish.py account, which is the Boat Rental Marbella identity. The two
properties' link networks must stay separated (SEO audit 2026-07).

Usage:
  python3 scripts/graph_org_publish.py publish-next [N]
  python3 scripts/graph_org_publish.py status
"""
import json
import pathlib
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent
BACKLOG = ROOT / "content" / "graph_org"
STATE = ROOT / "config" / "graph_org_state.json"
TOKEN_FILE = ROOT / ".graphorg_token"
AUTHOR_NAME = "BoatHire24"
AUTHOR_URL = "https://boathire24.com"

# Telegraph node whitelist; heading levels above h3 don't exist there.
_TAG_MAP = {"h1": "h3", "h2": "h3", "h3": "h3", "h4": "h4", "h5": "h4", "h6": "h4"}
_ALLOWED = {"a", "aside", "b", "blockquote", "br", "code", "em", "figcaption",
            "figure", "h3", "h4", "hr", "i", "img", "li", "ol", "p", "pre",
            "s", "strong", "u", "ul"}
_VOID = {"br", "hr", "img"}


class _NodeBuilder(HTMLParser):
    """article HTML -> Telegraph DOM node array (only href/src attrs survive)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root: list = []
        self.stack: list = []

    def _append(self, node):
        (self.stack[-1]["children"] if self.stack else self.root).append(node)

    def handle_starttag(self, tag, attrs):
        tag = _TAG_MAP.get(tag, tag)
        if tag not in _ALLOWED:
            return
        node = {"tag": tag}
        keep = {k: v for k, v in attrs if k in ("href", "src") and v}
        if keep:
            node["attrs"] = keep
        if tag in _VOID:
            self._append(node)
            return
        node["children"] = []
        self._append(node)
        self.stack.append(node)

    def handle_endtag(self, tag):
        tag = _TAG_MAP.get(tag, tag)
        if self.stack and self.stack[-1]["tag"] == tag:
            node = self.stack.pop()
            if not node["children"]:
                node.pop("children")

    def handle_data(self, data):
        if data.strip() or (self.stack and data):
            self._append(data)


def html_to_nodes(html: str) -> list:
    b = _NodeBuilder()
    b.feed(html)
    # top-level bare strings must live inside a block element
    return [n if isinstance(n, dict) else {"tag": "p", "children": [n]} for n in b.root]


def _token() -> str:
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    import requests
    r = requests.post("https://api.telegra.ph/createAccount", data={
        "short_name": AUTHOR_NAME,
        "author_name": AUTHOR_NAME,
        "author_url": AUTHOR_URL,
    }, timeout=60).json()
    if not r.get("ok"):
        raise RuntimeError(f"createAccount failed: {r}")
    tok = r["result"]["access_token"]
    TOKEN_FILE.write_text(tok)
    return tok


def _publish(token: str, art: dict) -> str:
    import requests
    nodes = html_to_nodes(art["html"])
    if not nodes:
        raise RuntimeError("article html produced no Telegraph nodes")
    r = requests.post("https://api.telegra.ph/createPage", data={
        "access_token": token,
        "title": art["title"][:256],
        "author_name": art.get("author_name", AUTHOR_NAME),
        "author_url": art.get("author_url", AUTHOR_URL),
        "content": json.dumps(nodes),
        "return_content": "false",
    }, timeout=60).json()
    if not r.get("ok"):
        raise RuntimeError(f"createPage failed: {r}")
    return r["result"]["url"].replace("https://telegra.ph/", "https://graph.org/")


def _state():
    return json.loads(STATE.read_text()) if STATE.exists() else {"published": {}}


def _save(s):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(s, indent=1, ensure_ascii=False))


def publish_next(n: int):
    token = _token()
    st = _state()
    done = set(st["published"])
    pending = sorted(p for p in BACKLOG.glob("*.json") if p.stem not in done)
    if not pending:
        print("graph.org backlog empty/all published. Add articles to content/graph_org/.")
        return
    for p in pending[:n]:
        try:
            art = json.loads(p.read_text())
            url = _publish(token, art)
            st["published"][p.stem] = {
                "url": url,
                "title": art["title"],
                "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            _save(st)
            print(f"PUBLISHED {p.stem} -> {url}")
        except Exception as e:  # noqa: BLE001
            print(f"FAILED {p.stem}: {e}", file=sys.stderr)
    rem = len([p for p in BACKLOG.glob('*.json') if p.stem not in st['published']])
    print(f"\npublished; {rem} left in backlog")


def status():
    st = _state()
    total = len(list(BACKLOG.glob("*.json"))) if BACKLOG.exists() else 0
    print(f"graph.org: {len(st['published'])} published / {total} in backlog / {total - len(st['published'])} pending")
    for k, v in list(st["published"].items())[-10:]:
        print(f"  {v.get('at','')[:10]}  {v['url']}  {v.get('title','')[:50]}")


def main():
    a = sys.argv[1:]
    if not a:
        status(); return
    if a[0] == "publish-next":
        publish_next(int(a[1]) if len(a) > 1 else 3)
    elif a[0] == "status":
        status()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
