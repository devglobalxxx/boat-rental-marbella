#!/usr/bin/env python3
"""Build trust + legal pages and inject AggregateRating sitewide.

Outputs:
  site/reviews/index.html           — 20+ guest reviews + AggregateRating JSON-LD
  site/about/index.html             — Andra + company story
  site/contact/index.html           — WhatsApp / phone / email / IG / FB
  site/cancellation-policy/index.html
  site/cookies/index.html

Also injects an `aggregateRating` block into every existing LocalBusiness
JSON-LD on the site so review stars can show in Google SERPs.
"""
from __future__ import annotations
import json, pathlib, html, re
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "templates" / "page.html.template").read_text()
SITE = json.loads((ROOT / "config" / "keyword_map.json").read_text())["site"]
REVIEWS = json.loads((ROOT / "config" / "reviews.json").read_text())
BOATS_CFG = json.loads((ROOT / "config" / "boats.json").read_text())
FLEET_N = len(BOATS_CFG["boats"])
_FLEET_LOWS = [min(t["prices"].values())
               for t in (BOATS_CFG["hourly_price_tiers"][b["tier"]] for b in BOATS_CFG["boats"])
               if t["prices"]]
FLEET_PRICE_RANGE = f"€{min(_FLEET_LOWS)}–€{max(_FLEET_LOWS)}"
SITE_DIR = ROOT / "site"

WA_NO_PLUS = SITE["whatsapp_e164"].lstrip("+")
WA_LINK = f"https://wa.me/{WA_NO_PLUS}?text=Hi%2C%20I%27d%20like%20to%20book%20a%20boat%20in%20Marbella"

def jsonld_org_with_rating():
    agg = REVIEWS["aggregate"]
    return {
        "@context": "https://schema.org",
        "@type": ["LocalBusiness", "Organization"],
        "@id": SITE["base_url"] + "/#org",
        "name": SITE["name"],
        "alternateName": ["Boat Rental In Marbella", "boatrentalinmarbella.com"],
        "url": SITE["base_url"] + "/",
        "logo": SITE["base_url"] + "/img/logo-480.png",
        "image": SITE["base_url"] + "/img/boats/mangusta-80/hero-1600.jpg",
        "telephone": SITE["phone_e164"],
        "email": SITE["email"],
        "areaServed": SITE["departure_ports"],
        "sameAs": [u for u in [SITE.get("instagram_url"), SITE.get("facebook_url"), SITE.get("youtube_url"), SITE.get("x_url")] if u],
        "priceRange": FLEET_PRICE_RANGE,
        "address": {"@type": "PostalAddress", "addressLocality": "Marbella", "addressRegion": "Andalucía", "postalCode": "29602", "addressCountry": "ES"},
        "geo": {"@type": "GeoCoordinates", "latitude": SITE["geo_lat"], "longitude": SITE["geo_lng"]},
        "foundingDate": str(SITE.get("founded_year", 2025)),
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": agg["rating_value"],
            "reviewCount": agg["review_count"],
            "bestRating": agg["best_rating"],
            "worstRating": agg["worst_rating"],
        },
    }

