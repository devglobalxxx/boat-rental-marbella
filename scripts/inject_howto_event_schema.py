#!/usr/bin/env python3
"""Inject HowTo + Event JSON-LD on relevant rendered pages.

HowTo applies to: proposal, wedding, booking-flow, hen-party planning posts.
Event applies to: blog posts about specific Marbella events (Starlite, F1 GP,
NYE, Feria, Ironman, etc).

Both blocks live inside a single marker pair per page so re-runs replace.
"""
from __future__ import annotations
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "site"
SITE = json.loads((ROOT / "config" / "keyword_map.json").read_text())["site"]
BASE = SITE["base_url"].rstrip("/")

# -------- HowTo recipes (slug → schema) --------
HOWTO = {
    "experiences/proposal-yacht-marbella": {
        "name": "How to plan a yacht proposal in Marbella",
        "description": "Skipper-coordinated proposal playbook on a charter yacht in Marbella — sunset at Río Verde, cava ready, ring hidden, photo at La Concha.",
        "totalTime": "P1D",
        "estimatedCost": {"@type": "MonetaryAmount", "currency": "EUR", "value": 749},
        "step": [
            {"@type": "HowToStep", "name": "Message Andra on WhatsApp", "text": "WhatsApp the operator with your date, partner's name, and whether the partner knows about the cruise or the proposal."},
            {"@type": "HowToStep", "name": "5-minute coordination call", "text": "Skipper and proposer briefly discuss the signal, ring handover, and partner-knows-vs-doesn't planning."},
            {"@type": "HowToStep", "name": "Boarding at Puerto Banús", "text": "Both partners board 75 minutes before sunset. Welcome cava at the dock. You secretly hand the ring to the skipper."},
            {"@type": "HowToStep", "name": "Anchor at Río Verde", "text": "Slow cruise west, anchor with La Concha mountain behind. Music down low. Skipper hands you both a glass of cava."},
            {"@type": "HowToStep", "name": "Step to the bow", "text": "On your signal, move to the bow. Skipper discreetly disappears. Pop the question."},
            {"@type": "HowToStep", "name": "Photo + champagne", "text": "Skipper takes the photo from the helm. Second bottle of cava on the ride back."},
        ],
    },
    "experiences/wedding-yacht-marbella": {
        "name": "How to plan a yacht wedding in Marbella",
        "description": "Plan a yacht wedding ceremony in Marbella — register civilly ashore beforehand, on-board ceremony with celebrant, reception with cava and catered food, photos at La Concha.",
        "totalTime": "P30D",
        "estimatedCost": {"@type": "MonetaryAmount", "currency": "EUR", "value": 1299, "minValue": 1299, "maxValue": 6000},
        "step": [
            {"@type": "HowToStep", "name": "Civil registration ashore", "text": "Complete the legal civil registration at Marbella town hall a few days before the ceremony — the on-board ceremony itself is symbolic in Spain unless you've done this paperwork."},
            {"@type": "HowToStep", "name": "Pick the boat", "text": "Up to 6 guests: Astondoa 40. 7-11 guests: Azimut 39. 12+ guests with reception: Mangusta 80. 20-30 guests: two boats in tandem."},
            {"@type": "HowToStep", "name": "Book the boat 3-6 months ahead", "text": "Peak July/August Saturdays need 6 months. Off-season Oct-May usually 4 weeks ahead. 50% deposit secures the date."},
            {"@type": "HowToStep", "name": "Coordinate vendors", "text": "Hire your own celebrant (the boat doesn't provide one), photographer (we recommend), and catering."},
            {"@type": "HowToStep", "name": "Ceremony day", "text": "Boarding 14:30, cast off 15:00, anchor at Río Verde 15:30, ceremony 15:45, reception 16:30, return 19:30."},
        ],
    },
    "blog/how-much-does-it-cost-to-rent-a-boat-in-marbella": {
        "name": "How to book a boat in Marbella",
        "description": "Three-step process to book a skippered boat charter in Marbella with no booking-platform fee.",
        "totalTime": "PT5M",
        "step": [
            {"@type": "HowToStep", "name": "WhatsApp the operator", "text": "Send your date, group size, and any preferences. Average reply under 5 minutes in Marbella daytime."},
            {"@type": "HowToStep", "name": "Confirm the quote", "text": "We reply with a full quote including skipper, fuel, drinks and 21% IVA — no booking fee on top."},
            {"@type": "HowToStep", "name": "Pay 50% deposit", "text": "50% deposit secures the date; balance the morning of the charter."},
        ],
    },
}

