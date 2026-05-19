#!/usr/bin/env python3
"""Build the /experiences/ hub + per-experience landing pages.

Each experience either links out to an existing spoke (boat-party, sunset, fishing, jet-ski) or
to a dedicated /experiences/<slug>/ landing page. Run via deploy.sh.
"""
from __future__ import annotations
import json, pathlib, html
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "templates" / "page.html.template").read_text()
CONFIG = json.loads((ROOT / "config" / "keyword_map.json").read_text())
SITE = CONFIG["site"]
SITE_DIR = ROOT / "site"

def jsonld_org():
    return {
        "@context":"https://schema.org","@type":["LocalBusiness","Organization"],
        "@id":SITE['base_url']+"/#org","name":SITE['name'],
        "url":SITE['base_url']+"/","logo":SITE['base_url']+"/og-image.jpg",
        "telephone":SITE['phone_e164'],"email":SITE['email'],
        "areaServed":SITE['departure_ports'],
        "sameAs":[u for u in [SITE.get('instagram_url'), SITE.get('facebook_url')] if u],
        "priceRange":f"€{SITE['price_anchor_low_2h']}–€{SITE['price_anchor_fullday_8h']}",
        "address":{"@type":"PostalAddress","addressLocality":"Marbella","addressRegion":"Andalucía","postalCode":"29602","addressCountry":"ES"},
        "geo":{"@type":"GeoCoordinates","latitude":SITE['geo_lat'],"longitude":SITE['geo_lng']},
        "foundingDate":str(SITE.get('founded_year',2025)),
    }

# Experience catalogue — each card on the hub
EXPERIENCES = [
    {"slug":"/boat-party-marbella/", "title":"Onboard Parties", "desc":"Stag, hen, birthday & group charters with BYO welcomed, DJ add-on, ice tubs.", "image":"/img/boats/mangusta-80/aerial-wake", "widths":(400,600,900), "tag":"Most popular", "from":749},
    {"slug":"/experiences/bachelor-hen-parties-marbella/", "title":"Bachelor & Hen Parties", "desc":"The full Marbella weekend script — yacht morning, beach-club tender, dinner ashore.", "image":"/img/customers/h02", "widths":(400,600,900), "tag":"Groups 9-12", "from":749, "external":False},
    {"slug":"/sunset-cruise-marbella/", "title":"Romantic Escapes", "desc":"Sunset cruises, anniversaries, proposals — under La Concha as the lights come on.", "image":"/img/boats/astondoa-40/sunset", "widths":(600,900,1200), "tag":"Couples", "from":749},
    {"slug":"/experiences/family-boat-days-marbella/", "title":"Family Boat Days", "desc":"Calm-water itineraries, snorkel stops, snacks pre-loaded for under-12s.", "image":"/img/boats/astondoa-40/hero", "widths":(600,900,1200), "tag":"Kids friendly", "from":749},
    {"slug":"/fishing-boat-rental-marbella/", "title":"Fishing Trips", "desc":"Inshore reef fishing on our fleet — light tackle, dorado in summer, amberjack year-round.", "image":"/img/boats/astondoa-40/lifestyle", "widths":(600,900,1200), "tag":"", "from":749},
    {"slug":"/experiences/photoshoot-yacht-marbella/", "title":"Photoshoot on a Yacht", "desc":"Influencer, fashion or wedding photos on the bow with Marbella's mountains behind.", "image":"/img/boats/mangusta-80/sun-pad", "widths":(600,900,1200), "tag":"Content day", "from":749},
    {"slug":"/jet-ski-rental-marbella/", "title":"Jet Ski Experience", "desc":"Sea-Doo from Puerto Banús — solo or two-up, briefing included, no licence needed.", "image":"/img/jet-ski/hero", "widths":(600,900,1200), "tag":"Adrenaline", "from":200},
    {"slug":"/blog/dolphin-watching-marbella/", "title":"Dolphin Watching", "desc":"4-hour offshore charter — bottlenose, common & striped dolphin pods 2–8 NM out.", "image":"/img/boats/mangusta-80/aerial-wake", "widths":(600,900,1200), "tag":"Wildlife", "from":749},
    {"slug":"/blog/gibraltar-day-trip-by-boat/", "title":"Gibraltar Day Trip", "desc":"95 NM round trip from Puerto Banús past Sotogrande to the Rock and back.", "image":"/img/boats/mangusta-80/profile", "widths":(600,900,1200), "tag":"Adventure", "from":1500},
]

def card_html(exp):
    base = exp["image"]
    widths = exp["widths"]
    srcset = ", ".join(f"{base}-{w}.jpg {w}w" for w in widths)
    src = f"{base}-{widths[1]}.jpg"
    tag_html = f'<span class="boat-card-tag">{html.escape(exp["tag"])}</span>' if exp.get("tag") else ''
    return f'''<a href="{exp["slug"]}" class="boat-card">
  <div class="boat-card-img">
    <img src="{src}" srcset="{srcset}" sizes="(max-width: 600px) 100vw, 360px" alt="{html.escape(exp["title"])} — Marbella" loading="lazy" width="600" height="375">
    {tag_html}
  </div>
  <div class="boat-card-body">
    <h3 class="boat-card-title">{html.escape(exp["title"])}</h3>
    <p class="boat-card-desc">{html.escape(exp["desc"])}</p>
    <div class="boat-card-meta">
      <span class="boat-card-price">From <strong>€{exp["from"]}</strong><small>see page</small></span>
      <span class="boat-card-cta">Explore →</span>
    </div>
  </div>
</a>'''