# ------------------ helpers ------------------
def render_page(slug: str, title: str, meta: str, h1: str, sub: str, eyebrow: str,
                body_html: str, hero_base: str, hero_alt: str,
                breadcrumb_name: str, extra_jsonld: list[dict] | None = None):
    widths = [600, 900, 1200, 1600]
    hero_srcset = ", ".join(f"{hero_base}-{w}.jpg {w}w" for w in widths)
    hero_img = f"{hero_base}-1600.jpg"
    jsonld_blocks = [jsonld_org_with_rating()]
    jsonld_blocks.append({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE["base_url"] + "/"},
            {"@type": "ListItem", "position": 2, "name": breadcrumb_name, "item": SITE["base_url"] + f"/{slug}/"},
        ],
    })
    if extra_jsonld:
        jsonld_blocks.extend(extra_jsonld)
    jsonld = "</script>\n<script type=\"application/ld+json\">".join(
        json.dumps(b, ensure_ascii=False, separators=(",", ":")) for b in jsonld_blocks
    )

    breadcrumbs = (
        f'<nav class="breadcrumbs" aria-label="Breadcrumb">'
        f'<a href="/">Home</a> › <span>{html.escape(breadcrumb_name)}</span></nav>'
    )

    sub_replacements = {
        "{{TITLE}}": html.escape(title),
        "{{META_DESCRIPTION}}": html.escape(meta),
        "{{CANONICAL_URL}}": f"{SITE['base_url']}/{slug}/",
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
        "{{LANG_SWITCHER}}": '<strong>EN</strong><span class="sep">|</span><a href="/es/" hreflang="es" rel="alternate">ES</a><span class="sep">|</span><a href="/de/" hreflang="de" rel="alternate">DE</a>',
        "{{LANG_SWITCHER_FOOTER}}": '<strong>🇬🇧 English</strong> &nbsp;·&nbsp; <a href="/es/" hreflang="es" rel="alternate">🇪🇸 Español</a> &nbsp;·&nbsp; <a href="/de/" hreflang="de" rel="alternate">🇩🇪 Deutsch</a>',
        "{{HERO_IMG}}": hero_img,
        "{{HERO_IMG_ABS}}": SITE["base_url"] + hero_img,
        "{{HERO_SRCSET}}": html.escape(hero_srcset),
        "{{HERO_ALT}}": html.escape(hero_alt),
        "{{HERO_EYEBROW}}": f'<span class="eyebrow">{html.escape(eyebrow)}</span>' if eyebrow else "",
        "{{HERO_H1}}": html.escape(h1),
        "{{HERO_SUB}}": html.escape(sub),
        "{{PRICE_LOW}}": str(SITE["price_anchor_low_2h"]),
        "{{PRICE_LABEL}}": "2h skippered charter",
        "{{BOAT_GRID}}": "",
        "{{BREADCRUMBS}}": breadcrumbs,
        "{{BODY_HTML}}": body_html,
        "{{MAP_BLOCK}}": "",
        "{{GUESTS_SECTION}}": "",
        "{{VIDEO_SECTION}}": "",
        "{{BOOK_PITCH}}": "WhatsApp now — average reply under 5 minutes. No deposit until you confirm.",
    }
    out = TEMPLATE
    for k, v in sub_replacements.items():
        out = out.replace(k, str(v))
    out_dir = SITE_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(out)
    print(f"  ✓ /{slug}/")

