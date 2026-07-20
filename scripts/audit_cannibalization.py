#!/usr/bin/env python3
"""Site-wide keyword-cannibalization audit.

Finds clusters of pages whose slug/title/primary-keyword target the same search
intent, EXCLUDING pairs already resolved via config/blog_canonical_map.json.
Uses the same similarity logic as the daily_content.py dedup gate so the audit
and the gate agree on what "duplicate" means.

Output: report to stdout + machine-readable clusters to
logs/cannibalization_audit.json. Read-only — does not modify the canonical map.

Usage:
  python3 scripts/audit_cannibalization.py             # threshold 0.75
  python3 scripts/audit_cannibalization.py --t 0.70    # looser sweep
"""
from __future__ import annotations
import argparse, difflib, json, pathlib, re, sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = ROOT / "site"

# Language mirrors + non-content dirs: never audit (translations have hreflang,
# they are not cannibalization).
SKIP_TOP = {
    "es", "de", "fr", "uk", "pl", "ar", "sv", "nl", "it", "ru", "no", "da", "fi", "et",
    "img", "api", "data", "ig", "tags", "search",
}
SKIP_EXACT = {
    "about", "contact", "cookies", "privacy", "terms", "cancellation-policy",
    "sitemap", "reviews", "faq", "boats",
}

_GENERIC = {
    "a", "an", "and", "at", "blog", "by", "day", "experiences", "for", "from",
    "guide", "hire", "how", "in", "of", "on", "the", "tips", "to", "trip",
    "vs", "what", "when", "where", "with", "your",
    "marbella", "spain", "boat", "boats", "yacht", "yachts",
    "charter", "charters", "rental", "rentals",
}

def tokens(text: str) -> set:
    t = set(re.split(r"[^a-z0-9]+", text.lower())) - {""}
    return (t - _GENERIC) or t

def similarity(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    jac = len(ta & tb) / len(ta | tb) if (ta or tb) else 0.0
    ratio = difflib.SequenceMatcher(None, " ".join(sorted(ta)), " ".join(sorted(tb))).ratio()
    return max(jac, ratio)

def collect_pages() -> dict[str, str]:
    """slug -> comparison text (slug + title + primary keyword when known)."""
    pages: dict[str, str] = {}
    km = json.loads((ROOT / "config" / "keyword_map.json").read_text())
    for bucket in ("spokes", "blog"):
        for it in km.get(bucket, []):
            slug = (it.get("slug") or "").strip("/")
            if slug:
                pages[slug] = " ".join(
                    filter(None, [slug, it.get("title", ""), it.get("primary_keyword", "")])
                )
    # Rendered pages not in keyword_map (hand-built experiences, boat pages…)
    for d in SITE.rglob("index.html"):
        rel = d.relative_to(SITE).parent
        slug = str(rel)
        if slug == ".":
            continue
        top = slug.split("/")[0]
        if top in SKIP_TOP or slug in SKIP_EXACT:
            continue
        if slug.startswith("boats/"):  # one page per physical boat — never dupes
            continue
        if re.match(r"^blog/[a-z0-9]+-review-marbella$", slug):
            # one review page per physical boat — the shared "<boat>-review-marbella"
            # template makes these score high on similarity despite covering distinct
            # boats. Verified 2026-07-20 (14 boats, all genuinely different subjects).
            continue
        pages.setdefault(slug, slug)
    return pages

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--t", type=float, default=0.75, help="similarity threshold")
    args = ap.parse_args()

    canon = json.loads((ROOT / "config" / "blog_canonical_map.json").read_text())["map"]
    already_dupe = set(canon.keys())

    pages = collect_pages()
    # Exclude pages already canonicalized away — they're solved.
    slugs = sorted(s for s in pages if s not in already_dupe)
    print(f"auditing {len(slugs)} pages (skipped {len(already_dupe)} already-mapped dupes)\n")

    # Union-find clustering over pairs >= threshold
    parent = {s: s for s in slugs}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    pair_scores = {}
    for i, a in enumerate(slugs):
        for b in slugs[i + 1:]:
            s = similarity(pages[a], pages[b])
            if s >= args.t:
                union(a, b)
                pair_scores[(a, b)] = s

    clusters = defaultdict(list)
    for s in slugs:
        clusters[find(s)].append(s)
    real = sorted(
        (v for v in clusters.values() if len(v) > 1),
        key=len, reverse=True,
    )

    out = []
    for members in real:
        members.sort()
        scores = {
            f"{a} <> {b}": round(s, 2)
            for (a, b), s in pair_scores.items()
            if a in members and b in members
        }
        out.append({"members": members, "pair_scores": scores})
        print(f"CLUSTER ({len(members)}):")
        for m in members:
            print(f"  - {m}")
        for k, v in sorted(scores.items(), key=lambda x: -x[1]):
            print(f"      {v}  {k}")
        print()

    report = {"threshold": args.t, "n_pages": len(slugs), "clusters": out}
    (ROOT / "logs" / "cannibalization_audit.json").write_text(
        json.dumps(report, indent=1)
    )
    print(f"{len(real)} unresolved cluster(s) -> logs/cannibalization_audit.json")
    return 0

if __name__ == "__main__":
    sys.exit(main())