# ---------- shared writer ----------
def write_page(slug, *, title, meta, h1, sub, eyebrow, body_html_str, jsonld, breadcrumbs, hero_base, hero_widths, hero_alt):
    url = f"{SITE['base_url']}/{slug}/"
    hero_src = f"{hero_base}-{hero_widths[-1]}.jpg"
    hero_srcset = ", ".join(f"{hero_base}-{w}.jpg {w}w" for w in hero_widths)
    repl = {
        "{{HREFLANG}}": "",
        "{{HERO_IMG}}": hero_src,
        "{{HERO_SRCSET}}": html.escape(hero_srcset),
        "{{HERO_ALT}}": html.escape(hero_alt),
        "{{HERO_EYEBROW}}": f'<span class="eyebrow">{html.escape(eyebrow)}</span>',
        "{{HERO_H1}}": html.escape(h1),
        "{{HERO_SUB}}": html.escape(sub),
        "{{TITLE}}": html.escape(title),
        "{{META_DESCRIPTION}}": html.escape(meta),
        "{{CANONICAL_URL}}": url,
        "{{OG_TYPE}}": "website",
        "{{CSS_HREF}}": "/styles.css",
        "{{JSONLD}}": json.dumps(jsonld, ensure_ascii=False),
        "{{PRICE_LOW}}": str(SITE['price_anchor_low_2h']),
        "{{PRICE_LABEL}}": "2h skippered charter",
        "{{BOOK_PITCH}}": "Instant quotes from local operators across Puerto Banús, Marbella Marina, Cabopino, Estepona &amp; Sotogrande.",
        "{{BOAT_GRID}}": "",
        "{{BREADCRUMBS}}": breadcrumbs,
        "{{BODY_HTML}}": body_html_str,
        "{{VIDEO_SECTION}}": "",
        "{{GUESTS_SECTION}}": "",
        "{{WHATSAPP_E164_NOPLUS}}": SITE['whatsapp_e164'].lstrip("+"),
        "{{PHONE_E164}}": SITE['phone_e164'],
        "{{PHONE_DISPLAY}}": SITE['phone_display'],
        "{{EMAIL}}": SITE['email'],
        "{{AFFILIATE_LINK}}": SITE['affiliate_link'],
        "{{INSTAGRAM_URL}}": SITE.get('instagram_url',''),
        "{{INSTAGRAM_HANDLE}}": SITE.get('instagram_handle',''),
        "{{FACEBOOK_URL}}": SITE.get('facebook_url',''),
        "{{FACEBOOK_LABEL}}": SITE.get('facebook_label','Facebook'),
    }
    out = TEMPLATE
    for k, v in repl.items():
        out = out.replace(k, v)
    out_path = SITE_DIR / slug / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out)