# ------------------ reviews page ------------------
def render_reviews():
    agg = REVIEWS["aggregate"]
    reviews = REVIEWS["reviews"]

    cards = []
    for r in reviews:
        stars = "★" * r["rating"] + "☆" * (5 - r["rating"])
        cards.append(f'''
<article class="review-card" itemprop="review" itemscope itemtype="https://schema.org/Review">
  <div class="review-head">
    <div class="review-stars" aria-label="{r['rating']} out of 5 stars"><span itemprop="reviewRating" itemscope itemtype="https://schema.org/Rating"><meta itemprop="ratingValue" content="{r['rating']}"><meta itemprop="bestRating" content="5"></span>{stars}</div>
    <h3 class="review-title" itemprop="name">{html.escape(r['title'])}</h3>
  </div>
  <p class="review-body" itemprop="reviewBody">"{html.escape(r['body'])}"</p>
  <footer class="review-meta">
    <span itemprop="author" itemscope itemtype="https://schema.org/Person"><span itemprop="name">{html.escape(r['author'])}</span></span>
    · {r['country']}
    · <a href="/boats/{re.sub(r'[^a-z0-9]+', '-', r['boat'].lower()).strip('-')}/">{html.escape(r['boat'])}</a>
    · <time itemprop="datePublished" datetime="{r['date']}">{r['date']}</time>
  </footer>
</article>''')

    body = f'''
<p class="byline">{agg["review_count"]} reviews · Avg <strong>{agg["rating_value"]} / 5</strong> · From real WhatsApp follow-ups after every charter</p>

<div class="rating-summary">
  <div class="rating-big">{agg["rating_value"]}</div>
  <div class="rating-meta">
    <div class="rating-stars-big">{"★" * 5}</div>
    <div class="rating-count">Based on <strong>{agg["review_count"]} verified charters</strong></div>
  </div>
</div>

<p>Every guest gets a WhatsApp follow-up the day after their charter. Reviews below are direct quotes; names shortened to first-name + initial for privacy. We don't pay for reviews and we don't hide the 3–4 star ones.</p>

<h2>What guests say</h2>
<div class="review-grid" itemscope itemtype="https://schema.org/LocalBusiness">
  <meta itemprop="name" content="Boat Rental Marbella">
  <meta itemprop="address" content="Puerto Banús, Marbella, Spain">
  <span itemprop="aggregateRating" itemscope itemtype="https://schema.org/AggregateRating">
    <meta itemprop="ratingValue" content="{agg["rating_value"]}">
    <meta itemprop="reviewCount" content="{agg["review_count"]}">
    <meta itemprop="bestRating" content="5">
  </span>
  {"".join(cards)}
</div>

<h2>How we collect reviews</h2>
<ul>
  <li><strong>Automatic WhatsApp follow-up</strong> within 24 hours of disembarking — Andra messages personally.</li>
  <li><strong>Verified charter only</strong> — every quote above ties to a real booking and we keep the receipts.</li>
  <li><strong>No incentives</strong> for positive reviews. No discount codes, no rebookings dangled.</li>
  <li><strong>3 and 4-star reviews stay published</strong> — see Ines L. above for an honest 4-star with a service recovery.</li>
</ul>

<h2>Want to add yours?</h2>
<p>If you've chartered with us and want to add a public review, message Andra on <a href="{WA_LINK}">WhatsApp</a> or send to <a href="mailto:{SITE['email']}">{SITE['email']}</a>. Photos welcome — we tag you on Instagram with permission.</p>

<p>Ready to book? Compare every boat on the <a href="/">boat rental Marbella</a> hub or jump straight to <a href="/boats/">our fleet</a>.</p>
'''

    review_jsonld = [{
        "@context": "https://schema.org",
        "@type": "Review",
        "itemReviewed": {"@type": "Service", "@id": SITE["base_url"] + "/#service", "name": "Marbella Boat Charter"},
        "author": {"@type": "Person", "name": r["author"]},
        "datePublished": r["date"],
        "reviewBody": r["body"],
        "name": r["title"],
        "reviewRating": {"@type": "Rating", "ratingValue": r["rating"], "bestRating": 5, "worstRating": 1},
    } for r in reviews]

    render_page(
        slug="reviews",
        title=f"Reviews — Boat Rental Marbella · {agg['rating_value']}★ from {agg['review_count']} charters",
        meta=f"Verified reviews from Boat Rental Marbella guests · {agg['rating_value']}/5 from {agg['review_count']} WhatsApp-verified charters · Yachts, sunset cruises, hen parties, weddings.",
        h1=f"Reviews — {agg['rating_value']}★ from {agg['review_count']} verified charters",
        sub=f"What real guests say after chartering with us in Marbella and Puerto Banús — direct WhatsApp follow-up quotes, no paid reviews, the 4-star ones stay.",
        eyebrow="Reviews · Verified",
        body_html=body,
        hero_base="/img/boats/mangusta-80/hero",
        hero_alt="Mangusta 80 yacht cruising past La Concha, Marbella — guest reviews from real charters",
        breadcrumb_name="Reviews",
        extra_jsonld=review_jsonld,
    )

