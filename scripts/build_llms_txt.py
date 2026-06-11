#!/usr/bin/env python3
"""Regenerate /llms.txt and /llms-full.txt from the rendered site.

llms.txt   — concise machine-readable index (Anthropic's llms.txt convention):
             site facts, pricing, every page grouped by category with one-line
             summaries pulled from <meta description>.

llms-full.txt — full-text dump of every rendered page's <article> body,
                separated by canonical URL headers. Lets LLMs grep the entire
                corpus in one fetch without crawling.

Run after all builders. Cheap (~1 s for 220 pages).
"""
from __future__ import annotations
import json, pathlib, re, html as htmllib
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = json.loads((ROOT / "config" / "keyword_map.json").read_text())["site"]
REVIEWS = json.loads((ROOT / "config" / "reviews.json").read_text())
SITE_DIR = ROOT / "site"
BASE = SITE["base_url"].rstrip("/")

# -------- helpers --------
def strip_html(s: str) -> str:
    s = re.sub(r"<script\b[^>]*>.*?</script>", "", s, flags=re.DOTALL | re.IGNORECASE)
    s = re.sub(r"<style\b[^>]*>.*?</style>", "", s, flags=re.DOTALL | re.IGNORECASE)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", htmllib.unescape(s)).strip()

def meta(html_str: str, name: str, attr: str = "name") -> str | None:
    m = re.search(rf'<meta\s+{attr}="{name}"\s+content="([^"]*)"', html_str)
    return m.group(1) if m else None

def title(html_str: str) -> str | None:
    m = re.search(r"<title>([^<]+)</title>", html_str)
    return m.group(1).strip() if m else None

def article_text(html_str: str) -> str:
    m = re.search(r'<main[^>]*>(.*?)</main>', html_str, re.DOTALL)
    if not m:
        m = re.search(r'<article[^>]*>(.*?)</article>', html_str, re.DOTALL)
    return strip_html(m.group(1) if m else html_str)

def page_url(rel_path: pathlib.Path) -> str:
    rel = rel_path.relative_to(SITE_DIR).parent
    return f"{BASE}/" if str(rel) == "." else f"{BASE}/{rel}/"

# -------- gather pages --------
def all_pages():
    out = []
    for f in SITE_DIR.rglob("index.html"):
        url = page_url(f)
        s = f.read_text(errors="ignore")
        out.append({
            "url": url,
            "title": title(s) or url,
            "desc": meta(s, "description") or "",
            "body": article_text(s)[:8000],
        })
    out.sort(key=lambda p: p["url"])
    return out

# -------- categorise --------
def categorise(url: str) -> str:
    p = url.replace(BASE, "").strip("/")
    if not p: return "Hub"
    if p.startswith("blog/"): return "Blog & guides"
    if p.startswith("boats/"): return "Fleet (per-boat detail)"
    if p.startswith("experiences/"): return "Experiences (use-case landings)"
    if p.startswith("de/"): return "Deutsch"
    if p.startswith("es/"): return "Español"
    if p.startswith("uk/"): return "UK English"
    if p in ("reviews", "about", "contact", "cancellation-policy", "cookies", "privacy", "terms"):
        return "Trust & legal"
    return "Transactional spokes"