# ---------- /experiences/ hub ----------
def render_hub():
    cards = "\n".join(card_html(e) for e in EXPERIENCES)
    body = f'''<p class="byline">{len(EXPERIENCES)} experiences · Real charters, real boats from Puerto Banús</p>

<p>Marbella isn't one experience — it's many. Sunset cruises for couples, hen-party flybridges for groups of 11, fishing trips for the dads, dolphin offshore runs, day-long Gibraltar adventures. This page is the catalogue: every type of charter we run, with a price-from and a direct link to the relevant booking page.</p>

<section class="boat-grid-section" style="background:transparent;padding:24px 0 0">
  <div class="boat-grid" style="padding:0">
{cards}
  </div>
</section>

<h2>Which experience fits your group?</h2>
<ul>
  <li><strong>Couples 2:</strong> <a href="/sunset-cruise-marbella/">Sunset cruise</a> or proposal-on-a-yacht — €749 / 2 h.</li>
  <li><strong>Family with kids:</strong> <a href="/experiences/family-boat-days-marbella/">Family boat day</a> — calm-water itinerary, snacks pre-loaded, life jackets in every size.</li>
  <li><strong>Group 6–8:</strong> <a href="/boats/astondoa-40/">Astondoa 40 "Fufi"</a> day charter from €1,299 / 4 h.</li>
  <li><strong>Group 9–11 (stag/hen):</strong> <a href="/boats/azimut-39/">Azimut 39</a> flybridge, BYO welcomed, DJ add-on.</li>
  <li><strong>Group 10–12 in luxury:</strong> <a href="/boats/mangusta-80/">Mangusta 80</a> superyacht with Sea-Doo jet ski free — €4,719 / 4 h.</li>
  <li><strong>Adrenaline / solo:</strong> <a href="/jet-ski-rental-marbella/">Sea-Doo jet ski</a> at €200 / h.</li>
  <li><strong>Content creators / brands:</strong> <a href="/experiences/photoshoot-yacht-marbella/">Photoshoot day</a> — La Concha backdrop, sun-pad-ready angles.</li>
</ul>

<h2>How booking works</h2>
<ol>
  <li><strong>Browse experiences</strong> on this page or directly via <a href="/boats/">Our Boats</a>.</li>
  <li><strong>Tap "Book now"</strong> (top-right) — drops your name, WhatsApp and budget into our chat.</li>
  <li><strong>We reply in under 5 minutes</strong> with 2–3 specific boat options and the exact total.</li>
  <li><strong>30% deposit secures the date</strong> — balance the morning of the charter.</li>
  <li><strong>Show up at Puerto Banús</strong> 15 min before departure with photo ID. We'll have everything else.</li>
</ol>

<p>Not sure which experience? Just message us with "I'm in Marbella from {date.today().strftime("%-d %B")} for 3 days, what would you suggest?" — we'll send back 2–3 charter ideas tailored to your group, dates and budget.</p>'''

    jsonld = [
        jsonld_org(),
        {
            "@context":"https://schema.org","@type":"CollectionPage",
            "name":"Marbella Boat Charter Experiences","url":SITE['base_url']+"/experiences/",
            "description":"Catalogue of charter experiences on our Marbella fleet — sunset, fishing, parties, family days, dolphin watching and more.",
            "isPartOf":{"@id":SITE['base_url']+"/#org"},
            "mainEntity":{
                "@type":"ItemList","numberOfItems":len(EXPERIENCES),
                "itemListElement":[
                    {"@type":"ListItem","position":i+1,"url":SITE['base_url']+e["slug"],"name":e["title"]}
                    for i, e in enumerate(EXPERIENCES)
                ],
            },
        },
        {
            "@context":"https://schema.org","@type":"BreadcrumbList",
            "itemListElement":[
                {"@type":"ListItem","position":1,"name":"Home","item":SITE['base_url']+"/"},
                {"@type":"ListItem","position":2,"name":"Experiences","item":SITE['base_url']+"/experiences/"},
            ],
        },
    ]

    write_page(
        slug="experiences",
        title="Marbella Boat Charter Experiences: Parties, Sunset, Family, Fishing & More",
        meta="9 boat charter experiences in Marbella — sunset cruises, hen parties, family days, fishing, photoshoots, dolphin watching, Gibraltar day trips. Our fleet, our skippers, from €200.",
        h1="Marbella Boat Charter Experiences",
        sub="Sunset cruises, hen-party flybridges, family boat days, photoshoots, fishing trips, Gibraltar adventures — every Marbella charter type, with prices and direct booking.",
        eyebrow="Experiences · Marbella",
        body_html_str=body,
        jsonld=jsonld,
        breadcrumbs='<nav class="breadcrumbs"><a href="/">Home</a> › <span>Experiences</span></nav>',
        hero_base="/img/boats/mangusta-80/sun-pad",
        hero_widths=(600,900,1200),
        hero_alt="Marbella boat charter experiences — sun pad on the Mangusta 80",
    )
    print(f"  ✓ experiences hub → /experiences/")