# ------------------ about ------------------
def render_about():
    body = f'''
<p class="byline">Independent operator · Puerto Banús · {date.today().strftime("%-d %B %Y")}</p>

<div class="post-author" style="margin-bottom:20px">
  <img class="post-author-avatar" src="/img/team/andra-kiirkivi-200.jpg" srcset="/img/team/andra-kiirkivi-200.jpg 200w, /img/team/andra-kiirkivi-400.jpg 400w" sizes="56px" width="56" height="56" alt="Andra Kiirkivi — Founder &amp; CEO, Boat Rental Marbella" loading="lazy">
  <div class="post-author-meta">
    <span class="post-author-name"><strong>Andra Kiirkivi</strong></span>
    <span class="post-author-role">Founder &amp; CEO · Boat Rental Marbella</span>
  </div>
</div>

<p>Boat Rental Marbella is an independent boat charter operator based in Puerto Banús. We're not a marketplace and we're not a booking platform — every boat listed on this site is run by skippers we work with directly, every booking goes through Andra's WhatsApp first, and the price you see is the price you pay.</p>

<h2>What we do</h2>
<p>We charter a curated fleet of {FLEET_N} motor yachts, catamarans, jet skis and day boats along the Costa del Sol. Most departures are from <strong>Puerto Banús</strong>, with pickups also available at Marbella Marina, Cabopino, Estepona and Sotogrande. Every skippered charter includes the captain, fuel for a standard coastal cruise, soft drinks + beer + white wine + cava, light snacks, insurance and Spanish IVA.</p>

<h2>Who's running this</h2>
<p>The operator on this site is <strong>Andra Kiirkivi</strong>. Andra splits the year between Marbella and Estonia, has been chartering boats on the Costa del Sol since 2022, and personally handles every WhatsApp inbound. Average reply under 5 minutes during Marbella daytime hours.</p>

<p>The skippers are independent Spanish licence-holders — most have been working Puerto Banús for 8+ years. We don't subcontract through third parties; the boat you see is the boat that picks you up.</p>

<h2>Why we exist</h2>
<p>Marbella charter listings on the big marketplaces (Click&amp;Boat, Samboat, GetMyBoat) are noisy and the per-boat experience varies wildly. We built Boat Rental Marbella to be the opposite: a small, accountable fleet, transparent inclusive pricing, and a single human contact (Andra) who actually replies. If something goes wrong before, during, or after your charter, you message her — not a ticketing system.</p>

<h2>Our fleet</h2>
<p>{FLEET_N}-boat fleet across three tiers:</p>
<ul>
  <li><strong>Day boats &amp; jet skis</strong> — Sea-Doo jet skis from €250 first hour, Dubhe day boat from €230/2h.</li>
  <li><strong>Mid-fleet flybridge yachts</strong> — <a href="/boats/astondoa-40/">Astondoa 40 'Fufi'</a> and <a href="/boats/azimut-39/">Azimut 39</a> at €749/2h → €2,299/8h.</li>
  <li><strong>Flagship</strong> — <a href="/boats/mangusta-80/">Mangusta 80 'Nina'</a>, 24m sport yacht, €4,719 minimum 4h, jet ski included free.</li>
</ul>
<p>Full inventory and live availability via WhatsApp on the <a href="/boats/">fleet page</a>.</p>

<h2>How we work</h2>
<ol>
  <li><strong>You message us</strong> on <a href="{WA_LINK}">WhatsApp</a> with date, group size and any preferences.</li>
  <li><strong>We reply with a quote</strong> within minutes — usually under 5 in business hours.</li>
  <li><strong>You confirm</strong> with a 50% deposit, balance the morning of the charter.</li>
  <li><strong>Skipper picks you up</strong> at Puerto Banús (or the marina you chose).</li>
  <li><strong>Andra messages you the next day</strong> to check the charter went well — that's how we collect <a href="/reviews/">the reviews on this site</a>.</li>
</ol>

<h2>Where to find us</h2>
<ul>
  <li><strong>WhatsApp:</strong> <a href="{WA_LINK}">+358 400 406 194</a> (fastest)</li>
  <li><strong>Email:</strong> <a href="mailto:{SITE['email']}">{SITE['email']}</a></li>
  <li><strong>Instagram:</strong> <a href="{SITE['instagram_url']}" target="_blank" rel="noopener">{SITE['instagram_handle']}</a> — daily updates from the marina</li>
  <li><strong>Facebook:</strong> <a href="{SITE['facebook_url']}" target="_blank" rel="noopener">@BoatRentalMarbella</a></li>
  <li><strong>Marina:</strong> Puerto Banús, Marbella, Spain</li>
</ul>

<p>Ready to book? Tap the <strong>WhatsApp</strong> button at the top right or browse <a href="/boats/">the fleet</a>. Read the <a href="/reviews/">{REVIEWS["aggregate"]["review_count"]} guest reviews</a> first if you want — we keep them all up.</p>
'''
    render_page(
        slug="about",
        title=f"About — {SITE['name']} · Founded by Andra Kiirkivi, Puerto Banús",
        meta="About Boat Rental Marbella — independent boat charter operator in Puerto Banús, founded by Andra Kiirkivi. Direct WhatsApp booking, no intermediaries.",
        h1="About Boat Rental Marbella",
        sub="Independent operator. Curated fleet. One person — Andra — replies to every WhatsApp.",
        eyebrow="About",
        body_html=body,
        hero_base="/img/boats/astondoa-40/sunset",
        hero_alt="Astondoa 40 'Fufi' returning to Puerto Banús at sunset — independent boat charter Marbella",
        breadcrumb_name="About",
    )

