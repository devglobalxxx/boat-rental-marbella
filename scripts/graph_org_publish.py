#!/usr/bin/env python3
"""graph.org publisher (Telegraph's sister domain, same API backend).

Reuses the Telegraph API + HTML->node converter from telegraph_publish.py, but
keeps its OWN backlog (content/graph_org/) and state (config/graph_org_state.json)
and reports graph.org URLs. Content is UNIQUE from the telegra.ph backlog to
avoid duplicate content. 3/day backlink drip to https://boathire24.com.

Usage:
  python3 scripts/graph_org_publish.py publish-next [N]
  python3 scripts/graph_org_publish.py status
"""
import importlib.util
import json
import pathlib
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
BACKLOG = ROOT / "content" / "graph_org"
STATE = ROOT / "config" / "graph_org_state.json"

# import the shared Telegraph helpers
_spec = importlib.util.spec_from_file_location("tp", str(ROOT / "scripts" / "telegraph_publish.py"))
tp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tp)


def _state():
    return json.loads(STATE.read_text()) if STATE.exists() else {"published": {}}


def _save(s):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(s, indent=1, ensure_ascii=False))


def publish_next(n: int):
    token = tp.get_token()
    st = _state()
    done = set(st["published"])
    pending = sorted(p for p in BACKLOG.glob("*.json") if p.stem not in done)
    if not pending:
        print("graph.org backlog empty/all published. Add articles to content/graph_org/.")
        return
    for p in pending[:n]:
        try:
            url = tp.publish_article(p, token)          # returns telegra.ph URL
            url = url.replace("https://telegra.ph/", "https://graph.org/")
            st["published"][p.stem] = {
                "url": url,
                "title": json.loads(p.read_text())["title"],
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