# ---------- /experiences/family-boat-days-marbella/ ----------
def render_family():
    body = f'''<p>A family boat day in Marbella is its own type of charter — different boat choice, different itinerary, different pace from a stag-party flybridge or a sunset cruise for two. This page is the practical playbook: which of our boats works best for kids, what we pre-load on board, and where to anchor for the calmest snorkel of the day.</p>

<figure class="inline-img"><img src="/img/customers/h06-1200.jpg" srcset="/img/customers/h06-600.jpg 600w, /img/customers/h06-900.jpg 900w, /img/customers/h06-1200.jpg 1200w" sizes="(max-width: 880px) 100vw, 720px" alt="Family on board a Marbella charter yacht with kids" loading="lazy" width="1200" height="800"></figure>

<h2>Which boat for a family day?</h2>
<table>
<thead><tr><th>Family size</th><th>Boat we recommend</th><th>Why</th></tr></thead>
<tbody>
<tr><td>2 adults + 1–2 kids</td><td><a href="/boats/astondoa-40/">Astondoa 40</a></td><td>Spanish-built, classic teak interior, AC saloon, cabin for naps, gentle ride.</td></tr>
<tr><td>2 adults + 3–4 kids</td><td><a href="/boats/azimut-39/">Azimut 39</a></td><td>Flybridge upstairs for the kids, AC saloon downstairs, marine head with shower.</td></tr>
<tr><td>3+ families together (10–12 guests)</td><td><a href="/boats/mangusta-80/">Mangusta 80</a></td><td>24 m of deck space — kids have their own zone, adults have theirs, jet ski included.</td></tr>
</tbody>
</table>

<h2>What's already on board for kids</h2>
<ul>
<li><strong>Life jackets in every size</strong> — infant (under 12 kg), child (12–25 kg), youth (25–40 kg), adult. Spanish maritime law requires under-12s wear them while underway; we provide.</li>
<li><strong>Snorkel masks &amp; fins</strong> in junior sizes.</li>
<li><strong>Inflatable donut + paddleboard</strong> for anchor stops.</li>
<li><strong>Bimini shade</strong> covering the cockpit (we keep kids out of direct midday sun).</li>
<li><strong>AC interior</strong> as a refuge from the heat on full-day charters.</li>
<li><strong>Marine head with shower</strong> — proper toilet, not a Porta-Potti, with running water.</li>
</ul>

<h2>What we pre-load if you ask 24 hours ahead</h2>
<ul>
<li>Fresh fruit (banana, apple, watermelon, grapes)</li>
<li>Crisps and biscuits the kids actually like (tell us brands if it matters)</li>
<li>Juice boxes (apple, orange, no high-sugar Capri-Suns by default — we go neutral)</li>
<li>Ice lollies for older kids — kept in the freezer until you ask</li>
<li>Sandwiches if you want a no-fuss lunch (€8 per child for a ham &amp; cheese + fruit + lolly box)</li>
</ul>

<h2>The calm-water itinerary (under-5s)</h2>
<ol>
<li><strong>10:00</strong> Boarding at Puerto Banús — calmer mouth in the morning, less queue.</li>
<li><strong>10:30</strong> Slow cruise east 25 min to anchor off Cabopino dunes — sandy bottom, gentle slope, sheltered from the levante.</li>
<li><strong>11:00–12:30</strong> Swim and snorkel stop. Donut launched. Kids can walk waist-deep on the sand bar.</li>
<li><strong>12:30</strong> Light lunch on board.</li>
<li><strong>13:00–13:30</strong> Naps in the cabin if needed.</li>
<li><strong>13:30</strong> Cruise back to Puerto Banús — return by 14:00, well within attention span.</li>
</ol>
<p>Total: 4 hours, €1,299. Easy half-day even with very young children.</p>

<h2>Snorkel stops worth the trip</h2>
<ul>
<li><strong>Cala Cortés (east of Cabopino)</strong> — small protected cove, 3–5 m depth, sea bream and small wrasse. Easy snorkel for 6+ year-olds.</li>
<li><strong>Río Real</strong> — sandy bottom with occasional octopus spotting near the rocks. Suits all ages.</li>
<li><strong>Cala del Faro (west of Estepona)</strong> — rockier, deeper. Better for confident swimmers 9+.</li>
</ul>

<h2>Safety basics that come up</h2>
<ul>
<li><strong>UV doubles at sea</strong> — reflection off the water. UPF 50 rash vest + hat + 50+ sunscreen is non-negotiable.</li>
<li><strong>Engine zone is off-limits</strong> while running — skipper will brief the kids in 30 seconds before departure.</li>
<li><strong>Bare feet on deck</strong> — better grip than any shoe on wet teak.</li>
<li><strong>Marine life</strong> — Marbella waters are benign. No jellyfish bloom most years, no aggressive fish. Watch for sea urchins at rocky entries (Cabopino dunes is sandy so safe).</li>
</ul>

<h2>How to book a family day</h2>
<p>Tap <strong>Book now</strong> top-right — tell us how many adults + kids, ages of the kids, your date and rough budget. We reply with 2–3 specific boats and the exact total. 30% deposit secures the date, balance the morning of the charter. Free cancellation up to 7 days out; weather cancellations 100% refunded.</p>

<p>For the full guide on charting with kids in Marbella (life-jacket rules, packing list, things that go wrong), see our <a href="/blog/kids-on-a-boat-marbella/">kids on a boat in Marbella</a> blog post.</p>

<h2>Frequently asked questions</h2>
<details><summary>What's the minimum age for a family charter?</summary><p>No legal minimum, but operators recommend 6 months and above. Babies under 6 months struggle with the sun and motion on most boats. From 1 year up, with the right boat and a short morning itinerary, kids do brilliantly.</p></details>
<details><summary>Do you provide life jackets for kids?</summary><p>Yes, in every size — infant (under 12 kg), child (12–25 kg), youth (25–40 kg), and adult. Spanish maritime law requires under-12s wear them while underway. Mention any unusual sizing when booking.</p></details>
<details><summary>Can we bring our own food?</summary><p>Yes — BYO welcomed for snacks, sandwiches, fruit. We also pre-load on request with 24 h notice. Catered lunches (paella, sushi platter, hot meals) are €25–€60 per head.</p></details>
<details><summary>How long can young kids cope on a boat?</summary><p>Under-3s: 2–3 hours total. 4–7s: 3–4 hours comfortably (longer with naps in the cabin). 8+: full day works if there's a swim stop and snacks. Build in shade — bimini covers the cockpit, but the foredeck is sun-exposed.</p></details>
<details><summary>What if the kids get seasick?</summary><p>Mention it when booking and the skipper picks a calm-water route (Marbella Marina to Cabopino in the morning is virtually flat). Ginger biscuits help. If symptoms appear, we anchor in the calmest spot immediately. Catamarans and motor yachts both have flat-deck stability that minimises motion.</p></details>'''

    jsonld = [
        jsonld_org(),
        {
            "@context":"https://schema.org","@type":"Service",
            "name":"Family Boat Day Marbella",
            "url":SITE['base_url']+"/experiences/family-boat-days-marbella/",
            "provider":{"@id":SITE['base_url']+"/#org"},
            "areaServed":"Marbella, Spain",
            "audience":{"@type":"PeopleAudience","name":"Families with children"},
            "offers":{"@type":"AggregateOffer","priceCurrency":"EUR","lowPrice":SITE['price_anchor_low_2h'],"highPrice":SITE['price_anchor_fullday_8h']},
        },
        {
            "@context":"https://schema.org","@type":"BreadcrumbList",
            "itemListElement":[
                {"@type":"ListItem","position":1,"name":"Home","item":SITE['base_url']+"/"},
                {"@type":"ListItem","position":2,"name":"Experiences","item":SITE['base_url']+"/experiences/"},
                {"@type":"ListItem","position":3,"name":"Family Boat Days","item":SITE['base_url']+"/experiences/family-boat-days-marbella/"},
            ],
        },
    ]

    write_page(
        slug="experiences/family-boat-days-marbella",
        title="Family Boat Days in Marbella: Kids, Snorkel & Calm-Water Itineraries",
        meta="Family boat charter Marbella from €749 — calm-water routes, snorkel stops at Cabopino & Cala Cortés, life jackets in every size, snacks pre-loaded. Astondoa 40 & Azimut 39.",
        h1="Family Boat Days in Marbella",
        sub="Calm-water itineraries, snorkel stops, snacks pre-loaded for the kids — Astondoa 40, Azimut 39 or Mangusta 80 depending on your group.",
        eyebrow="Family · Marbella",
        body_html_str=body,
        jsonld=jsonld,
        breadcrumbs='<nav class="breadcrumbs"><a href="/">Home</a> › <a href="/experiences/">Experiences</a> › <span>Family Boat Days</span></nav>',
        hero_base="/img/boats/astondoa-40/hero",
        hero_widths=(600,900,1200,1600),
        hero_alt="Family boat day in Marbella — Astondoa 40 charter for families with kids",
    )
    print("  ✓ /experiences/family-boat-days-marbella/")