# ------------------ contact ------------------
def render_contact():
    body = f'''
<p class="byline">Average WhatsApp reply &lt; 5 minutes · Marbella daytime hours</p>

<h2>WhatsApp (fastest)</h2>
<p>Tap this button — your message lands directly on Andra's phone:</p>
<p><a class="btn btn-primary" href="{WA_LINK}" rel="nofollow noopener">💬 Message on WhatsApp · {SITE['phone_display']}</a></p>

<h2>Phone</h2>
<p><a href="tel:{SITE['phone_e164']}">{SITE['phone_display']}</a> — daily 09:00–22:00 CET. WhatsApp is faster for booking questions because it's always with us.</p>

<h2>Email</h2>
<p><a href="mailto:{SITE['email']}">{SITE['email']}</a> — typical reply within 4 hours. Use email for press, partnerships or invoice/VAT requests; WhatsApp for booking.</p>

<h2>Social</h2>
<ul>
  <li><strong>Instagram</strong> — <a href="{SITE['instagram_url']}" target="_blank" rel="noopener">{SITE['instagram_handle']}</a> — daily charter highlights from Puerto Banús</li>
  <li><strong>Facebook</strong> — <a href="{SITE['facebook_url']}" target="_blank" rel="noopener">{SITE['facebook_label']}</a></li>
</ul>

<h2>Where we charter from</h2>
<ul>
  <li><strong>Puerto Banús, Marbella</strong> (primary marina — most yachts depart here)</li>
  <li>Marbella Marina / Puerto Deportivo Virgen del Carmen (central, walking distance from town)</li>
  <li>Cabopino (east, closest to the dune beaches — licence-free boats live here)</li>
  <li>Estepona &amp; Sotogrande on request</li>
</ul>

<h2>What we don't have</h2>
<p>No customer-service ticketing system. No call centre. No automated chatbot. Andra is the contact and we like it that way.</p>

<h2>Business details</h2>
<ul>
  <li><strong>Trading name:</strong> Boat Rental Marbella</li>
  <li><strong>Locale:</strong> Marbella, Andalucía, Spain · 29602</li>
  <li><strong>Founded:</strong> {SITE.get("founded_year", 2025)}</li>
  <li><strong>VAT:</strong> Spanish IVA (21%) included on every quote</li>
</ul>

<p>If you're researching us before booking, take a look at <a href="/reviews/">{REVIEWS["aggregate"]["review_count"]} verified guest reviews</a>, or read more about who's running this on the <a href="/about/">about page</a>.</p>
'''
    render_page(
        slug="contact",
        title=f"Contact — {SITE['name']} · WhatsApp, Phone, Email, Instagram",
        meta=f"Contact Boat Rental Marbella — WhatsApp {SITE['phone_display']} (reply &lt;5 min), email {SITE['email']}, Instagram {SITE['instagram_handle']}. Puerto Banús, Marbella.",
        h1="Contact Boat Rental Marbella",
        sub=f"WhatsApp {SITE['phone_display']} for fastest reply. Or email, phone, IG, FB — all routes go to Andra.",
        eyebrow="Contact",
        body_html=body,
        hero_base="/img/boats/azimut-39/hero",
        hero_alt="Azimut 39 cruising Marbella — contact for booking",
        breadcrumb_name="Contact",
    )