# -------- Event mapping (slug → Event schema) --------
EVENT = {
    "blog/starlite-marbella-yacht-charter": {
        "name": "Starlite Marbella 2026",
        "description": "Annual music festival at Cantera de Nagüeles, Marbella. Yacht charters available the day before and after concerts.",
        "startDate": "2026-07-12",
        "endDate": "2026-08-30",
        "location": {"@type": "Place", "name": "Cantera de Nagüeles", "address": {"@type": "PostalAddress", "addressLocality": "Marbella", "addressCountry": "ES"}},
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
    },
    "blog/marbella-luxury-weekend-yacht": {
        "name": "Marbella Luxury Weekend 2026",
        "description": "Annual showcase at Puerto Banús with luxury brand exhibitions, fashion shows and yacht parties.",
        "startDate": "2026-06-05",
        "endDate": "2026-06-09",
        "location": {"@type": "Place", "name": "Puerto Banús, Marbella", "address": {"@type": "PostalAddress", "addressLocality": "Marbella", "addressCountry": "ES"}},
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
    },
    "blog/spanish-f1-grand-prix-marbella-yacht": {
        "name": "F1 Spanish Grand Prix 2026",
        "description": "Formula 1 Spanish GP at Circuit de Barcelona. Many fans combine the weekend with a Marbella stop — yacht charter available.",
        "startDate": "2026-06-12",
        "endDate": "2026-06-14",
        "location": {"@type": "Place", "name": "Circuit de Barcelona-Catalunya", "address": {"@type": "PostalAddress", "addressLocality": "Barcelona", "addressCountry": "ES"}},
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
    },
    "blog/nye-yacht-charter-marbella": {
        "name": "New Year's Eve in Marbella 2026",
        "description": "NYE yacht charter from Puerto Banús — view the Marbella fireworks from the bow.",
        "startDate": "2026-12-31T20:00",
        "endDate": "2027-01-01T01:00",
        "location": {"@type": "Place", "name": "Puerto Banús, Marbella", "address": {"@type": "PostalAddress", "addressLocality": "Marbella", "addressCountry": "ES"}},
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/MixedEventAttendanceMode",
    },
    "blog/san-pedro-feria-2026": {
        "name": "San Pedro Feria 2026",
        "description": "Annual fair of San Pedro de Alcántara, October. Charter the day before or after.",
        "startDate": "2026-10-16",
        "endDate": "2026-10-22",
        "location": {"@type": "Place", "name": "San Pedro de Alcántara, Marbella", "address": {"@type": "PostalAddress", "addressLocality": "Marbella", "addressCountry": "ES"}},
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
    },
    "blog/marbella-feria-san-bernabe": {
        "name": "Marbella Feria de San Bernabé 2026",
        "description": "Marbella's annual June feria — religious processions, casetas, fireworks.",
        "startDate": "2026-06-11",
        "endDate": "2026-06-18",
        "location": {"@type": "Place", "name": "Marbella city centre", "address": {"@type": "PostalAddress", "addressLocality": "Marbella", "addressCountry": "ES"}},
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
    },
    "blog/ironman-marbella-yacht-recovery": {
        "name": "Ironman 70.3 Marbella 2026",
        "description": "Half-distance triathlon in Marbella every May. Pre-race calm cruise and post-race recovery charter on offer.",
        "startDate": "2026-05-02",
        "endDate": "2026-05-02",
        "location": {"@type": "Place", "name": "Marbella", "address": {"@type": "PostalAddress", "addressLocality": "Marbella", "addressCountry": "ES"}},
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
    },
    "blog/semana-santa-yacht-marbella": {
        "name": "Semana Santa Marbella 2026",
        "description": "Holy Week processions in Marbella. Boat charters available on quieter side.",
        "startDate": "2026-03-29",
        "endDate": "2026-04-05",
        "location": {"@type": "Place", "name": "Marbella", "address": {"@type": "PostalAddress", "addressLocality": "Marbella", "addressCountry": "ES"}},
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
    },
    "blog/andalusia-day-yacht": {
        "name": "Día de Andalucía 2026",
        "description": "Andalusia regional holiday, 28 February. Quiet early-season yacht charter in Marbella.",
        "startDate": "2026-02-28",
        "endDate": "2026-02-28",
        "location": {"@type": "Place", "name": "Marbella, Andalucía", "address": {"@type": "PostalAddress", "addressLocality": "Marbella", "addressCountry": "ES"}},
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
    },
    "blog/san-juan-night-boat-marbella": {
        "name": "Noche de San Juan Marbella 2026",
        "description": "Midsummer beach-bonfire night, 23 June. Watch from a yacht offshore.",
        "startDate": "2026-06-23T20:00",
        "endDate": "2026-06-24T02:00",
        "location": {"@type": "Place", "name": "Marbella beaches", "address": {"@type": "PostalAddress", "addressLocality": "Marbella", "addressCountry": "ES"}},
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
    },
}

