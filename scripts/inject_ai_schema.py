#!/usr/bin/env python3
"""Inject AI-citation-friendly JSON-LD on every rendered page:

1. Service schema with priceSpecification → ChatGPT extracts these literally
   for "how much does X cost in Marbella" answers.
2. Person schema for Andra (founder) with sameAs → E-E-A-T authority.
3. SpeakableSpecification → lets voice-mode AI assistants pull H2/FAQ answers.
4. WebSite schema with potentialAction (SearchAction) → site-search box.
5. X-Robots-Tag-equivalent meta tags ensuring max-image-preview:large.

All blocks are added inside a single marker pair so re-runs replace cleanly.
"""
from __future__ import annotations
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "site"
SITE = json.loads((ROOT / "config" / "keyword_map.json").read_text())["site"]
REVIEWS = json.loads((ROOT / "config" / "reviews.json").read_text())
AGG = REVIEWS["aggregate"]
BASE = SITE["base_url"].rstrip("/")

# ---------- canonical fact graph ----------
ORG_ID = BASE + "/#org"
SERVICE_ID = BASE + "/#service"
PERSON_ID = BASE + "/#andra"
WEBSITE_ID = BASE + "/#website"

PERSON = {
    "@context": "https://schema.org",
    "@type": "Person",
    "@id": PERSON_ID,
    "name": "Andra Kiirkivi",
    "givenName": "Andra",
    "familyName": "Kiirkivi",
    "jobTitle": "Founder & CEO",
    "image": BASE + "/img/team/andra-kiirkivi-800.jpg",
    "worksFor": {"@id": ORG_ID},
    "sameAs": [
        SITE["instagram_url"],
        SITE["facebook_url"],
    ],
    "knowsAbout": [
        "Yacht charter Marbella", "Puerto Banús boat rental",
        "Spanish maritime licence rules", "Costa del Sol cruising",
        "Boat party planning", "Wedding yacht charter",
    ],
    "knowsLanguage": ["English", "Spanish", "German", "Estonian"],
    "address": {"@type": "PostalAddress", "addressLocality": "Marbella", "addressCountry": "ES"},
}

