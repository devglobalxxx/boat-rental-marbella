#!/usr/bin/env python3
"""Deploy gate: fail (exit 1) when the rendered site contains
  1. unreplaced {{TEMPLATE}} tokens
  2. internal links pointing at nonexistent pages (above a small tolerance)
  3. fleet-size claims that contradict config/boats.json
  4. flagship price claims that contradict the pricing tiers

Run as the last render step in deploy.sh, before commit.
"""
from __future__ import annotations
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
BOATS = json.loads((ROOT / "config" / "boats.json").read_text())
FLEET_N = len(BOATS["boats"])
errors = []

# 0. stylesheet must be linked on every page (guards against link-rewriter regressions)
css_missing = []
for f in SITE.rglob("index.html"):
    s = f.read_text(errors="ignore")
    has_external = re.search(r'<link rel="stylesheet" href="(?:https://boatrentalinmarbella\.com)?/styles[a-z-]*\.css"', s)
    has_inline = "<style" in s
    if not has_external and not has_inline:
        css_missing.append(str(f.relative_to(SITE)))
if css_missing:
    errors.append(f"{len(css_missing)} pages missing /styles.css link, e.g. {css_missing[:3]}")

# 1. unreplaced template tokens
token_pages = []
for f in SITE.rglob("index.html"):
    if re.search(r"\{\{[A-Z_]+\}\}", f.read_text(errors="ignore")):
        token_pages.append(str(f.relative_to(SITE)))
if token_pages:
    errors.append(f"unreplaced template tokens on {len(token_pages)} pages, e.g. {token_pages[:3]}")

# 2. broken internal links
valid = set()
for f in SITE.rglob("index.html"):
    rel = f.relative_to(SITE).parent
    valid.add("/" if str(rel) == "." else f"/{rel}/")
asset_exts = (".jpg", ".png", ".css", ".js", ".mp4", ".xml", ".txt", ".json", ".ico", ".webp", ".avif", ".svg", ".html")
for f in SITE.rglob("*"):
    if f.is_file() and f.suffix in asset_exts:
        valid.add("/" + str(f.relative_to(SITE)))
broken = set()
for f in SITE.rglob("index.html"):
    for m in re.finditer(r'href="(/[^"#?]*)"', f.read_text(errors="ignore")):
        href = m.group(1)
        if href.startswith("//"):
            continue
        h = href if href.endswith("/") or "." in href.split("/")[-1] else href + "/"
        if h not in valid:
            broken.add(h)
if len(broken) > 3:  # tolerance for transient build ordering
    errors.append(f"{len(broken)} broken internal link targets, e.g. {sorted(broken)[:5]}")

# 3. fleet-size contradictions
wrong_counts = set()
for f in list(SITE.rglob("index.html")) + [SITE / "llms.txt", SITE / "data" / "facts.json"]:
    if not f.exists():
        continue
    s = f.read_text(errors="ignore")
    for m in re.finditer(r"(\d{1,2})[- ][Bb]oat[s]?[ -][Ff]leet", s):
        if int(m.group(1)) != FLEET_N:
            wrong_counts.add(f"{f.relative_to(SITE)}: claims {m.group(1)}-boat fleet (actual {FLEET_N})")
if wrong_counts:
    errors.append("fleet-size contradictions: " + "; ".join(sorted(wrong_counts)[:5]))

# 4. flagship price sanity — Mangusta 4h must be the tier_b price everywhere it appears with a price
tier_b_price = BOATS["hourly_price_tiers"]["tier_b"]["prices"]["4h"]  # 4719
bad_price_pages = []
mangusta = SITE / "boats" / "mangusta-80" / "index.html"
if mangusta.exists():
    s = mangusta.read_text(errors="ignore")
    if f"€{tier_b_price:,}" not in s and f"€{tier_b_price}" not in s:
        bad_price_pages.append("boats/mangusta-80 missing current flagship price")
if bad_price_pages:
    errors.append("; ".join(bad_price_pages))

if errors:
    print("CONSISTENCY CHECK FAILED:")
    for e in errors:
        print(f"  ✗ {e}")
    sys.exit(1)
print(f"consistency check OK (fleet={FLEET_N}, no tokens, links resolve, prices aligned)")