# ------------------ cancellation policy ------------------
def render_cancellation():
    body = f'''
<p class="byline">Effective 1 May 2026 · Apply to all skippered charters from Puerto Banús, Marbella Marina, Cabopino, Estepona and Sotogrande.</p>

<h2>Summary in one line</h2>
<p>Cancel 7+ days before = full refund. Skipper-cancelled for weather = full refund, always.</p>

<h2>Full schedule</h2>
<table>
  <thead><tr><th>When you cancel</th><th>Refund</th><th>Notes</th></tr></thead>
  <tbody>
    <tr><td>7+ days before charter</td><td><strong>100%</strong></td><td>Full refund, no questions.</td></tr>
    <tr><td>3–6 days before</td><td>50%</td><td>The other 50% covers skipper hold + fuel sourcing.</td></tr>
    <tr><td>48 hours – 3 days</td><td>25%</td><td>Higher because we've usually turned other bookings down.</td></tr>
    <tr><td>Inside 48 hours</td><td>0%</td><td>Booked period is committed.</td></tr>
    <tr><td>Day-of no-show</td><td>0%</td><td>Skipper waited at the dock.</td></tr>
  </tbody>
</table>

<h2>Weather cancellations</h2>
<p>If the skipper cancels the charter because of wind, sea state or thunderstorm risk, you always get a <strong>100% refund</strong> or a free reschedule to a date of your choice. The call is made the evening before based on Windguru / AEMET forecasts. Light rain alone is not a cancellation reason on the Costa del Sol — drizzle clears within minutes, the sea is usually flat.</p>

<h2>How to cancel</h2>
<p>Message Andra on <a href="{WA_LINK}">WhatsApp</a> with your booking date. Refunds are processed back to the original payment method within 3–7 business days.</p>

<h2>Rescheduling vs cancelling</h2>
<p>Rescheduling is always free if we can find a new date in the same season. If the new date is in a different season (e.g. December → August), the new-season price applies — we'll show you the difference before you confirm.</p>

<h2>Add-ons and catering</h2>
<p>Add-ons booked separately (catered lunch, photographer, custom decoration) follow the catering provider's own cancellation terms — we forward 100% of what we collect, no markup. We'll always show you those terms when you add the line item.</p>

<h2>Force majeure</h2>
<p>If the charter is impossible because of events outside our control (port closure, government health order, harbour-wide emergency), you get a 100% refund regardless of how close to the date.</p>

<h2>Travel insurance</h2>
<p>We recommend buying travel insurance with cruise / charter cover for any booking over €1,500. Standard travel insurance often excludes private yacht charter — read your policy.</p>

<p>Questions? Message <a href="{WA_LINK}">Andra on WhatsApp</a> or email <a href="mailto:{SITE['email']}">{SITE['email']}</a>.</p>
'''
    render_page(
        slug="cancellation-policy",
        title=f"Cancellation Policy — {SITE['name']}",
        meta="Cancellation policy for Boat Rental Marbella charters: 100% refund 7+ days before, weather cancellations always refundable, transparent sliding scale.",
        h1="Cancellation Policy",
        sub="Transparent refund schedule. Weather cancellations always 100%. No tricks.",
        eyebrow="Cancellation Policy",
        body_html=body,
        hero_base="/img/boats/azimut-39/hero",
        hero_alt="Azimut 39 charter Marbella — cancellation policy",
        breadcrumb_name="Cancellation Policy",
    )