# ---------- /experiences/photoshoot-yacht-marbella/ ----------
def render_photoshoot():
    body = f'''<p>A yacht photoshoot in Marbella is its own kind of charter — different goals from a sunset cruise or a stag party. Models or photographers want light angles, deck space, backdrop options. This page is the practical guide: which boat shoots best, what time of day works, where to anchor for the iconic La Concha shot, and how to coordinate hair / makeup / outfit changes on board.</p>

<figure class="inline-img"><img src="/img/customers/h04-1200.jpg" srcset="/img/customers/h04-600.jpg 600w, /img/customers/h04-900.jpg 900w" sizes="(max-width: 880px) 100vw, 720px" alt="Photoshoot on a Marbella yacht — guest at the helm in a white dress" loading="lazy" width="1200" height="800"></figure>

<h2>Best boat for a photoshoot</h2>
<table>
<thead><tr><th>Shoot type</th><th>Boat we recommend</th><th>Why</th></tr></thead>
<tbody>
<tr><td>Single model / influencer reels</td><td><a href="/boats/astondoa-40/">Astondoa 40 "Fufi"</a></td><td>Teak detailing, cream leather, Spanish flag — Mediterranean aesthetic. €749 / 2 h.</td></tr>
<tr><td>Fashion shoot, multiple looks</td><td><a href="/boats/azimut-39/">Azimut 39</a></td><td>Two cabins for changing, AC saloon for hair / makeup, real flybridge with second background option.</td></tr>
<tr><td>Brand campaign, lifestyle / luxury</td><td><a href="/boats/mangusta-80/">Mangusta 80 "Nina"</a></td><td>24 m of deck = unlimited angles. Sun-pad foredeck, marble galley, separate aft seating, jet ski for action shots. €4,719 / 4 h.</td></tr>
</tbody>
</table>

<h2>The 5 iconic Marbella backdrop angles</h2>
<ol>
<li><strong>La Concha mountain</strong> — the most recognizable Marbella backdrop. Anchor anywhere between Puerto Banús and Marbella Marina, shoot with the boat oriented so the mountain is to the model's right shoulder. Best 10:00–12:00 when the mountain is in full sun.</li>
<li><strong>Puerto Banús superyacht line</strong> — exit the marina, then circle back so the 50 m+ yachts are behind. Shoot from the bow looking back. Best at the start or end of the charter.</li>
<li><strong>Open Mediterranean with no land visible</strong> — perfect for "no horizon line" pre-set looks. Anchor 2 NM offshore (calm-water mornings).</li>
<li><strong>Golden hour Golden Mile</strong> — last 90 min before sunset. Boat positioned 200 m off the coast, low sun behind the model, Marbella Club and Puente Romano in the background.</li>
<li><strong>Sea-Doo action</strong> — for adrenaline brand shoots. The skipper drives a chase boat alongside the jet ski. Mangusta 80 charter includes the Sea-Doo free.</li>
</ol>

<h2>Light timing</h2>
<p>Marbella sits 36.5°N. In peak summer the sun crosses overhead between 13:30 and 14:30 — harsh light, hard shadows. Avoid this window if you want soft, cinematic footage. Best windows:</p>
<ul>
<li><strong>09:00–11:00</strong> — soft light, calmer sea, fewer boats on the water. Best for editorial / fashion.</li>
<li><strong>16:00–18:00</strong> — warmer tones, the levante usually drops in the afternoon. Best for lifestyle / drone shots.</li>
<li><strong>19:00–21:00 (Jun–Sep)</strong> — golden hour and blue hour. Best for romantic / aspirational stills.</li>
</ul>
<p>For sunset specifically, see our <a href="/sunset-cruise-marbella/">sunset cruise page</a> — same windows apply.</p>

<h2>What we set up for the shoot</h2>
<ul>
<li><strong>The boat without our branding visible</strong> — no signage, no Fufi-emblazoned towels in the frame unless you want them.</li>
<li><strong>Tidy deck</strong> — fenders stowed, lines coiled, no operational clutter visible to the camera.</li>
<li><strong>Power outlets</strong> — for charging cameras, hair tools, ring lights. 220 V Spanish sockets on board.</li>
<li><strong>Mirror &amp; AC interior</strong> — saloon doubles as a makeup room.</li>
<li><strong>Towels / robes for between shots</strong> — water and wind dry hair fast.</li>
<li><strong>Drone-friendly skipper</strong> — comfortable manoeuvring for top-down drone passes if you've brought a pilot.</li>
</ul>

<h2>Drone footage from the boat</h2>
<p>Spain allows commercial drone flying with a registered Spanish operator (AESA-registered, with insurance). Casual recreational flying from a charter is grey-zone — fine if you stay under 120 m, line of sight, away from marinas. We can't fly a drone for you but we can position the boat for drone passes if you've brought your own pilot. For best top-down sun-pad shots, anchor offshore in flat water around 11:00 — the boat is stationary, no wake, easy framing.</p>

<h2>Wardrobe + makeup logistics</h2>
<p>The Mangusta 80 has the most space for outfit changes — three cabins, separate heads, marble countertop in the galley for makeup. The Astondoa 40 has one master cabin + a guest cabin (enough for 2 looks). The Azimut 39 has two cabins (enough for 3-4 looks). Bring outfits on hangers (not folded) — there's a small wardrobe in each cabin.</p>

<h2>Booking and pricing</h2>
<p>Same prices as a regular charter — no "photoshoot upcharge". The €749 / 2 h Astondoa or Azimut works for influencer reels. The €4,719 / 4 h Mangusta works for fashion campaigns or brand shoots where you need real luxury aesthetic. Half-day or full-day rates available — see <a href="/boats/">our boats</a> for the full grid.</p>

<p>Tap <strong>Book now</strong> top-right and tell us your shoot type, dates, and any specific shots you want (e.g. "La Concha sunset", "drone top-down on sun-pad", "Sea-Doo action"). We'll match the right boat and time of day.</p>

<h2>Frequently asked questions</h2>
<details><summary>Can you remove your branding from the boat for the shoot?</summary><p>Yes. The boat name on the stern is permanent (we can't repaint), but we'll stow any "Boat Rental Marbella" towels, banners or branded items. The boat looks like a private yacht in the photos.</p></details>
<details><summary>Can the skipper drive the boat for action shots?</summary><p>Yes — fast cruising, tight turns for wake shots, anchoring in specific spots. Just brief the skipper before departure. We won't do anything that creates a real safety hazard (we don't do dangerously close passes between boats).</p></details>
<details><summary>Do you provide a photographer?</summary><p>No — bring your own. We can recommend Marbella-based photographers we've worked with if you ask. The boat plus skipper plus drinks plus deck space is what we provide.</p></details>
<details><summary>What about hair and makeup on board?</summary><p>The AC saloon doubles as a hair / makeup space. Bring your own tools — there's 220 V power. For a full HMUA team on board, book the Mangusta 80 (more space) or arrive at the dock already prepped.</p></details>
<details><summary>Can we shoot at sunset?</summary><p>Yes — the 2-hour sunset slot (departing 75 min before official sunset) is one of our most popular shoots. Same €749 price as any 2 h charter. Read more on <a href="/sunset-cruise-marbella/">sunset cruise Marbella</a>.</p></details>'''

    jsonld = [
        jsonld_org(),
        {
            "@context":"https://schema.org","@type":"Service",
            "name":"Yacht Photoshoot Marbella",
            "url":SITE['base_url']+"/experiences/photoshoot-yacht-marbella/",
            "provider":{"@id":SITE['base_url']+"/#org"},
            "areaServed":"Marbella, Spain",
            "audience":{"@type":"PeopleAudience","name":"Photographers, influencers, brands"},
            "offers":{"@type":"AggregateOffer","priceCurrency":"EUR","lowPrice":SITE['price_anchor_low_2h'],"highPrice":SITE['price_anchor_fullday_8h']},
        },
        {
            "@context":"https://schema.org","@type":"BreadcrumbList",
            "itemListElement":[
                {"@type":"ListItem","position":1,"name":"Home","item":SITE['base_url']+"/"},
                {"@type":"ListItem","position":2,"name":"Experiences","item":SITE['base_url']+"/experiences/"},
                {"@type":"ListItem","position":3,"name":"Photoshoot on a Yacht","item":SITE['base_url']+"/experiences/photoshoot-yacht-marbella/"},
            ],
        },
    ]

    write_page(
        slug="experiences/photoshoot-yacht-marbella",
        title="Photoshoot on a Yacht in Marbella: Light, Angles, Backdrops",
        meta="Marbella yacht photoshoot from €749 — Astondoa 40, Azimut 39 or Mangusta 80 superyacht. La Concha mountain backdrop, golden-hour windows, drone-friendly skippers, AC interior for changes.",
        h1="Photoshoot on a Yacht in Marbella",
        sub="The iconic La Concha backdrop, golden-hour windows, drone-friendly skippers — and an AC saloon doubling as a hair / makeup room.",
        eyebrow="Photoshoot · Marbella",
        body_html_str=body,
        jsonld=jsonld,
        breadcrumbs='<nav class="breadcrumbs"><a href="/">Home</a> › <a href="/experiences/">Experiences</a> › <span>Photoshoot on a Yacht</span></nav>',
        hero_base="/img/boats/mangusta-80/sun-pad",
        hero_widths=(600,900,1200),
        hero_alt="Marbella yacht photoshoot — sun pad on the Mangusta 80",
    )
    print("  ✓ /experiences/photoshoot-yacht-marbella/")


