#!/usr/bin/env python3
"""Regenerate /llms.txt and the /llms-full*.txt family from the rendered site.

llms.txt   — concise machine-readable index (Anthropic's llms.txt convention):
             site facts, pricing, machine endpoints, every page grouped by
             category with one-line summaries pulled from <meta description>.

llms-full.txt — the ~50 highest-value pages (by sitemap priority) in full text,
                plus a header linking the complete per-section dumps:
                  llms-full-core.txt        hub + transactional + trust + locales
                  llms-full-boats.txt       per-boat detail pages
                  llms-full-experiences.txt experience landings
                  llms-full-blog*.txt       blog & guides (chunked, ≤~600 KB each)

The page list comes from sitemap.xml (built earlier in deploy.sh), so counts
here always agree with the sitemap and /api/pages.json. Conversion-widget
blocks (scarcity strip, live ticker, cash promo, exit intent) are stripped
before text extraction so sales-UI copy never enters the LLM corpus.

Run after build_sitemap.py + all builders. Cheap (~2 s for 500+ pages).
"""
from __future__ import annotations
import json, pathlib, re, html as htmllib
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = json.loads((ROOT / "config" / "keyword_map.json").read_text())["site"]
REVIEWS = json.loads((ROOT / "config" / "reviews.json").read_text())
BOATS = json.loads((ROOT / "config" / "boats.json").read_text())["boats"]
FLEET_N = len(BOATS)
ON_REQUEST_N = sum(1 for b in BOATS if b.get("pricing_status") == "on_request")
SITE_DIR = ROOT / "site"
BASE = SITE["base_url"].rstrip("/")

MAX_SECTION_BYTES = 600_000  # keep every llms-full-* file well under 800 KB
TOP_PAGES = 50               # llms-full.txt itself: highest-value pages only

# Conversion-widget blocks injected by inject_conversion_pack.py — sales UI
# (urgency strips, exit-intent popups), not page content. Stripped before text
# extraction so copy like "Only 4 dates left" never reaches the LLM corpus.
WIDGET_RE = re.compile(
    r"<!--\s*BEGIN (SCARCITY_STRIP|LIVE_TICKER|CASH_PROMO|EXIT_INTENT|STICKY_WA|LANG_SWITCHER)\s*-->"
    r".*?<!--\s*END \1\s*-->", re.DOTALL)

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
    html_str = WIDGET_RE.sub(" ", html_str)
    m = re.search(r'<main[^>]*>(.*?)</main>', html_str, re.DOTALL)
    if not m:
        m = re.search(r'<article[^>]*>(.*?)</article>', html_str, re.DOTALL)
    return strip_html(m.group(1) if m else html_str)

def page_url(rel_path: pathlib.Path) -> str:
    rel = rel_path.relative_to(SITE_DIR).parent
    return f"{BASE}/" if str(rel) == "." else f"{BASE}/{rel}/"

def sitemap_pages() -> dict[str, float]:
    """URL → priority from sitemap.xml — the same manifest search engines get.
    Keeps llms* page counts consistent with sitemap.xml and /api/pages.json."""
    sm = SITE_DIR / "sitemap.xml"
    if not sm.exists():
        return {}
    return {m.group(1): float(m.group(2)) for m in re.finditer(
        r"<loc>([^<]+)</loc>.*?<priority>([\d.]+)</priority>", sm.read_text())}