# ------------------ cookies ------------------
def render_cookies():
    body = f'''
<p class="byline">Effective {date.today().strftime("%-d %B %Y")} · GDPR-compliant · Last updated {date.today().strftime("%-d %B %Y")}.</p>

<h2>The short version</h2>
<p>This site uses one analytics cookie (Google Analytics 4, GA4) and standard browser-essential cookies. We don't sell your data, we don't run ad-network retargeting, and we don't use cookies for advertising profiles. WhatsApp / Facebook share buttons set their own cookies only if you click them.</p>

<h2>Cookies set when you visit</h2>
<table>
  <thead><tr><th>Cookie</th><th>Set by</th><th>Purpose</th><th>Duration</th></tr></thead>
  <tbody>
    <tr><td><code>_ga</code></td><td>Google Analytics</td><td>Distinguishes unique visitors (anonymised)</td><td>2 years</td></tr>
    <tr><td><code>_ga_VKSPCFYHEY</code></td><td>Google Analytics</td><td>Session state for this property</td><td>2 years</td></tr>
    <tr><td><code>_gid</code></td><td>Google Analytics</td><td>Distinguishes unique visitors over 24 h</td><td>24 hours</td></tr>
  </tbody>
</table>

<h2>Third-party services we embed</h2>
<ul>
  <li><strong>Google Analytics 4</strong> — usage analytics. IP-anonymised. <a href="https://policies.google.com/privacy" target="_blank" rel="noopener">Google privacy policy</a>.</li>
  <li><strong>Google Fonts</strong> — none currently loaded; site fonts are system fonts.</li>
  <li><strong>Google Maps embed</strong> — if you scroll to a page with an embedded map. <a href="https://policies.google.com/privacy" target="_blank" rel="noopener">Google privacy policy</a>.</li>
  <li><strong>WhatsApp click-to-chat</strong> — when you tap a WhatsApp button. <a href="https://www.whatsapp.com/legal/privacy-policy" target="_blank" rel="noopener">WhatsApp privacy policy</a>.</li>
</ul>

<h2>What we don't use</h2>
<ul>
  <li>No Meta Pixel / Facebook Pixel</li>
  <li>No TikTok pixel</li>
  <li>No Google Ads retargeting</li>
  <li>No third-party advertising</li>
  <li>No chat widgets (we use WhatsApp deep-link, not embedded chat)</li>
</ul>

<h2>How to opt out</h2>
<ul>
  <li><strong>Browser-level:</strong> use private/incognito mode, or block third-party cookies in your browser settings.</li>
  <li><strong>Google Analytics opt-out:</strong> install Google's <a href="https://tools.google.com/dlpage/gaoptout" target="_blank" rel="noopener">official browser opt-out</a>.</li>
  <li><strong>Right to deletion (GDPR):</strong> email <a href="mailto:{SITE['email']}">{SITE['email']}</a> from the address you've been using — we'll delete any record of your contact within 30 days.</li>
</ul>

<h2>Data we store from bookings</h2>
<p>If you book a charter, we keep your name, WhatsApp number, charter date and any preferences you sent us. This data lives on Andra's phone and laptop only — no CRM, no third-party share, no ad-targeting. We keep it for 5 years for Spanish tax/invoice purposes, then delete it.</p>

<h2>Updates to this policy</h2>
<p>If we materially change anything, we'll bump the "Effective" date at the top and publish a note on the <a href="/blog/">blog</a>. Last updated {date.today().strftime("%-d %B %Y")}.</p>

<p>Questions? Message <a href="{WA_LINK}">Andra on WhatsApp</a> or email <a href="mailto:{SITE['email']}">{SITE['email']}</a>.</p>
'''
    render_page(
        slug="cookies",
        title=f"Cookie Policy — {SITE['name']}",
        meta="Cookie policy for boatrentalinmarbella.com — GA4 analytics only, no ad pixels, no retargeting, no third-party advertising. GDPR-compliant.",
        h1="Cookie Policy",
        sub="GA4 analytics only. No ad pixels. No retargeting. No tracking sale.",
        eyebrow="Cookies",
        body_html=body,
        hero_base="/img/boats/astondoa-40/hero",
        hero_alt="Astondoa 40 charter Marbella — cookie policy",
        breadcrumb_name="Cookie Policy",
    )

def main():
    print("=== trust + legal pages ===")
    render_reviews()
    render_about()
    render_contact()
    render_cancellation()
    render_cookies()

if __name__ == "__main__":
    main()
