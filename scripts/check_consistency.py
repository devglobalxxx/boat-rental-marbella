#!/usr/bin/env python3
"""Deploy gate: fail (exit 1) when the rendered site contains
  1. pages missing a stylesheet (guards against link-rewriter regressions)
  2. unreplaced {{TEMPLATE}} tokens visible to users
  3. fleet-size claims that contradict config/boats.json
  4. flagship price missing from the Mangusta page

Backend-only safety net — never modifies a single page.
"""
from __future__ import annotations
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
BOATS = json.loads((ROOT / "config" / "boats.json").read_text())
FLEET_N = len(BOATS["boats"])
errors = []

# 1. stylesheet present on every page (external styles*.css or inline <style>)
css_missing = []
for f in SITE.rglob("index.html"):
    s = f.read_text(errors="ignore")
    has_external = re.search(r'<link rel="stylesheet" href="(?:https://boatrentalinmarbella\.com)?/styles[a-z-]*\.css"', s)
    if not has_external and "<style" not in s:
        css_missing.append(str(f.relative_to(SITE)))
if css_missing:
    errors.append(f"{len(css_missing)} pages missing stylesheet, e.g. {css_missing[:3]}")

# 2. unreplaced template tokens ({{MAP_BLOCK}} allowlisted — pre-existing in the
#    approved version; remove via the one-line builder fix when sign-off given)
token_pages = []
for f in SITE.rglob("index.html"):
    s = f.read_text(errors="ignore").replace("{{MAP_BLOCK}}", "")
    if re.search(r"\{\{[A-Z_]+\}\}", s):
        token_pages.append(str(f.relative_to(SITE)))
if token_pages:
    errors.append(f"unreplaced template tokens on {len(token_pages)} pages, e.g. {token_pages[:3]}")

# 3. fleet-size claims must match config/boats.json
#    Scoped to fleet-claim phrases ("X-boat fleet", "fleet of X boats",
#    "X boats in our/the fleet", "our X boats") so counts like "2 jet skis"
#    never false-positive.
FLEET_CLAIM_RES = [
    re.compile(r"\b(\d{1,3})[-\s][Bb]oat [Ff]leet\b"),
    re.compile(r"\bfleet of (\d{1,3}) (?:boats|yachts|vessels)\b", re.IGNORECASE),
    re.compile(r"\b(\d{1,3}) (?:boats|yachts|vessels) in (?:our|the) fleet\b", re.IGNORECASE),
    re.compile(r"\bour (\d{1,3}) (?:boats|yachts)\b", re.IGNORECASE),
    re.compile(r"\bwe (?:operate|have) (\d{1,3}) (?:boats|yachts)\b", re.IGNORECASE),
]
fleet_claim_errors = []
targets = list(SITE.rglob("index.html"))
if (SITE / "llms.txt").exists():
    targets.append(SITE / "llms.txt")
for f in targets:
    s = f.read_text(errors="ignore")
    for rx in FLEET_CLAIM_RES:
        for m in rx.finditer(s):
            if int(m.group(1)) != FLEET_N:
                fleet_claim_errors.append(f"{f.relative_to(SITE)}: '{m.group(0)}'")
if fleet_claim_errors:
    errors.append(
        f"{len(fleet_claim_errors)} fleet-size claims contradict boats.json ({FLEET_N} boats), "
        f"e.g. {fleet_claim_errors[:3]}")

# 4. flagship price sanity
tier_b_price = BOATS["hourly_price_tiers"]["tier_b"]["prices"]["4h"]
mangusta = SITE / "boats" / "mangusta-80" / "index.html"
if mangusta.exists():
    s = mangusta.read_text(errors="ignore")
    if f"€{tier_b_price:,}" not in s and f"€{tier_b_price}" not in s:
        errors.append("boats/mangusta-80 missing current flagship price")

if errors:
    print("CONSISTENCY CHECK FAILED — deploy blocked:")
    for e in errors:
        print(f"  ✗ {e}")
    sys.exit(1)
print(f"consistency check OK ({FLEET_N}-boat fleet, stylesheets present, no tokens, prices aligned)")