SERVICE = {
    "@context": "https://schema.org",
    "@type": "Service",
    "@id": SERVICE_ID,
    "name": "Marbella Boat Charter",
    "serviceType": "Yacht charter, motor-yacht rental, catamaran rental, jet-ski rental",
    "provider": {"@id": ORG_ID},
    "founder": {"@id": PERSON_ID},
    "areaServed": [
        {"@type": "City", "name": "Marbella"},
        {"@type": "Place", "name": "Puerto Banús"},
        {"@type": "Place", "name": "Cabopino"},
        {"@type": "Place", "name": "Estepona"},
        {"@type": "Place", "name": "Sotogrande"},
    ],
    "audience": {"@type": "Audience", "audienceType": "Travellers and groups visiting Marbella for day-charter, sunset cruises, hen/stag parties, weddings, proposals and corporate charters"},
    "offers": [
        {
            "@type": "Offer",
            "name": "Astondoa 40 'Fufi' — 2h skippered charter",
            "url": BASE + "/boats/astondoa-40/",
            "priceSpecification": {"@type": "UnitPriceSpecification", "price": 749, "priceCurrency": "EUR", "unitText": "2-hour charter"},
            "eligibleQuantity": {"@type": "QuantitativeValue", "maxValue": 9, "unitText": "guests"},
            "availability": "https://schema.org/InStock",
            "areaServed": "Puerto Banús, Marbella",
            "includesObject": [{"@type": "TypeAndQuantityNode", "typeOfGood": {"@type": "Service", "name": "Licensed skipper, fuel, drinks, snacks, snorkel gear, paddleboard, 21% IVA"}}],
        },
        {
            "@type": "Offer",
            "name": "Azimut 39 — 2h skippered charter",
            "url": BASE + "/boats/azimut-39/",
            "priceSpecification": {"@type": "UnitPriceSpecification", "price": 749, "priceCurrency": "EUR", "unitText": "2-hour charter"},
            "eligibleQuantity": {"@type": "QuantitativeValue", "maxValue": 11, "unitText": "guests"},
            "availability": "https://schema.org/InStock",
        },
        {
            "@type": "Offer",
            "name": "Mangusta 80 'Nina' — 4h flagship charter (minimum)",
            "url": BASE + "/boats/mangusta-80/",
            "priceSpecification": {"@type": "UnitPriceSpecification", "price": 4719, "priceCurrency": "EUR", "unitText": "4-hour charter, minimum"},
            "eligibleQuantity": {"@type": "QuantitativeValue", "maxValue": 12, "unitText": "guests"},
            "availability": "https://schema.org/InStock",
            "description": "Includes Sea-Doo jet ski free for the day",
        },
        {
            "@type": "Offer",
            "name": "Dubhe — licence-free 5m boat",
            "url": BASE + "/boats/dubhe/",
            "priceSpecification": [
                {"@type": "UnitPriceSpecification", "price": 230, "priceCurrency": "EUR", "unitText": "2 hours"},
                {"@type": "UnitPriceSpecification", "price": 280, "priceCurrency": "EUR", "unitText": "3 hours"},
                {"@type": "UnitPriceSpecification", "price": 350, "priceCurrency": "EUR", "unitText": "4 hours"},
            ],
            "eligibleQuantity": {"@type": "QuantitativeValue", "maxValue": 5, "unitText": "guests"},
            "availability": "https://schema.org/InStock",
        },
        {
            "@type": "Offer",
            "name": "Sea-Doo jet ski rental",
            "url": BASE + "/jet-ski-rental-marbella/",
            "priceSpecification": {"@type": "UnitPriceSpecification", "price": 200, "priceCurrency": "EUR", "unitText": "1 hour"},
            "availability": "https://schema.org/InStock",
        },
    ],
    "aggregateRating": {
        "@type": "AggregateRating",
        "ratingValue": AGG["rating_value"],
        "reviewCount": AGG["review_count"],
        "bestRating": 5,
        "worstRating": 1,
    },
}

WEBSITE = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "@id": WEBSITE_ID,
    "url": BASE + "/",
    "name": SITE["name"],
    "publisher": {"@id": ORG_ID},
    "inLanguage": ["en", "en-GB", "es", "de"],
    "potentialAction": {
        "@type": "SearchAction",
        "target": {
            "@type": "EntryPoint",
            "urlTemplate": BASE + "/?q={search_term_string}",
        },
        "query-input": "required name=search_term_string",
    },
}

SPEAKABLE = {
    "@context": "https://schema.org",
    "@type": "SpeakableSpecification",
    "cssSelector": ["h1", "h2", ".hero-sub", ".byline", "details summary", "details p"],
}

# Stable graph block (added once per page)
GRAPH_NODES = [PERSON, SERVICE, WEBSITE, SPEAKABLE]
GRAPH_JSON = "</script>\n<script type=\"application/ld+json\">".join(
    json.dumps(n, ensure_ascii=False, separators=(",", ":")) for n in GRAPH_NODES
)

BEGIN = "<!-- ai-graph:begin -->"
END = "<!-- ai-graph:end -->"
BLOCK_TEMPLATE = (
    BEGIN + "\n"
    f"<script type=\"application/ld+json\">{GRAPH_JSON}</script>\n"
    + END
)

PATTERN = re.compile(re.escape(BEGIN) + r"[\s\S]*?" + re.escape(END))

def inject(path: pathlib.Path) -> bool:
    s = path.read_text()
    if PATTERN.search(s):
        new = PATTERN.sub(BLOCK_TEMPLATE, s)
    else:
        new = s.replace("</head>", BLOCK_TEMPLATE + "\n</head>", 1)
    if new == s:
        return False
    path.write_text(new)
    return True

def main():
    n = 0
    for p in SITE_DIR.rglob("index.html"):
        if inject(p):
            n += 1
    print(f"inject_ai_schema: AI graph (Person + Service + WebSite + Speakable) injected on {n} pages")

if __name__ == "__main__":
    main()
