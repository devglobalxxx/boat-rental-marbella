#!/usr/bin/env python3
"""rentry.co publisher for BoatHire24 backlink pages.

rentry.co is a markdown pastebin with a simple API (CSRF token + POST). We
convert the article HTML to Markdown and publish, keeping backlinks to
https://boathire24.com. Own backlog (content/rentry/) and state
(config/rentry_state.json, which also stores each paste's edit_code).

Usage:
  python3 scripts/rentry_post.py publish-next [N]
  python3 scripts/rentry_post.py status
"""
import http.cookiejar
import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent
BACKLOG = ROOT / "content" / "rentry"
STATE = ROOT / "config" / "rentry_state.json"
BASE = "https://rentry.co"


class _ToMarkdown(HTMLParser):
    """Minimal HTML -> Markdown for the tag subset our articles use."""

    def __init__(self):
        super().__init__()
        self.out = []
        self.list_stack = []      # 'ul' or 'ol'
        self.ol_counter = []
        self.href = None
        self.link_text = []
        self.in_link = False

    def _emit(self, s):
        (self.link_text if self.in_link else self.out).append(s)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("p",):
            self.out.append("\n\n")
        elif tag == "h3":
            self.out.append("\n\n## ")
        elif tag == "h4":
            self.out.append("\n\n### ")
        elif tag in ("strong", "b"):
            self._emit("**")
        elif tag in ("em", "i"):
            self._emit("*")
        elif tag == "blockquote":
            self.out.append("\n\n> ")
        elif tag == "ul":
            self.list_stack.append("ul")
            self.out.append("\n")
        elif tag == "ol":
            self.list_stack.append("ol")
            self.ol_counter.append(0)
            self.out.append("\n")
        elif tag == "li":
            if self.list_stack and self.list_stack[-1] == "ol":
                self.ol_counter[-1] += 1
                self.out.append(f"\n{self.ol_counter[-1]}. ")
            else:
                self.out.append("\n- ")
        elif tag == "a":
            self.in_link = True
            self.href = a.get("href", "")
            self.link_text = []
        elif tag == "img":
            src = a.get("src", "")
            alt = a.get("alt", "boat rental")
            if src:
                self.out.append(f"\n\n![{alt}]({src})\n")
        elif tag == "figure":
            self.out.append("\n\n")
        elif tag == "figcaption":
            # render caption as an italic line under the image
            self.out.append("\n*")
        elif tag == "br":
            self.out.append("  \n")

    def handle_endtag(self, tag):
        if tag in ("strong", "b"):
            self._emit("**")
        elif tag in ("em", "i"):
            self._emit("*")
        elif tag == "a" and self.in_link:
            text = "".join(self.link_text).strip() or self.href
            self.out.append(f"[{text}]({self.href})")
            self.in_link = False
            self.href = None
        elif tag == "figcaption":
            self.out.append("*\n")
        elif tag == "ul" and self.list_stack:
            self.list_stack.pop(); self.out.append("\n")
        elif tag == "ol" and self.list_stack:
            self.list_stack.pop(); self.ol_counter.pop(); self.out.append("\n")

    def handle_data(self, data):
        self._emit(re.sub(r"\s+", " ", data))

    def markdown(self):
        md = "".join(self.out)
        md = re.sub(r"\n{3,}", "\n\n", md)
        return md.strip() + "\n"


def html_to_md(html: str) -> str:
    p = _ToMarkdown()
    p.feed(html)
    p.close()
    return p.markdown()


def _opener():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [("User-Agent", "Mozilla/5.0"), ("Referer", BASE)]
    return op, cj


def create(text: str) -> dict:
    op, cj = _opener()
    op.open(BASE, timeout=30).read()
    token = next((c.value for c in cj if c.name == "csrftoken"), None)
    if not token:
        raise RuntimeError("no csrftoken from rentry.co")
    data = urllib.parse.urlencode({"csrf_token": token, "text": text}).encode()
    res = json.load(op.open(urllib.request.Request(BASE + "/api/new", data=data), timeout=30))
    if res.get("status") != "200":
        raise RuntimeError(f"rentry error: {res}")
    return res


def _state():
    return json.loads(STATE.read_text()) if STATE.exists() else {"published": {}}


def _save(s):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(s, indent=1, ensure_ascii=False))


def publish_next(n: int):
    st = _state()
    done = set(st["published"])
    pending = sorted(p for p in BACKLOG.glob("*.json") if p.stem not in done)
    if not pending:
        print("rentry backlog empty/all published. Add articles to content/rentry/.")
        return
    for p in pending[:n]:
        try:
            art = json.loads(p.read_text())
            md = f"# {art['title']}\n\n" + html_to_md(art["html"])
            res = create(md)
            st["published"][p.stem] = {
                "url": res["url"], "edit_code": res.get("edit_code"),
                "title": art["title"],
                "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            _save(st)
            print(f"PUBLISHED {p.stem} -> {res['url']}")
        except Exception as e:  # noqa: BLE001
            print(f"FAILED {p.stem}: {e}", file=sys.stderr)
    rem = len([p for p in BACKLOG.glob('*.json') if p.stem not in st['published']])
    print(f"\npublished; {rem} left in backlog")


def status():
    st = _state()
    total = len(list(BACKLOG.glob("*.json"))) if BACKLOG.exists() else 0
    print(f"rentry.co: {len(st['published'])} published / {total} in backlog / {total - len(st['published'])} pending")
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
