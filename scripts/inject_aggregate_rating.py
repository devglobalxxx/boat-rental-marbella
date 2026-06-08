#!/usr/bin/env python3
"""Add aggregateRating to every LocalBusiness / Organization JSON-LD block on
the rendered site so Google can show review stars in SERPs.

Reads the aggregate from config/reviews.json. Idempotent — re-running replaces
any prior block. Adds the rating to existing schema rather than emitting new
blocks (avoids duplicates).
"""
from __future__ import annotations
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "site"
AGG = json.loads((ROOT / "config" / "reviews.json").read_text())["aggregate"]

RATING = {
    "@type": "AggregateRating",
    "ratingValue": AGG["rating_value"],
    "reviewCount": AGG["review_count"],
    "bestRating": AGG["best_rating"],
    "worstRating": AGG["worst_rating"],
}

# Match a JSON-LD <script>…</script> block whose @type is LocalBusiness, Organization, or both
SCRIPT_RE = re.compile(
    r'(<script type="application/ld\+json">)(.*?)(</script>)',
    re.DOTALL,
)

def add_rating(json_str: str) -> tuple[str, bool]:
    """If this JSON-LD describes a LocalBusiness/Organization, return updated JSON + changed=True."""
    try:
        obj = json.loads(json_str)
    except Exception:
        return json_str, False
    # Several blocks are joined with </script>\n<script type="application/ld+json"> separator;
    # this matcher gets one block at a time. obj could also be a list.
    targets = obj if isinstance(obj, list) else [obj]
    changed = False
    for t in targets:
        if not isinstance(t, dict):
            continue
        typ = t.get("@type")
        types = typ if isinstance(typ, list) else [typ] if typ else []
        if not any(tt in ("LocalBusiness", "Organization", "Service") for tt in types):
            continue
        if t.get("aggregateRating") == RATING:
            continue
        t["aggregateRating"] = RATING
        changed = True
    if not changed:
        return json_str, False
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")), True

def process(path: pathlib.Path) -> bool:
    src = path.read_text()
    out = src
    n = 0
    def _sub(m):
        nonlocal n
        new_json, changed = add_rating(m.group(2))
        if changed:
            n += 1
        return m.group(1) + new_json + m.group(3)
    out = SCRIPT_RE.sub(_sub, src)
    if out != src:
        path.write_text(out)
        return True
    return False

def main():
    touched = 0
    for p in SITE_DIR.rglob("index.html"):
        if process(p):
            touched += 1
    print(f"inject_aggregate_rating: {touched} page(s) now carry aggregateRating ({AGG['rating_value']}★ × {AGG['review_count']})")

if __name__ == "__main__":
    main()