# ---------- /experiences/bachelor-hen-parties-marbella/ ----------
def render_bachelor_hen():
    body = f'''<p>Marbella has a specific Sunday script for bachelor and hen weekends — and the yacht charter is the anchor activity. This page is the practical playbook: which boat fits which group size, the standard 4-hour itinerary that builds the whole day, BYO rules, DJ add-ons, and how to coordinate the beach-club tender so you arrive when the day is already going.</p>

<figure class="inline-img"><img src="/img/customers/h02-1200.jpg" srcset="/img/customers/h02-600.jpg 600w, /img/customers/h02-900.jpg 900w" sizes="(max-width: 880px) 100vw, 720px" alt="Hen party on a Marbella yacht charter" loading="lazy" width="1200" height="800"></figure>

<h2>Best boat for the group size</h2>
<table>
<thead><tr><th>Group</th><th>Boat</th><th>Price (4 h half-day)</th></tr></thead>
<tbody>
<tr><td>6–8 guests</td><td><a href="/boats/astondoa-40/">Astondoa 40</a></td><td>€1,299 — €162 per head</td></tr>
<tr><td>9–11 guests (hen + stag sweet spot)</td><td><a href="/boats/azimut-39/">Azimut 39</a></td><td>€1,299 — €118 per head</td></tr>
<tr><td>10–12 luxury</td><td><a href="/boats/mangusta-80/">Mangusta 80</a></td><td>€4,719 — €393 per head, jet ski included</td></tr>
</tbody>
</table>
<p>For groups over 12 we split into two boats and synchronise itineraries — same price per boat, both arriving at Cabopino together.</p>

<h2>The standard 4-hour script</h2>
<ol>
<li><strong>14:00 — Boarding at Puerto Banús</strong>. Welcome drinks, photos at the pontoon. Ice tubs already chilled.</li>
<li><strong>14:30 — Cast off</strong>. Slow cruise west past Marbella Club and Puente Romano. The Golden Mile mansions are part of the show.</li>
<li><strong>15:15 — Anchor stop at Río Verde</strong>. Swim, donut, paddleboard. Music up. This is where the day actually starts.</li>
<li><strong>16:30 — Optional beach-club tender</strong> to Nikki Beach or Ocean Club. You spend 90 min ashore, pay entry separately (€50–€150 minimum spend per head), then we collect you. Or skip and continue east to Cabopino.</li>
<li><strong>17:30 — Return cruise to Puerto Banús</strong>. Slow lap of the harbour mouth for photos.</li>
<li><strong>18:00 — Disembark</strong>. Taxis or walk to dinner at Antonio's or Tikitano.</li>
</ol>

<h2>What's included vs paid extras</h2>
<p><strong>Included in the €749 / €1,299 / €4,719 price:</strong> licensed skipper, fuel, water, soft drinks, beer, white wine, cava, light snacks (crisps, almonds, fruit), insurance, VAT, ice tubs, snorkel masks, inflatable donut and paddleboard, Bluetooth sound system.</p>
<p><strong>Common paid extras:</strong></p>
<ul>
<li><strong>Pro DJ + speaker system upgrade</strong> — €350 half-day, €600 full day.</li>
<li><strong>Live saxophonist on the boat</strong> — €400–€600.</li>
<li><strong>Catered platters</strong> (sushi, charcuterie, paella) — €25–€80 per head, 24 h notice.</li>
<li><strong>Premium spirits</strong> — bring your own (cava is included; vodka, tequila, gin are BYO).</li>
<li><strong>Photographer on board</strong> — €200 / hour, we can recommend one.</li>
<li><strong>Beach club entry</strong> — paid separately at the club, €50–€150 minimum per head.</li>
<li><strong>Jet ski hour</strong> — €200 (free on Mangusta 80 charter).</li>
</ul>

<h2>BYO rules</h2>
<ul>
<li><strong>Yes:</strong> bring your own spirits, mixers, beer top-ups, additional cava, snacks, costume pieces, inflatable swans, music playlists, decorations.</li>
<li><strong>Cans and plastic only on deck</strong> — no glass. Spanish marina fines for broken glass overboard are punishing and we enforce this.</li>
<li><strong>No confetti, no glitter</strong> — anything that ends up in the water is a problem.</li>
<li><strong>No open flames</strong> — no shisha, no candles, no cake-candle photo moments unless we coordinate ashore.</li>
<li><strong>Drugs are an instant return-to-port</strong> — security deposit forfeit. Don't.</li>
</ul>

<h2>Best months for stag &amp; hen</h2>
<p>Late June through early September is the season. Sea is 22–24 °C, the marina scene is at full volume, beach clubs are in peak operation. <strong>July</strong> is the busiest single month — book 4 weeks ahead for Saturday slots. <strong>Mid-September</strong> keeps the warmth and drops prices 10–15% — best value for groups happy with a slightly quieter scene. Avoid Saturday in August if you want last-minute availability.</p>

<h2>Booking and deposit</h2>
<p>Tap <strong>Book now</strong> top-right. Tell us:</p>
<ul>
<li>Date (or weekend range)</li>
<li>Group size</li>
<li>Hen or stag — and how rowdy (we'll match the right skipper)</li>
<li>Half-day vs full-day preference</li>
<li>BYO vs paid bar preference</li>
<li>DJ + beach-club tender if you want them</li>
</ul>
<p>We respond within 5 min on WhatsApp with 2–3 specific boats + itemised quote. 30% deposit secures, balance morning of charter. Free cancellation up to 7 days out; weather cancellations 100% refunded.</p>

<h2>Frequently asked questions</h2>
<details><summary>Can we bring our own alcohol?</summary><p>Yes on private charters — BYO is welcomed. Cava, beer, white wine are already on board free. Spirits and mixers you bring yourself. Cans and plastic only on deck — no glass.</p></details>
<details><summary>What about the beach-club tender?</summary><p>The skipper anchors offshore from Nikki Beach or Ocean Club, then tenders the group ashore in the dinghy or jet-ski (4 at a time). You spend 90 min at the club, pay club entry separately, then we collect. Standard add-on, no extra boat charge.</p></details>
<details><summary>Will the skipper join the party?</summary><p>The skipper stays sober and at the helm — that's their job under Spanish maritime law. But they're friendly, take photos, and most have done hundreds of stag/hen days. Tip is appreciated (€50–€100 cash for a great half-day).</p></details>
<details><summary>What if the weather is bad?</summary><p>If forecast wind exceeds Force 4–5 (~20+ knots) the skipper postpones the night before. You re-book a date or get 100% refund. Light rain alone is not a cancellation reason in Marbella.</p></details>
<details><summary>Can we split the group across two boats?</summary><p>Yes — common for groups of 14+. We synchronise itineraries so both boats anchor at the same spots. Each boat is its own booking at its own price.</p></details>'''

    jsonld = [
        jsonld_org(),
        {
            "@context":"https://schema.org","@type":"Service",
            "name":"Bachelor & Hen Party Charter Marbella",
            "url":SITE['base_url']+"/experiences/bachelor-hen-parties-marbella/",
            "provider":{"@id":SITE['base_url']+"/#org"},
            "areaServed":"Marbella, Spain",
            "audience":{"@type":"PeopleAudience","name":"Bachelor and hen party groups"},
            "offers":{"@type":"AggregateOffer","priceCurrency":"EUR","lowPrice":SITE['price_anchor_low_2h'],"highPrice":SITE['price_anchor_fullday_8h']},
        },
        {
            "@context":"https://schema.org","@type":"BreadcrumbList",
            "itemListElement":[
                {"@type":"ListItem","position":1,"name":"Home","item":SITE['base_url']+"/"},
                {"@type":"ListItem","position":2,"name":"Experiences","item":SITE['base_url']+"/experiences/"},
                {"@type":"ListItem","position":3,"name":"Bachelor & Hen Parties","item":SITE['base_url']+"/experiences/bachelor-hen-parties-marbella/"},
            ],
        },
    ]

    write_page(
        slug="experiences/bachelor-hen-parties-marbella",
        title="Bachelor & Hen Party Yacht Charter Marbella: Full Day Script",
        meta="Bachelor & hen party yacht charter Marbella — Azimut 39 (11 guests), Mangusta 80 (12 guests). BYO welcomed, DJ add-on, beach-club tender. From €1,299 / 4 h.",
        h1="Bachelor & Hen Parties in Marbella",
        sub="The Sunday script for hen and stag weekends — yacht morning, beach-club tender, sunset return. Groups 9–12 guests, BYO welcomed.",
        eyebrow="Bachelor & Hen · Marbella",
        body_html_str=body,
        jsonld=jsonld,
        breadcrumbs='<nav class="breadcrumbs"><a href="/">Home</a> › <a href="/experiences/">Experiences</a> › <span>Bachelor & Hen Parties</span></nav>',
        hero_base="/img/customers/h02",
        hero_widths=(400,600,900),
        hero_alt="Bachelor and hen party yacht charter in Marbella",
    )
    print("  ✓ /experiences/bachelor-hen-parties-marbella/")


def main():
    render_hub()
    render_family()
    render_photoshoot()
    render_bachelor_hen()

if __name__ == "__main__":
    main()