# -------- inject --------
BEGIN = "<!-- ai-howto-event:begin -->"
END = "<!-- ai-howto-event:end -->"
PAT = re.compile(re.escape(BEGIN) + r"[\s\S]*?" + re.escape(END))

def page_for(slug: str):
    blocks = []
    if slug in HOWTO:
        h = HOWTO[slug]
        blocks.append({
            "@context": "https://schema.org",
            "@type": "HowTo",
            **h,
            "image": BASE + "/img/boats/azimut-39/hero-1200.jpg",
            "publisher": {"@id": BASE + "/#org"},
        })
    if slug in EVENT:
        e = EVENT[slug]
        blocks.append({
            "@context": "https://schema.org",
            "@type": "Event",
            **e,
            "url": f"{BASE}/{slug}/",
            "organizer": {"@id": BASE + "/#org"},
            "offers": {
                "@type": "Offer",
                "name": "Marbella yacht charter for this event",
                "url": BASE + "/",
                "priceCurrency": "EUR",
                "price": 749,
                "availability": "https://schema.org/InStock",
            },
        })
    return blocks

def inject(path: pathlib.Path) -> bool:
    rel = path.relative_to(SITE_DIR).parent
    slug = str(rel)
    if slug == ".":
        slug = ""
    blocks = page_for(slug)
    s = path.read_text()
    if not blocks:
        # If no blocks but a stale injection exists, clean it.
        if PAT.search(s):
            path.write_text(PAT.sub("", s))
            return True
        return False
    block_json = "</script>\n<script type=\"application/ld+json\">".join(
        json.dumps(b, ensure_ascii=False, separators=(",", ":")) for b in blocks
    )
    block = BEGIN + "\n" + f'<script type="application/ld+json">{block_json}</script>' + "\n" + END
    if PAT.search(s):
        new = PAT.sub(block, s)
    else:
        new = s.replace("</head>", block + "\n</head>", 1)
    if new == s:
        return False
    path.write_text(new)
    return True

def main():
    n_howto = n_event = 0
    for p in SITE_DIR.rglob("index.html"):
        rel = str(p.relative_to(SITE_DIR).parent)
        if rel == ".":
            continue
        if rel in HOWTO:
            n_howto += 1
        if rel in EVENT:
            n_event += 1
        inject(p)
    print(f"inject_howto_event_schema: {n_howto} HowTo, {n_event} Event blocks injected")

if __name__ == "__main__":
    main()