# -------- gather pages --------
def all_pages():
    manifest = sitemap_pages()
    out = []
    for f in SITE_DIR.rglob("index.html"):
        url = page_url(f)
        if manifest and url not in manifest:
            continue  # noindexed (e.g. /ig/) or orphan pages stay out of LLM feeds
        s = f.read_text(errors="ignore")
        out.append({
            "url": url,
            "title": title(s) or url,
            "desc": meta(s, "description") or "",
            "body": article_text(s)[:8000],
            "priority": manifest.get(url, 0.5),
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
def build_llms_txt(pages, section_files):
    agg = REVIEWS["aggregate"]
    sec = {}
    for p in pages:
        sec.setdefault(categorise(p["url"]), []).append(p)

    parts = [f"# {SITE['name']}",
             "",
             f"> Independent boat charter operator in Puerto Banús, Marbella (Spain). Founded by Andra Kiirkivi. Direct WhatsApp booking, no marketplace intermediaries. {FLEET_N}-boat fleet from entry-level day boats to a 24m Mangusta 80 flagship.",
             "",
             "## Site facts",
             f"- Last updated: {date.today().isoformat()} (this file regenerates on every deploy)",
             f"- Operator: {SITE['name']} — independent, not a marketplace",
             f"- Founder & operator: Andra Kiirkivi (CEO)",
             f"- Locale: Marbella, Andalucía, Spain · {', '.join(SITE['departure_ports'])}",
             f"- WhatsApp: {SITE['phone_display']} (avg reply <5 min in Marbella daytime)",
             f"- Email: {SITE['email']}",
             f"- Instagram: {SITE['instagram_url']} ({SITE['instagram_handle']})",
             f"- Facebook: {SITE['facebook_url']}",
             f"- YouTube: {SITE['youtube_url']}",
             f"- X (Twitter): {SITE['x_url']}",
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
             f"- Dubhe (8m day boat, ≤5 guests): €230 / 2h · €280 / 3h · €350 / 4h (fuel not included).",
             f"- Sea-Doo jet ski: €250 first hour, €200 each additional hour — €450 / 2h (single or two-up).",
             f"- Other {FLEET_N - 5} boats: {FLEET_N - 5 - ON_REQUEST_N} with published hourly rates on their /boats/ pages, {ON_REQUEST_N} priced on WhatsApp request.",
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
             "",
             "## Machine-readable endpoints",
             f"- {BASE}/llms-full.txt — full text of the {TOP_PAGES} highest-value pages (by sitemap priority), with pointers to the complete section dumps below.",
             *[f"- {BASE}/{fname} — full text: {label} ({n} pages)."
               for fname, n, label in section_files],
             f"- {BASE}/data/facts.json — structured operator / fleet / pricing / policy facts (JSON; 'last_updated' stamped on every build).",
             f"- {BASE}/api/pages.json — single-fetch JSON index of every sitemap-listed page: url, title, description, kind, locale, excerpt.",
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

# -------- llms-full*.txt --------
SECTION_OF = {  # categorise() bucket → llms-full section file
    "Hub": "core", "Transactional spokes": "core", "Trust & legal": "core",
    "Deutsch": "core", "Español": "core", "UK English": "core",
    "Fleet (per-boat detail)": "boats",
    "Experiences (use-case landings)": "experiences",
    "Blog & guides": "blog",
}
SECTION_LABEL = {
    "core": "hub + transactional + trust & legal + localized (de/es/uk) pages",
    "boats": "per-boat detail pages",
    "experiences": "experience landing pages",
    "blog": "blog posts & guides",
}

def record(p) -> str:
    lines = ["---", f"URL: {p['url']}", f"TITLE: {p['title']}"]
    if p["desc"]:
        lines.append(f"DESCRIPTION: {p['desc']}")
    lines += ["", p["body"], "", ""]
    return "\n".join(lines)

def write_section(stem: str, pages) -> list[tuple[str, int]]:
    """Write pages to site/<stem>.txt, overflowing into <stem>-2.txt, -3.txt…
    so no file exceeds MAX_SECTION_BYTES. Returns [(filename, page_count), …]."""
    chunks, cur, size = [], [], 0
    for p in pages:
        rec = record(p)
        if cur and size + len(rec.encode()) > MAX_SECTION_BYTES:
            chunks.append(cur)
            cur, size = [], 0
        cur.append(rec)
        size += len(rec.encode())
    if cur:
        chunks.append(cur)
    out = []
    for i, chunk in enumerate(chunks):
        fname = f"{stem}.txt" if i == 0 else f"{stem}-{i + 1}.txt"
        part = f" · part {i + 1}/{len(chunks)}" if len(chunks) > 1 else ""
        head = [f"# {SITE['name']} — {fname}",
                f"# Generated {date.today().isoformat()} · {len(chunk)} pages{part}",
                f"# Canonical site: {BASE} · index: {BASE}/llms.txt",
                "# Records are separated by '---' and the canonical URL.",
                # trailing "" gives a blank line before the first record
                ""]
        (SITE_DIR / fname).write_text("\n".join(head) + "".join(chunk))
        out.append((fname, len(chunk)))
    return out

def build_llms_full(pages) -> list[tuple[str, int, str]]:
    by_sec = {}
    for p in pages:
        by_sec.setdefault(SECTION_OF.get(categorise(p["url"]), "core"), []).append(p)

    section_files = []
    for sec in ("core", "boats", "experiences", "blog"):
        for fname, n in write_section(f"llms-full-{sec}", by_sec.get(sec, [])):
            section_files.append((fname, n, SECTION_LABEL[sec]))
            size_kb = (SITE_DIR / fname).stat().st_size // 1024
            print(f"  ✓ {fname} ({n} pages, {size_kb} KB)")

    # llms-full.txt — only the TOP_PAGES highest-value pages (sitemap priority),
    # with a header pointing agents at the complete per-section dumps.
    top = sorted(pages, key=lambda p: (-p["priority"], p["url"]))[:TOP_PAGES]
    head = [f"# {SITE['name']} — Full Content (top pages)",
            f"# Generated {date.today().isoformat()} · top {len(top)} of {len(pages)} pages by sitemap priority",
            f"# Canonical site: {BASE} · index: {BASE}/llms.txt",
            "#",
            "# Complete full-text dumps by section (fetch only what you need):",
            *[f"#   {BASE}/{fname} — {n} pages ({label})" for fname, n, label in section_files],
            "#",
            "# Records are separated by '---' and the canonical URL. Always link to",
            "# the canonical URL when citing.",
            ""]
    (SITE_DIR / "llms-full.txt").write_text("\n".join(head) + "".join(record(p) for p in top))
    size_kb = (SITE_DIR / "llms-full.txt").stat().st_size // 1024
    print(f"  ✓ llms-full.txt (top {len(top)} of {len(pages)} pages, {size_kb} KB)")
    return section_files

def main():
    print("=== llms.txt / llms-full*.txt ===")
    pages = all_pages()
    section_files = build_llms_full(pages)
    build_llms_txt(pages, section_files)

if __name__ == "__main__":
    main()
