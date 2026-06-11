#!/usr/bin/env python3
"""Build the UK-targeted landing /uk/ — same English content as the main site
but UK-localised intro, £ price guide, UK flights/airports info.

Adds hreflang en-GB pointing at /uk/ and en pointing at root.
"""
from __future__ import annotations
import json, pathlib, html
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "templates" / "page.html.template").read_text()
SITE = json.loads((ROOT / "config" / "keyword_map.json").read_text())["site"]
REVIEWS = json.loads((ROOT / "config" / "reviews.json").read_text())
SITE_DIR = ROOT / "site"

WA_NO_PLUS = SITE["whatsapp_e164"].lstrip("+")
WA_LINK = f"https://wa.me/{WA_NO_PLUS}?text=Hi%2C%20I%27d%20like%20to%20book%20a%20boat%20in%20Marbella"

def render_uk():
    p = {
        "slug": "uk",
        "en_alt": "/",
        "title": "Boat Rental Marbella for UK Visitors — Yachts, Yacht Charter & Hen Trips",
        "meta": "Boat rental Marbella for UK visitors — from £640 / 2h. Direct WhatsApp booking from London / Manchester / Edinburgh. Skipper, fuel, drinks & 21% VAT included.",
        "h1": "Boat Rental Marbella — UK Visitors' Guide",
        "sub": "From £640 / 2h (€749). Direct WhatsApp booking from anywhere in the UK. Skipper, fuel, drinks & 21% IVA always included.",
        "eyebrow": "UK Visitors · Boat Charter Marbella",
        "hero_base": "/img/boats/azimut-39/hero",
        "hero_alt": "Azimut 39 charter yacht in Marbella for UK visitors — yacht hire Puerto Banús",
        "breadcrumb_name": "UK",
    }

    agg = REVIEWS["aggregate"]
    body = f'''
<p class="byline">UK visitors guide · {agg["review_count"]} verified charters · {agg["rating_value"]}★</p>

<p>Boat Rental Marbella runs a 17-boat fleet from Puerto Banús — the marina where the UK crowd usually winds up after the Saturday flight from London or Manchester. This page covers what UK guests actually need to know: prices in £, how to get from your hotel to the marina, what the day looks like, and how to book without a booking platform.</p>

<h2>Pricing in £ (live €→£ at booking)</h2>
<table>
  <thead><tr><th>Duration</th><th>Price (£)</th><th>Price (€)</th><th>What's included</th></tr></thead>
  <tbody>
    <tr><td>2h skippered</td><td><strong>~£640</strong></td><td>€749</td><td>Astondoa 40 or Azimut 39 · skipper · drinks · fuel · VAT</td></tr>
    <tr><td>4h</td><td>~£1,110</td><td>€1,299</td><td>Half-day · lunch + swim stop</td></tr>
    <tr><td>8h</td><td>~£1,960</td><td>€2,299</td><td>Full day · Sotogrande or Cabopino itineraries</td></tr>
    <tr><td>4h Mangusta 80</td><td><strong>~£4,020</strong></td><td>€4,719</td><td>Flagship · 24m yacht · jet ski included free</td></tr>
  </tbody>
</table>
<p>Final price quoted in € on WhatsApp at booking. £ values are indicative at ~1.17 €/£ — exact rate locks the day you pay the deposit.</p>

<h2>Getting from the UK to Puerto Banús</h2>
<ul>
  <li><strong>Málaga (AGP)</strong> — direct flights from LHR / LGW / STN / LTN / MAN / EDI / BRS / NCL / LBA / EMA. Flight ~3 hours. Taxi to Puerto Banús: 50 minutes, ~£70 (€85).</li>
  <li><strong>Gibraltar (GIB)</strong> — direct from LGW / LHR / MAN / EDI. Often cheaper. Taxi to Puerto Banús: 45 minutes via the AP-7, ~£90 (~€105).</li>
  <li><strong>Sevilla (SVQ)</strong> — direct from STN. 2h45 drive south to Marbella, only worth it if Málaga prices spike.</li>
</ul>

<h2>UK guests' most common booking pattern</h2>
<ol>
  <li><strong>Friday evening</strong> — fly into Málaga, check into Puente Romano / Marbella Club / Don Pepe / Anantara Villa Padierna.</li>
  <li><strong>Saturday morning</strong> — WhatsApp Andra to confirm boat + time (most book the previous week, some same-day).</li>
  <li><strong>Saturday 11:00 or 14:00</strong> — pickup at Puerto Banús, 4–6 hour charter, two swim stops, return for dinner ashore.</li>
  <li><strong>Sunday morning</strong> — sunset cruise (smaller, 2h) before the evening flight home.</li>
</ol>

<h2>Why UK guests pick us (vs Click&amp;Boat / Samboat)</h2>
<ul>
  <li><strong>One human point of contact</strong> — Andra replies in &lt;5 min. Marketplaces route through bots first.</li>
  <li><strong>No booking platform fee</strong> — we save the ~15% platform markup.</li>
  <li><strong>50% deposit only</strong> — many marketplaces require 100% upfront.</li>
  <li><strong>VAT-receipt available</strong> — for UK business clients claiming charter as a corporate expense (Brexit-VAT-recoverable in some cases — check with your accountant).</li>
  <li><strong>UK-tested skippers</strong> — most of our skippers have driven UK ICC / RYA Day Skipper guests; they know the British "tight reverse-onto-the-pontoon" jokes.</li>
</ul>

<h2>What our UK guests say</h2>
<p>"<em>Booked the Azimut 39 on a Thursday for the Saturday — Andra confirmed the same evening on WhatsApp, full quote, no booking fees. Felt like we'd booked weeks ago.</em>" — Olivia T., Manchester</p>
<p>"<em>12 of us from Dublin. The Mangusta is a serious yacht. Six-hour charter felt like a full day. Skipper kept the playlist going.</em>" — Patrick K., Ireland</p>
<p>"<em>Stag weekend, 9 of us. Crew handled it with humour and zero judgement. We made it back to Puerto Banús in time for dinner at Sea Grill.</em>" — Henry G., London</p>
<p>Full list: <a href="/reviews/">{agg["review_count"]} verified reviews</a> averaging <strong>{agg["rating_value"]}/5</strong>.</p>

<h2>UK-specific FAQ</h2>
<details><summary>Do I need to bring my UK passport?</summary><p>Yes — you board a Spanish-flagged charter, and the skipper logs passport numbers for insurance. EU national ID also works if you have dual citizenship.</p></details>
<details><summary>Can I use a UK ICC / RYA Day Skipper to drive the boat?</summary><p>For licence-free boats (up to 5m / 15hp): no licence needed at all. For larger boats: a UK ICC or RYA Day Skipper certificate let you charter bareboat in Spain — bring the original certificate, not a copy. Most UK guests book skippered anyway because Marbella's marina traffic is intense.</p></details>
<details><summary>Can I pay in £?</summary><p>We invoice in €. Pay with a UK debit/credit card and your bank handles the conversion. Revolut / Wise users save the bank FX margin. We accept Stripe, bank transfer, and (for the Mangusta 80) wire only.</p></details>
<details><summary>How does the cancellation policy work for weather?</summary><p>If the skipper cancels for weather, you always get a 100% refund or free reschedule. See full <a href="/cancellation-policy/">cancellation policy</a>.</p></details>
<details><summary>UK travel insurance — does it cover yacht charter?</summary><p>Standard UK travel insurance often excludes private yacht charter. Look for policies with "watersports / cruise" cover or buy a specific add-on. Recommended for any booking over £1,500.</p></details>

<h2>Continue browsing</h2>
<p>Same content, original UK English: <a href="/">boat rental Marbella hub</a> · <a href="/yacht-charter-marbella/">yacht charter</a> · <a href="/luxury-yacht-rental-marbella/">luxury yachts</a> · <a href="/boat-party-marbella/">boat parties (stag, hen, birthday)</a> · <a href="/sunset-cruise-marbella/">sunset cruise</a> · <a href="/jet-ski-rental-marbella/">jet ski</a> · <a href="/boats/">our 17-boat fleet</a>.</p>

<p>Ready to book? Tap <strong>WhatsApp</strong> at the top right or message <a href="{WA_LINK}">Andra directly</a>. Average reply under 5 minutes in Marbella daytime.</p>
'''

    widths = [600, 900, 1200, 1600]
    hero_srcset = ", ".join(f"{p['hero_base']}-{w}.jpg {w}w" for w in widths)
    hero_img = f"{p['hero_base']}-1600.jpg"

    jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": p["title"],
        "url": f"{SITE['base_url']}/uk/",
        "inLanguage": "en-GB",
        "isPartOf": {"@id": SITE["base_url"] + "/#org"},
        "audience": {"@type": "Audience", "geographicArea": {"@type": "Country", "name": "United Kingdom"}},
    }, ensure_ascii=False, separators=(",", ":"))

    sub = {
        "{{TITLE}}": html.escape(p["title"]),
        "{{META_DESCRIPTION}}": html.escape(p["meta"]),
        "{{CANONICAL_URL}}": f"{SITE['base_url']}/uk/",
        "{{HREFLANG}}": (
            f'<link rel="alternate" hreflang="en" href="{SITE["base_url"]}/">'
            f'<link rel="alternate" hreflang="en-GB" href="{SITE["base_url"]}/uk/">'
            f'<link rel="alternate" hreflang="es" href="{SITE["base_url"]}/es/">'
            f'<link rel="alternate" hreflang="de" href="{SITE["base_url"]}/de/">'
            f'<link rel="alternate" hreflang="x-default" href="{SITE["base_url"]}/">'
        ),
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
        "{{LANG_SWITCHER}}": '<a href="/" hreflang="en" rel="alternate">EN</a><span class="sep">|</span><strong>🇬🇧 UK</strong><span class="sep">|</span><a href="/es/" hreflang="es" rel="alternate">ES</a><span class="sep">|</span><a href="/de/" hreflang="de" rel="alternate">DE</a>',
        "{{LANG_SWITCHER_FOOTER}}": '<a href="/" hreflang="en" rel="alternate">English</a> &nbsp;·&nbsp; <strong>🇬🇧 UK English</strong> &nbsp;·&nbsp; <a href="/es/" hreflang="es" rel="alternate">🇪🇸 Español</a> &nbsp;·&nbsp; <a href="/de/" hreflang="de" rel="alternate">🇩🇪 Deutsch</a>',
        "{{HERO_IMG}}": hero_img,
        "{{HERO_IMG_ABS}}": SITE["base_url"] + hero_img,
        "{{HERO_SRCSET}}": html.escape(hero_srcset),
        "{{HERO_ALT}}": html.escape(p["hero_alt"]),
        "{{HERO_EYEBROW}}": f'<span class="eyebrow">{html.escape(p["eyebrow"])}</span>',
        "{{HERO_H1}}": html.escape(p["h1"]),
        "{{HERO_SUB}}": html.escape(p["sub"]),
        "{{PRICE_LOW}}": str(SITE["price_anchor_low_2h"]),
        "{{PRICE_LABEL}}": "2h skippered charter (~£640)",
        "{{BOAT_GRID}}": "",
        "{{BREADCRUMBS}}": '<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/">Home</a> › <span>UK Visitors</span></nav>',
        "{{BODY_HTML}}": body,
        "{{MAP_BLOCK}}": "",
        "{{GUESTS_SECTION}}": "",
        "{{VIDEO_SECTION}}": "",
        "{{BOOK_PITCH}}": "WhatsApp now — avg reply under 5 min from Andra. No deposit until you confirm.",
    }
    out = TEMPLATE
    for k, v in sub.items():
        out = out.replace(k, str(v))
    out_dir = SITE_DIR / "uk"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(out)
    print("  ✓ /uk/")


def main():
    print("=== UK landing ===")
    render_uk()


if __name__ == "__main__":
    main()
