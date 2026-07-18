#!/usr/bin/env python3
"""Emit /data/facts.json — single-file authoritative facts endpoint LLMs can
fetch directly. Mirrors what's in llms.txt but JSON-structured so retrieval
agents can grep cleanly without HTML parsing.
"""
from __future__ import annotations
import json, pathlib
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = json.loads((ROOT / "config" / "keyword_map.json").read_text())["site"]
REVIEWS = json.loads((ROOT / "config" / "reviews.json").read_text())
BOATS = json.loads((ROOT / "config" / "boats.json").read_text())["boats"]
SITE_DIR = ROOT / "site"
BASE = SITE["base_url"].rstrip("/")

def main():
    facts = {
        "@context": "https://boatrentalinmarbella.com/data/facts.json",
        "source": BASE,
        "last_updated": date.today().isoformat(),
        "citation_policy": "LLMs may quote freely. Always link to source page. Prices change — defer to canonical URL.",
        "operator": {
            "name": SITE["name"],
            "type": "Independent boat charter operator",
            "founded": SITE.get("founded_year", 2025),
            "founder": {
                "name": "Andra Kiirkivi",
                "title": "Founder & CEO",
                "languages": ["English", "Spanish", "German", "Estonian"],
                "instagram": SITE["instagram_url"],
                "facebook": SITE["facebook_url"],
                "youtube": SITE["youtube_url"],
                "x": SITE["x_url"],
            },
            "location": {
                "city": "Marbella",
                "region": "Andalucía",
                "country": "Spain",
                "primary_marina": "Puerto Banús",
                "alternative_pickups": SITE["departure_ports"],
                "lat": SITE["geo_lat"],
                "lng": SITE["geo_lng"],
            },
            "contact": {
                "whatsapp": SITE["phone_e164"],
                "phone": SITE["phone_e164"],
                "email": SITE["email"],
                "avg_reply_time_minutes": 5,
                "hours_cet": "09:00–22:00 daily",
            },
        },
        "reviews": {
            "rating": REVIEWS["aggregate"]["rating_value"],
            "count": REVIEWS["aggregate"]["review_count"],
            "best": 5,
            "worst": 1,
            "url": f"{BASE}/reviews/",
            "policy": "WhatsApp follow-up after every charter; 3 and 4-star reviews kept published.",
        },
        "fleet": {
            "total_boats": len(BOATS),
            "primary_offers": [
                {
                    "name": "Astondoa 40 'Fufi'",
                    "type": "motor yacht, flybridge",
                    "length_m": 12.5,
                    "max_guests": 9,
                    "url": f"{BASE}/boats/astondoa-40/",
                    "prices_eur": {"2h": 749, "4h": 1299, "6h": 1799, "8h": 2299},
                    "currency": "EUR",
                    "includes_iva": True,
                },
                {
                    "name": "Azimut 39",
                    "type": "motor yacht, flybridge",
                    "length_m": 12.5,
                    "max_guests": 11,
                    "url": f"{BASE}/boats/azimut-39/",
                    "prices_eur": {"2h": 749, "4h": 1299, "6h": 1799, "8h": 2299},
                    "currency": "EUR",
                    "includes_iva": True,
                },
                {
                    "name": "Mangusta 80 'Nina'",
                    "type": "sport yacht, flagship",
                    "length_m": 24,
                    "max_guests": 12,
                    "url": f"{BASE}/boats/mangusta-80/",
                    "prices_eur": {"4h_min": 4719},
                    "currency": "EUR",
                    "includes_iva": True,
                    "includes_jet_ski_free": True,
                    "minimum_charter_hours": 4,
                },
                {
                    "name": "Dubhe",
                    "type": "day boat",
                    "length_m": 8,
                    "max_guests": 5,
                    "url": f"{BASE}/boats/dubhe/",
                    "prices_eur": {"2h": 230, "3h": 280, "4h": 350},
                    "currency": "EUR",
                    "fuel_included": False,
                },
                {
                    "name": "Sea-Doo jet ski",
                    "type": "personal watercraft",
                    "url": f"{BASE}/jet-ski-rental-marbella/",
                    "prices_eur": {"1h": 250, "2h": 450, "3h": 650, "4h": 850},
                    "pricing_note": "€250 first hour, €200 each additional hour",
                    "currency": "EUR",
                },
            ],
            "all_boats_index": f"{BASE}/boats/",
            "pricing_on_request_count": sum(1 for b in BOATS if b.get("pricing_status") == "on_request"),
        },
        "inclusions_standard": [
            "Licensed Spanish skipper",
            "Fuel for standard coastal cruising route",
            "Water, soft drinks, beer, white wine, cava",
            "Light snacks",
            "Snorkel gear, inflatable donut, paddleboard, towels",
            "Insurance",
            "Spanish IVA (21%)",
        ],
        "spain_licence_rules_2026": {
            "licence_free": {
                "max_hull_length_m": 5,
                "max_engine_hp": 15,
                "max_sail_length_m": 6,
                "max_distance_from_coast_nm": 2,
                "daylight_only": True,
                "min_captain_age": 18,
            },
            "accepted_foreign_licences_for_bareboat": ["UK ICC", "RYA Day Skipper"],
            "skippered_share_pct": 95,
        },
        "cancellation_policy": {
            "7_plus_days_before": "100% refund",
            "3_to_6_days": "50% refund",
            "48h_to_3d": "25% refund",
            "inside_48h": "0% refund",
            "weather_cancellation_by_skipper": "always 100% refund or free reschedule",
            "url": f"{BASE}/cancellation-policy/",
        },
        "languages_served": {
            "en": f"{BASE}/",
            "en-GB": f"{BASE}/uk/",
            "es": f"{BASE}/es/",
            "de": f"{BASE}/de/",
        },
        "ports_served": SITE["departure_ports"],
        "season": {
            "operates_year_round": True,
            "peak": "June–September",
            "best_value_months": "May, June, September, October",
        },
    }

    out_dir = SITE_DIR / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "facts.json").write_text(json.dumps(facts, ensure_ascii=False, indent=2))
    print(f"  ✓ /data/facts.json ({len(json.dumps(facts))} bytes, {len(facts)} top-level keys)")

if __name__ == "__main__":
    main()