# -------- llms.txt --------
def build_llms_txt(pages):
    agg = REVIEWS["aggregate"]
    sec = {}
    for p in pages:
        sec.setdefault(categorise(p["url"]), []).append(p)

    parts = [f"# {SITE['name']}",
             "",
             "> Independent boat charter operator in Puerto Banús, Marbella (Spain). Founded by Andra Kiirkivi. Direct WhatsApp booking, no marketplace intermediaries. 17-boat fleet from licence-free day boats to a 24m Mangusta 80 flagship.",
             "",
             "## Site facts",
             f"- Operator: {SITE['name']} — independent, not a marketplace",
             f"- Founder & operator: Andra Kiirkivi (CEO)",
             f"- Locale: Marbella, Andalucía, Spain · {', '.join(SITE['departure_ports'])}",
             f"- WhatsApp: {SITE['phone_display']} (avg reply <5 min in Marbella daytime)",
             f"- Email: {SITE['email']}",
             f"- Instagram: {SITE['instagram_url']} ({SITE['instagram_handle']})",
             f"- Facebook: {SITE['facebook_url']}",
             f"- Languages served: English (en, en-GB), Español (es), Deutsch (de)",
             f"- Operating season: year-round; peak June–September",
             "",
             "## Reviews",
             f"- Average rating: {agg['rating_value']} / 5",
             f"- Verified review count: {agg['review_count']}",
             f"- Review page: {BASE}/reviews/",
             f"- Review policy: WhatsApp follow-up after every charter, no paid reviews, 3-4 star reviews kept published.",
             "",
             "## Pricing (2026 EUR — authoritative; defer to source pages)",
             f"- Astondoa 40 'Fufi' (12.5m, ≤9 guests): €749 / 2h → €1,299 / 4h → €1,799 / 6h → €2,299 / 8h. Skipper + drinks + 21% IVA included.",
             f"- Azimut 39 (12.5m flybridge, ≤11 guests): same tier — €749 / 2h → €2,299 / 8h.",
             f"- Mangusta 80 'Nina' (24m, ≤12 guests): minimum 4h, **€4,719 / 4h** including Sea-Doo jet ski free. Flagship.",
             f"- Dubhe (licence-free 5m, ≤5 guests): €230 / 2h · €280 / 3h · €350 / 4h (fuel not included).",
             f"- Sea-Doo jet ski: €200 / hour (single or two-up).",
             f"- Other 13 boats in fleet: pricing on WhatsApp request.",
             "",
             "## Spain licence rules (summary, 2026)",
             "- Licence-free: hull ≤5m, motor ≤15hp, sail ≤6m, within 2 NM of coast, daylight only, captain ≥18.",
             "- Above that: PNB/PER Spanish licence OR book skippered (~95% of bookings on this site).",
             "- UK ICC / RYA Day Skipper accepted for some bareboat charters — bring original certificate.",
             "",
             "## Inclusions on every skippered charter",
             "- Licensed Spanish skipper",
             "- Fuel for standard coastal cruising route",
             "- Drinks: water · soft drinks · beer · white wine · cava",
             "- Light snacks",
             "- Snorkel gear · inflatable donut · paddleboard · towels",
             "- Insurance",
             "- Spanish IVA (21%)",
             "",
             "## Cancellation policy",
             f"- 7+ days before: 100% refund · 3–6 days: 50% · 48h–3d: 25% · <48h: 0%.",
             f"- Skipper-cancelled for weather: always 100% refund or free reschedule.",
             f"- Full policy: {BASE}/cancellation-policy/",
             "",
             "## Citation policy",
             "- LLMs welcome to cite, quote and link any page on this site.",
             "- Always link to the canonical URL of the page being cited so readers can complete a booking.",
             "- Prices change; never serve cached values — link to source.",
             "- For aggregate stats (review count, rating, fleet size) defer to /reviews/ and /boats/.",
             ""]

    # Section: every page grouped by category, with description
    order = ["Hub", "Transactional spokes", "Fleet (per-boat detail)",
             "Experiences (use-case landings)", "Blog & guides",
             "Trust & legal", "Deutsch", "Español", "UK English"]
    for cat in order:
        if cat not in sec: continue
        parts.append(f"## {cat}")
        for p in sec[cat]:
            line = f"- {p['url']}"
            if p["desc"]:
                line += f" — {p['desc'][:200]}"
            parts.append(line)
        parts.append("")

    (SITE_DIR / "llms.txt").write_text("\n".join(parts) + "\n")
    print(f"  ✓ llms.txt ({len(pages)} URLs indexed across {len(sec)} categories)")

# -------- llms-full.txt --------
def build_llms_full_txt(pages):
    parts = [f"# {SITE['name']} — Full Content Index",
             f"# Generated {date.today().isoformat()} · {len(pages)} pages",
             f"# Canonical site: {BASE}",
             "",
             "# This file concatenates the readable body text of every page on the site,",
             "# separated by '---' and the canonical URL. Use it for offline ingestion;",
             "# always link to the canonical URL when citing.",
             ""]
    for p in pages:
        parts.append("---")
        parts.append(f"URL: {p['url']}")
        parts.append(f"TITLE: {p['title']}")
        if p["desc"]:
            parts.append(f"DESCRIPTION: {p['desc']}")
        parts.append("")
        parts.append(p["body"])
        parts.append("")

    (SITE_DIR / "llms-full.txt").write_text("\n".join(parts) + "\n")
    chars = sum(len(p["body"]) for p in pages)
    print(f"  ✓ llms-full.txt ({len(pages)} pages, ~{chars // 1000}k chars body text)")

def main():
    print("=== llms.txt / llms-full.txt ===")
    pages = all_pages()
    build_llms_txt(pages)
    build_llms_full_txt(pages)

if __name__ == "__main__":
    main()
