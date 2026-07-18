#!/usr/bin/env python3
"""Validate (and optionally fix) per-boat price claims in content/*.json against
config/boats.json hourly_price_tiers (SEO audit 2026-07 follow-up: LLM-written
posts hallucinated intermediate tier prices like €1,499/4h for the real €1,299).

Every "€X for N hours" style claim is attributed to the nearest preceding boat
or tier mention. Claims about boats with published tiers are auto-fixable;
claims that price an on-request boat are only reported (they need a sentence
rewrite, not a number swap). Market/competitor context is skipped.

Usage:
  python3 scripts/check_price_claims.py            # report only
  python3 scripts/check_price_claims.py --fix      # rewrite mismatched numbers
"""
from __future__ import annotations
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "config" / "boats.json").read_text())
TIERS = {k: {int(h.rstrip("h")): p for h, p in t.get("prices", {}).items()}
         for k, t in CFG["hourly_price_tiers"].items()}

# display-name → tier key (longest names first so "Fairline Targa 43" wins over "Fairline Targa")
NAME_TIER: list[tuple[str, str]] = []
for b in CFG["boats"]:
    slug, tier = b["slug"], b.get("tier", "on_request")
    name = b.get("name") or slug.replace("-", " ").title()
    NAME_TIER.append((name, tier))
    NAME_TIER.append((slug.replace("-", " "), tier))
NAME_TIER += [("Tier A", "tier_a"), ("Tier B", "tier_b")]
NAME_TIER.sort(key=lambda x: -len(x[0]))

MARKET_WORDS = re.compile(
    r"market|typical|operators?\s+charge|competitor|elsewhere|other\s+(luxury|charter)|"
    r"across\s+marbella|€[\d,]+\s*[–-]\s*€?[\d,]+", re.I)

# price-then-duration and duration-then-price claim shapes
PATTERNS = [
    re.compile(r"€(?P<price>[\d,]{3,6})\s*(?:total\s*)?(?:for\s+(?:a\s+)?|/\s*|\(\s*)(?P<h>\d)\s*[-\s]?h(?:ours?|our)?\b", re.I),
    re.compile(r"(?P<h>\d)\s*[-\s]?hours?\s*(?:charter|option|trip|cruise)?\s*[\(:—-]\s*€(?P<price>[\d,]{3,6})", re.I),
    re.compile(r"(?P<h>\d)\s*hours?</(?:td|strong|th)>\s*(?:</tr>)?\s*<td>\s*€(?P<price>[\d,]{3,6})", re.I),
    re.compile(r"€(?P<price>[\d,]{3,6})\s*\(\s*(?P<h>\d)\s*h\b", re.I),
]

# names too generic to attribute a price to safely
AMBIGUOUS = {"speedboat", "bandido", "k80", "dubhe"}
# if any of these sit between the subject and the price, the price is about
# something else (e.g. "Azimut 39 ... upgrade to the Mangusta 80 at €4,719")
INTERVENING = re.compile(r"mangusta|flagship|superyacht|jet\s*ski|sea[- ]doo|dubhe|maiora|mefasa|sunseeker|princess|prestige|fairline|pershing|ferretti|canados|lagoon", re.I)

def attribute(text: str, pos: int) -> tuple[str, str] | None:
    """Nearest boat/tier mention within 140 chars, with no other boat mentioned
    between it and the price. Conservative by design: no subject → no verdict."""
    window = text[max(0, pos - 140):pos]
    best = None
    for name, tier in NAME_TIER:
        i = window.lower().rfind(name.lower())
        if i >= 0 and (best is None or i > best[0]):
            best = (i, name, tier, i + len(name))
    if not best:
        return None
    i, name, tier, end = best
    if name.lower() in AMBIGUOUS:
        return None
    between = window[end:]
    m = INTERVENING.search(between)
    if m and m.group(0).lower() not in name.lower():
        return None
    return (name, tier)

def scan(fix: bool) -> tuple[int, int, int]:
    mismatches = fixed = unfixable = 0
    for f in sorted(ROOT.glob("content/*.json")):
        raw = f.read_text()
        edits: list[tuple[int, int, str]] = []
        seen = set()
        for pat in PATTERNS:
            for m in pat.finditer(raw):
                key = (m.start(), m.group("price"))
                if key in seen:
                    continue
                seen.add(key)
                claimed = int(m.group("price").replace(",", ""))
                hours = int(m.group("h"))
                if claimed < 200:          # per-person / add-on amounts, not charters
                    continue
                ctx = raw[max(0, m.start() - 260):m.start()]
                if MARKET_WORDS.search(raw[max(0, m.start() - 120):m.end() + 40]):
                    continue
                who = attribute(raw, m.start())
                if not who:
                    continue
                name, tier = who
                prices = TIERS.get(tier)
                if not prices:             # on-request boat priced with a number
                    mismatches += 1
                    unfixable += 1
                    print(f"UNFIXABLE {f.name}: {name} is on-request but claims €{claimed:,} / {hours}h")
                    continue
                real = prices.get(hours)
                if real is None:
                    mismatches += 1
                    unfixable += 1
                    print(f"UNFIXABLE {f.name}: {name} has no {hours}h tier (claims €{claimed:,}) — real tiers: {prices}")
                    continue
                if claimed != real:
                    mismatches += 1
                    # Only auto-fix values from the known hallucinated tier-A ladder.
                    # Anything else (e.g. €4,719 attributed to an Azimut) is more
                    # likely a mis-attribution of a DIFFERENT boat's correct price —
                    # rewriting those numbers would corrupt good content.
                    safe = tier == "tier_a" and claimed in {1099, 1149, 1449, 1499, 1649, 1749, 1899}
                    print(f"{'MISMATCH ' if safe else 'REVIEW   '} {f.name}: {name} {hours}h claimed €{claimed:,} → real €{real:,}")
                    if fix and safe:
                        ps, pe = m.span("price")
                        edits.append((ps, pe, f"{real:,}"))
        if fix and edits:
            for ps, pe, new in sorted(edits, reverse=True):
                raw = raw[:ps] + new + raw[pe:]
            json.loads(raw)               # must still be valid JSON
            f.write_text(raw)
            fixed += len(edits)
    return mismatches, fixed, unfixable

if __name__ == "__main__":
    fix = "--fix" in sys.argv
    mis, fixed, unfix = scan(fix)
    print(f"\n{mis} mismatched claims; {fixed} fixed; {unfix} need manual rewrite")
    sys.exit(0)
