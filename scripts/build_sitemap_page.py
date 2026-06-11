#!/usr/bin/env python3
"""Build /site-map/ — a human-readable directory of every page, grouped by
category. Linked from the footer on every page, this guarantees no rendered
page is ever orphaned (every page is ≤2 clicks from home).
"""
from __future__ import annotations
import json, pathlib, re, html as h
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = json.loads((ROOT / "config" / "keyword_map.json").read_text())["site"]
TEMPLATE = (ROOT / "templates" / "page.html.template").read_text()
SITE_DIR = ROOT / "site"
BASE = SITE["base_url"].rstrip("/")
WA_NO_PLUS = SITE["whatsapp_e164"].lstrip("+")

CATS = [
    ("Charter types", lambda p: p.count("/") == 2 and not any(p.startswith(x) for x in ("/blog/", "/boats/", "/experiences/", "/de/", "/es/", "/uk/", "/fr/", "/nl/", "/no/", "/pl/", "/ru/", "/sv/", "/ar/", "/site-map/")) and p.strip("/") not in ("reviews", "about", "contact", "cancellation-policy", "cookies", "privacy", "terms")),
    ("Our fleet", lambda p: p.startswith("/boats/")),
    ("Experiences", lambda p: p.startswith("/experiences/")),
    ("Guides & blog", lambda p: p.startswith("/blog/")),
    ("Languages", lambda p: re.fullmatch(r"/(uk|es|de|fr|nl|no|pl|ru|sv|ar)/", p) is not None or (p.count("/") == 3 and any(p.startswith(f"/{l}/") for l in ("es", "de")))),
    ("About & policies", lambda p: p.strip("/") in ("reviews", "about", "contact", "cancellation-policy", "cookies", "privacy", "terms")),
]

def page_title(f: pathlib.Path) -> str:
    m = re.search(r"<title>([^<]+)</title>", f.read_text(errors="ignore"))
    t = m.group(1).strip() if m else ""
    return t.split("—")[0].split("|")[0].strip() or str(f.parent.name)

def main():
    pages = []
    for f in SITE_DIR.rglob("index.html"):
        rel = f.relative_to(SITE_DIR).parent
        p = "/" if str(rel) == "." else f"/{rel}/"
        if p in ("/", "/site-map/"):
            continue
        pages.append((p, page_title(f)))
    pages.sort()

    sections = []
    used = set()
    for cat, pred in CATS:
        items = [(p, t) for p, t in pages if pred(p) and p not in used]
        for p, _ in items:
            used.add(p)
        if not items:
            continue
        lis = "\n".join(f'<li><a href="{p}">{h.escape(t)}</a></li>' for p, t in items)
        sections.append(f"<h2>{cat} ({len(items)})</h2>\n<ul class=\"sitemap-cols\">\n{lis}\n</ul>")
    leftovers = [(p, t) for p, t in pages if p not in used]
    if leftovers:
        lis = "\n".join(f'<li><a href="{p}">{h.escape(t)}</a></li>' for p, t in leftovers)
        sections.append(f"<h2>More ({len(leftovers)})</h2>\n<ul class=\"sitemap-cols\">\n{lis}\n</ul>")

    body = (f'<p class="byline">{len(pages)} pages · Updated {date.today().strftime("%-d %B %Y")}</p>\n'
            f'<p>Every page on Boat Rental Marbella, grouped by section. Looking for something specific? '
            f'Message us on <a href="https://wa.me/{WA_NO_PLUS}" rel="nofollow noopener">WhatsApp</a> and ask.</p>\n'
            + "\n".join(sections))

    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": "Site map — Boat Rental Marbella", "url": f"{BASE}/site-map/",
    }, separators=(",", ":"))

    sub = {
        "{{TITLE}}": "Site Map — every page on Boat Rental Marbella",
        "{{META_DESCRIPTION}}": f"Full directory of all {len(pages)} pages on Boat Rental Marbella — charter types, fleet, experiences, guides, languages and policies.",
        "{{CANONICAL_URL}}": f"{BASE}/site-map/",
        "{{HREFLANG}}": "",
        "{{OG_TYPE}}": "website",
        "{{JSONLD}}": jsonld,
        "{{WHATSAPP_E164_NOPLUS}}": WA_NO_PLUS,
        "{{PHONE_E164}}": SITE["phone_e164"],
        "{{PHONE_DISPLAY}}": SITE["phone_display"],
        "{{EMAIL}}": SITE["email"],
        "{{INSTAGRAM_URL}}": SITE["instagram_url"],
        "{{INSTAGRAM_HANDLE}}": SITE["instagram_handle"],
        "{{FACEBOOK_URL}}": SITE["facebook_url"],
        "{{FACEBOOK_LABEL}}": SITE["facebook_label"],
        "{{AFFILIATE_LINK}}": SITE["affiliate_link"],
        "{{LANG_SWITCHER}}": '<strong>EN</strong>',
        "{{LANG_SWITCHER_FOOTER}}": '<strong>🇬🇧 English</strong>',
        "{{HERO_IMG}}": "/img/boats/mangusta-80/hero-1600.jpg",
        "{{HERO_IMG_ABS}}": BASE + "/img/boats/mangusta-80/hero-1600.jpg",
        "{{HERO_SRCSET}}": ", ".join(f"/img/boats/mangusta-80/hero-{w}.jpg {w}w" for w in (600, 900, 1200, 1600)),
        "{{HERO_ALT}}": "Boat Rental Marbella fleet",
        "{{HERO_EYEBROW}}": '<span class="eyebrow">Site map</span>',
        "{{HERO_H1}}": "Site Map",
        "{{HERO_SUB}}": "Every page, grouped by section.",
        "{{PRICE_LOW}}": str(SITE["price_anchor_low_2h"]),
        "{{PRICE_LABEL}}": "2h skippered charter",
        "{{BOAT_GRID}}": "",
        "{{BREADCRUMBS}}": '<nav class="breadcrumbs"><a href="/">Home</a> › <span>Site map</span></nav>',
        "{{BODY_HTML}}": body,
        "{{MAP_BLOCK}}": "",
        "{{GUESTS_SECTION}}": "",
        "{{VIDEO_SECTION}}": "",
        "{{BOOK_PITCH}}": "WhatsApp now — average reply under 5 minutes.",
    }
    out = TEMPLATE
    for k, v in sub.items():
        out = out.replace(k, str(v))
    d = SITE_DIR / "site-map"
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(out)
    print(f"  ✓ /site-map/ ({len(pages)} pages directory)")

if __name__ == "__main__":
    main()
