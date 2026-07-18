#!/usr/bin/env python3
"""Keep AggregateRating markup honest and manual-action-safe.

Google treats self-serving aggregateRating on pages without visibly rendered
reviews as spammy structured data, so this script now:
  1. strips every aggregateRating key from all JSON-LD blocks site-wide
     (cleanup of previously injected markup — the injectors edit committed HTML);
  2. attaches AggregateRating ONLY to the LocalBusiness block on /reviews/,
     where the reviews are visibly rendered, with reviewCount equal to the
     number of published review objects in config/reviews.json.

Idempotent — re-running converges to the same output.
"""
from __future__ import annotations
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "site"
REVIEWS = json.loads((ROOT / "config" / "reviews.json").read_text())
AGG = REVIEWS["aggregate"]
REVIEW_COUNT = len(REVIEWS["reviews"])  # honest count: only published reviews

RATING = {
    "@type": "AggregateRating",
    "ratingValue": AGG["rating_value"],
    "reviewCount": REVIEW_COUNT,
    "bestRating": AGG["best_rating"],
    "worstRating": AGG["worst_rating"],
}

SCRIPT_RE = re.compile(
    r'(<script type="application/ld\+json">)(.*?)(</script>)',
    re.DOTALL,
)

def strip_ratings(node) -> bool:
    """Recursively remove every aggregateRating key. Returns True if any removed."""
    changed = False
    if isinstance(node, dict):
        if node.pop("aggregateRating", None) is not None:
            changed = True
        for v in node.values():
            changed = strip_ratings(v) or changed
    elif isinstance(node, list):
        for v in node:
            changed = strip_ratings(v) or changed
    return changed

def add_rating(obj) -> bool:
    """Attach the honest rating to the first LocalBusiness block (reviews page only)."""
    targets = obj if isinstance(obj, list) else [obj]
    for t in targets:
        if not isinstance(t, dict):
            continue
        typ = t.get("@type")
        types = typ if isinstance(typ, list) else [typ] if typ else []
        if "LocalBusiness" in types:
            t["aggregateRating"] = RATING
            return True
    return False

def process(path: pathlib.Path, is_reviews_page: bool) -> bool:
    src = path.read_text()
    def _sub(m):
        try:
            obj = json.loads(m.group(2))
        except Exception:
            return m.group(0)
        changed = strip_ratings(obj)
        if is_reviews_page:
            changed = add_rating(obj) or changed
        if not changed:
            return m.group(0)
        return m.group(1) + json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + m.group(3)
    out = SCRIPT_RE.sub(_sub, src)
    if out != src:
        path.write_text(out)
        return True
    return False

def main():
    touched = 0
    reviews_page = SITE_DIR / "reviews" / "index.html"
    for p in SITE_DIR.rglob("index.html"):
        if process(p, p == reviews_page):
            touched += 1
    print(f"inject_aggregate_rating: cleaned {touched} page(s); "
          f"AggregateRating ({AGG['rating_value']}★ × {REVIEW_COUNT}) on /reviews/ only")

if __name__ == "__main__":
    main()
