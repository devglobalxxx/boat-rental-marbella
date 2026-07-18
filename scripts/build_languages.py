#!/usr/bin/env python3
"""Build hub landing pages for 9 additional languages.

Each language gets:
  site/<code>/index.html  — translated hub page (homepage equivalent)

Languages: DE FR AR RU SV NL PL UK NO
(Spanish ES already exists via build_es.py — left untouched)

Plus: regenerates a shared language switcher widget HTML snippet that
sister script `inject_language_switcher.py` injects into every page's footer.
"""
from __future__ import annotations
import json, pathlib, html, re
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config" / "keyword_map.json").read_text())
SITE = CONFIG["site"]
SITE_DIR = ROOT / "site"
BASE = SITE["base_url"]
WA = SITE.get("whatsapp_e164_noplus") or SITE["whatsapp_e164"].lstrip("+")
PHONE = SITE.get("phone_display", "+34 600 000 000")

# ─── Languages ─────────────────────────────────────────────────────────────────

LANGUAGES = [
    ("de", "Deutsch", "🇩🇪", "ltr"),
    ("fr", "Français", "🇫🇷", "ltr"),
    ("ar", "العربية", "🇦🇪", "rtl"),
    ("ru", "Русский", "🇷🇺", "ltr"),
    ("sv", "Svenska", "🇸🇪", "ltr"),
    ("nl", "Nederlands", "🇳🇱", "ltr"),
    ("pl", "Polski", "🇵🇱", "ltr"),
    ("uk", "Українська", "🇺🇦", "ltr"),
    ("no", "Norsk", "🇳🇴", "ltr"),
]

# Translated content per language ─────────────────────────────────────────────

CONTENT = {
    "de": {
        "title": "Bootsverleih Marbella 2026 — Yachten, Katamarane & Charter ab €749",
        "desc": "Buchen Sie eine Yacht in Marbella mit lizenziertem Skipper. Puerto Banús, Marbella Marina, Cabopino. Festpreise, sofortige WhatsApp-Bestätigung.",
        "h1": "Bootsverleih Marbella",
        "tagline": "Yachten und Katamarane mit Skipper an der Costa del Sol",
        "hero_sub": "200+ Charter-Optionen über Puerto Banús, Marbella Marina, Cabopino, Estepona und Sotogrande. Lizenzierte Skipper, transparente Preise, sofortige Bestätigung über WhatsApp.",
        "cta_wa": "Auf WhatsApp schreiben",
        "cta_browse": "Flotte ansehen",
        "section_boats": "Beliebte Charter",
        "section_why": "Warum bei uns buchen",
        "why_1": "Lizenzierte spanische Skipper inklusive — keine Erfahrung erforderlich",
        "why_2": "Kraftstoff, Getränke, Schnorchelausrüstung und IVA-Steuer enthalten",
        "why_3": "Antwort über WhatsApp in unter 5 Minuten, 8:00–22:00 Uhr",
        "why_4": "Kostenlose Stornierung bis 7 Tage vor Abfahrt",
        "boat_features": ["Skipper", "Kraftstoff", "Getränke", "Schnorcheln"],
        "from_label": "Ab",
        "price_on_request": "Preis auf Anfrage",
        "h2_destinations": "Abfahrtshäfen",
        "destinations_intro": "Wir bedienen die fünf wichtigsten Abfahrtspunkte der Costa del Sol:",
    },
    "fr": {
        "title": "Location de Bateau Marbella 2026 — Yachts, Catamarans & Charters dès 749€",
        "desc": "Louez un yacht à Marbella avec skipper agréé. Puerto Banús, Marbella Marina, Cabopino. Prix fixes, confirmation WhatsApp instantanée.",
        "h1": "Location de Bateau Marbella",
        "tagline": "Yachts et catamarans avec skipper sur la Costa del Sol",
        "hero_sub": "200+ options de charter à travers Puerto Banús, Marbella Marina, Cabopino, Estepona et Sotogrande. Skippers agréés, prix transparents, confirmation instantanée par WhatsApp.",
        "cta_wa": "Envoyer un message sur WhatsApp",
        "cta_browse": "Voir la flotte",
        "section_boats": "Charters populaires",
        "section_why": "Pourquoi réserver avec nous",
        "why_1": "Skippers espagnols agréés inclus — aucune expérience requise",
        "why_2": "Carburant, boissons, équipement de snorkeling et TVA inclus",
        "why_3": "Réponse WhatsApp en moins de 5 minutes, 8h00–22h00",
        "why_4": "Annulation gratuite jusqu'à 7 jours avant le départ",
        "boat_features": ["Skipper", "Carburant", "Boissons", "Snorkeling"],
        "from_label": "À partir de",
        "price_on_request": "Prix sur demande",
        "h2_destinations": "Ports de départ",
        "destinations_intro": "Nous desservons les cinq principaux points de départ de la Costa del Sol :",
    },
    "ar": {
        "title": "تأجير القوارب في ماربيا 2026 — يخوت وقوارب كاتاماران من €749",
        "desc": "استأجر يختًا في ماربيا مع ربان مرخص. بويرتو بانوس، مرسى ماربيا، كابوبينو. أسعار ثابتة، تأكيد فوري عبر واتساب.",
        "h1": "تأجير القوارب في ماربيا",
        "tagline": "يخوت وقوارب كاتاماران مع ربان على ساحل كوستا ديل سول",
        "hero_sub": "أكثر من 200 خيار تأجير عبر بويرتو بانوس، مرسى ماربيا، كابوبينو، إستيبونا وسوتوغراندي. ربابنة مرخصون، أسعار شفافة، تأكيد فوري عبر واتساب.",
        "cta_wa": "تواصل عبر واتساب",
        "cta_browse": "تصفح الأسطول",
        "section_boats": "الرحلات الأكثر طلبًا",
        "section_why": "لماذا تحجز معنا",
        "why_1": "ربابنة إسبان مرخصون مشمولون — لا حاجة لخبرة سابقة",
        "why_2": "الوقود والمشروبات ومعدات الغطس وضريبة القيمة المضافة مشمولة",
        "why_3": "الرد عبر واتساب في أقل من 5 دقائق، من 8:00 إلى 22:00",
        "why_4": "إلغاء مجاني حتى 7 أيام قبل الإبحار",
        "boat_features": ["ربان", "وقود", "مشروبات", "غطس"],
        "from_label": "ابتداءً من",
        "price_on_request": "السعر عند الطلب",
        "h2_destinations": "موانئ الانطلاق",
        "destinations_intro": "نخدم نقاط الانطلاق الخمس الرئيسية على ساحل كوستا ديل سول:",
    },
    "ru": {
        "title": "Аренда яхт в Марбелье 2026 — Яхты, катамараны и чартеры от €749",
        "desc": "Арендуйте яхту в Марбелье с лицензированным шкипером. Пуэрто-Банус, Марина Марбельи, Кабопино. Фиксированные цены, мгновенное подтверждение через WhatsApp.",
        "h1": "Аренда яхт в Марбелье",
        "tagline": "Яхты и катамараны со шкипером на Коста-дель-Соль",
        "hero_sub": "200+ вариантов чартера в Пуэрто-Банусе, Марине Марбельи, Кабопино, Эстепоне и Сотогранде. Лицензированные шкиперы, прозрачные цены, мгновенное подтверждение через WhatsApp.",
        "cta_wa": "Написать в WhatsApp",
        "cta_browse": "Посмотреть флот",
        "section_boats": "Популярные чартеры",
        "section_why": "Почему стоит бронировать у нас",
        "why_1": "Лицензированные испанские шкиперы включены — опыт не нужен",
        "why_2": "Топливо, напитки, снаряжение для снорклинга и НДС включены",
        "why_3": "Ответ в WhatsApp менее чем за 5 минут, 8:00–22:00",
        "why_4": "Бесплатная отмена за 7 дней до отплытия",
        "boat_features": ["Шкипер", "Топливо", "Напитки", "Снорклинг"],
        "from_label": "От",
        "price_on_request": "Цена по запросу",
        "h2_destinations": "Порты отправления",
        "destinations_intro": "Мы обслуживаем пять основных пунктов отправления на Коста-дель-Соль:",
    },
    "sv": {
        "title": "Båtuthyrning Marbella 2026 — Yachter, katamaraner och charter från 749 €",
        "desc": "Hyr en yacht i Marbella med licensierad skeppare. Puerto Banús, Marbella Marina, Cabopino. Fasta priser, omedelbar WhatsApp-bekräftelse.",
        "h1": "Båtuthyrning Marbella",
        "tagline": "Yachter och katamaraner med skeppare på Costa del Sol",
        "hero_sub": "200+ charteralternativ via Puerto Banús, Marbella Marina, Cabopino, Estepona och Sotogrande. Licensierade skeppare, transparenta priser, omedelbar bekräftelse via WhatsApp.",
        "cta_wa": "Meddela på WhatsApp",
        "cta_browse": "Visa flottan",
        "section_boats": "Populära charter",
        "section_why": "Varför boka hos oss",
        "why_1": "Licensierade spanska skeppare ingår — ingen erfarenhet krävs",
        "why_2": "Bränsle, drycker, snorkelutrustning och moms ingår",
        "why_3": "WhatsApp-svar inom 5 minuter, 08:00–22:00",
        "why_4": "Fri avbokning upp till 7 dagar före avgång",
        "boat_features": ["Skeppare", "Bränsle", "Drycker", "Snorkling"],
        "from_label": "Från",
        "price_on_request": "Pris på begäran",
        "h2_destinations": "Avgångshamnar",
        "destinations_intro": "Vi betjänar de fem viktigaste avgångspunkterna på Costa del Sol:",
    },
    "nl": {
        "title": "Bootverhuur Marbella 2026 — Yachten, catamarans & charters vanaf €749",
        "desc": "Huur een jacht in Marbella met gediplomeerde schipper. Puerto Banús, Marbella Marina, Cabopino. Vaste prijzen, directe WhatsApp-bevestiging.",
        "h1": "Bootverhuur Marbella",
        "tagline": "Yachten en catamarans met schipper aan de Costa del Sol",
        "hero_sub": "200+ charteropties via Puerto Banús, Marbella Marina, Cabopino, Estepona en Sotogrande. Gediplomeerde schippers, transparante prijzen, directe bevestiging via WhatsApp.",
        "cta_wa": "Stuur bericht via WhatsApp",
        "cta_browse": "Bekijk de vloot",
        "section_boats": "Populaire charters",
        "section_why": "Waarom bij ons boeken",
        "why_1": "Gediplomeerde Spaanse schippers inbegrepen — geen ervaring nodig",
        "why_2": "Brandstof, drankjes, snorkeluitrusting en BTW inbegrepen",
        "why_3": "WhatsApp-reactie binnen 5 minuten, 08:00–22:00",
        "why_4": "Gratis annulering tot 7 dagen voor vertrek",
        "boat_features": ["Schipper", "Brandstof", "Drankjes", "Snorkelen"],
        "from_label": "Vanaf",
        "price_on_request": "Prijs op aanvraag",
        "h2_destinations": "Vertrekhavens",
        "destinations_intro": "We bedienen de vijf belangrijkste vertrekpunten van de Costa del Sol:",
    },
    "pl": {
        "title": "Wynajem łodzi Marbella 2026 — Jachty, katamarany i czartery od 749 €",
        "desc": "Wynajmij jacht w Marbelli z licencjonowanym kapitanem. Puerto Banús, Marbella Marina, Cabopino. Stałe ceny, natychmiastowe potwierdzenie przez WhatsApp.",
        "h1": "Wynajem łodzi Marbella",
        "tagline": "Jachty i katamarany z kapitanem na Costa del Sol",
        "hero_sub": "Ponad 200 opcji czarteru w Puerto Banús, Marbella Marina, Cabopino, Estepona i Sotogrande. Licencjonowani kapitanowie, przejrzyste ceny, natychmiastowe potwierdzenie przez WhatsApp.",
        "cta_wa": "Napisz na WhatsApp",
        "cta_browse": "Zobacz flotę",
        "section_boats": "Popularne czartery",
        "section_why": "Dlaczego u nas",
        "why_1": "Licencjonowani hiszpańscy kapitanowie w cenie — bez doświadczenia",
        "why_2": "Paliwo, napoje, sprzęt do snorkelingu i VAT w cenie",
        "why_3": "Odpowiedź na WhatsApp w mniej niż 5 minut, 08:00–22:00",
        "why_4": "Bezpłatne anulowanie do 7 dni przed wypłynięciem",
        "boat_features": ["Kapitan", "Paliwo", "Napoje", "Snorkeling"],
        "from_label": "Od",
        "price_on_request": "Cena na zapytanie",
        "h2_destinations": "Porty odpływu",
        "destinations_intro": "Obsługujemy pięć głównych punktów wypłynięcia na Costa del Sol:",
    },
    "uk": {
        "title": "Оренда яхт у Марбельї 2026 — Яхти, катамарани та чартери від 749 €",
        "desc": "Орендуйте яхту в Марбельї з ліцензованим капітаном. Пуерто-Банус, Марина Марбельї, Кабопіно. Фіксовані ціни, миттєве підтвердження через WhatsApp.",
        "h1": "Оренда яхт у Марбельї",
        "tagline": "Яхти та катамарани з капітаном на Коста-дель-Соль",
        "hero_sub": "Понад 200 варіантів чартеру в Пуерто-Банусі, Марині Марбельї, Кабопіно, Естепоні та Сотогранде. Ліцензовані капітани, прозорі ціни, миттєве підтвердження через WhatsApp.",
        "cta_wa": "Написати у WhatsApp",
        "cta_browse": "Подивитись флот",
        "section_boats": "Популярні чартери",
        "section_why": "Чому варто бронювати у нас",
        "why_1": "Ліцензовані іспанські капітани включені — досвід не потрібен",
        "why_2": "Пальне, напої, спорядження для снорклінгу та ПДВ включені",
        "why_3": "Відповідь у WhatsApp менше ніж за 5 хвилин, 08:00–22:00",
        "why_4": "Безкоштовне скасування за 7 днів до відплиття",
        "boat_features": ["Капітан", "Пальне", "Напої", "Снорклінг"],
        "from_label": "Від",
        "price_on_request": "Ціна за запитом",
        "h2_destinations": "Порти відправлення",
        "destinations_intro": "Ми обслуговуємо п'ять основних пунктів відправлення на Коста-дель-Соль:",
    },
    "no": {
        "title": "Båtutleie Marbella 2026 — Yachter, katamaraner og charter fra €749",
        "desc": "Lei en yacht i Marbella med lisensiert skipper. Puerto Banús, Marbella Marina, Cabopino. Faste priser, øyeblikkelig WhatsApp-bekreftelse.",
        "h1": "Båtutleie Marbella",
        "tagline": "Yachter og katamaraner med skipper på Costa del Sol",
        "hero_sub": "200+ charteralternativer via Puerto Banús, Marbella Marina, Cabopino, Estepona og Sotogrande. Lisensierte skippere, transparente priser, øyeblikkelig bekreftelse via WhatsApp.",
        "cta_wa": "Send melding på WhatsApp",
        "cta_browse": "Se flåten",
        "section_boats": "Populære charter",
        "section_why": "Hvorfor booke hos oss",
        "why_1": "Lisensierte spanske skippere inkludert — ingen erfaring nødvendig",
        "why_2": "Drivstoff, drikke, snorkelutstyr og moms inkludert",
        "why_3": "WhatsApp-svar innen 5 minutter, 08:00–22:00",
        "why_4": "Gratis avbestilling opptil 7 dager før avgang",
        "boat_features": ["Skipper", "Drivstoff", "Drikke", "Snorkling"],
        "from_label": "Fra",
        "price_on_request": "Pris på forespørsel",
        "h2_destinations": "Avgangshavner",
        "destinations_intro": "Vi betjener de fem viktigste avgangspunktene på Costa del Sol:",
    },
}

# Featured boats — shared across all languages.
# Specs + prices come from config/boats.json (same source as facts.json);
# quote-only boats get price=None and render "price on request" per language.
BOATS_CFG = json.loads((ROOT / "config" / "boats.json").read_text())
_FLEET_LOWS = [min(t["prices"].values())
               for t in (BOATS_CFG["hourly_price_tiers"][b["tier"]] for b in BOATS_CFG["boats"])
               if t["prices"]]
FLEET_PRICE_RANGE = f"€{min(_FLEET_LOWS)}–€{max(_FLEET_LOWS)}"

FEATURED_SLUGS = ["astondoa-40", "azimut-39", "mangusta-80", "canados-86"]

def _featured_boats():
    by_slug = {b["slug"]: b for b in BOATS_CFG["boats"]}
    out = []
    for slug in FEATURED_SLUGS:
        b = by_slug[slug]
        tier = BOATS_CFG["hourly_price_tiers"][b["tier"]]
        if tier["prices"]:
            price = min(tier["prices"].values())
            hours = tier.get("min_hours") or min(int(k.rstrip("h")) for k in tier["prices"])
        else:
            price = hours = None  # quote-only
        out.append({
            "slug": slug,
            "name": b["name"],
            "spec": f'{b["length_m"]} m · {b["capacity_pax"]} pax',
            "price": price,
            "hours": hours,
        })
    return out

BOATS = _featured_boats()

DESTINATIONS = ["Puerto Banús", "Marbella Marina", "Cabopino", "Estepona", "Sotogrande"]

# ─── Page generator ────────────────────────────────────────────────────────────

def build_hub(code: str, lang_name: str, flag: str, dir_: str):
    c = CONTENT[code]
    wa_msg = "Hi%2C%20I%27d%20like%20to%20book%20a%20boat%20in%20Marbella"
    wa_url = f"https://wa.me/{WA}?text={wa_msg}"

    boat_cards = "\n".join(
        f'''<a href="{BASE}/boats/{b["slug"]}/" style="display:flex;flex-direction:column;background:#0c1828;border:1px solid rgba(201,168,78,0.18);border-radius:14px;overflow:hidden;text-decoration:none;color:#f4f4f2;transition:transform 0.15s;">
  <div style="aspect-ratio:16/9;background:url('{BASE}/img/boats/{b["slug"]}/hero-1200.jpg') center/cover;"></div>
  <div style="padding:16px;">
    <div style="font-weight:700;font-size:15px;margin-bottom:4px;">{b["name"]}</div>
    <div style="font-size:12px;color:rgba(244,244,242,0.55);margin-bottom:10px;">{b["spec"]}</div>
    <div style="font-size:11px;color:#c9a84e;font-weight:600;">{f'{c["from_label"]} €{b["price"]} / {b["hours"]}h' if b["price"] else c["price_on_request"]}</div>
  </div>
</a>'''
        for b in BOATS
    )

    destinations_list = "".join(
        f'<li style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.06);font-size:14px;color:rgba(244,244,242,0.75);">📍 {d}</li>'
        for d in DESTINATIONS
    )

    why_rows = "".join(
        f'<li style="display:flex;gap:10px;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.06);"><span style="color:#22c55e;flex-shrink:0;">✓</span><span style="font-size:14px;color:rgba(244,244,242,0.78);line-height:1.6;">{w}</span></li>'
        for w in [c["why_1"], c["why_2"], c["why_3"], c["why_4"]]
    )

    # hreflang alternates for all 10 languages + EN
    # NB: /uk/ is the UK-English landing (build_uk.py), so it must be declared
    # en-GB — "uk" is the Ukrainian language code and is invalid for that page.
    hreflang_links = (
        f'<link rel="alternate" hreflang="en" href="{BASE}/" />\n'
        + f'<link rel="alternate" hreflang="es" href="{BASE}/es/" />\n'
        + "\n".join(
            f'<link rel="alternate" hreflang="{"en-GB" if lc == "uk" else lc}" href="{BASE}/{lc}/" />'
            for lc, _, _, _ in LANGUAGES
        )
        + f'\n<link rel="alternate" hreflang="x-default" href="{BASE}/" />'
    )

    jsonld = {
        "@context": "https://schema.org",
        "@type": ["LocalBusiness", "Organization"],
        "@id": f"{BASE}/#org",
        "name": SITE["name"],
        "alternateName": ["Boat Rental In Marbella", "boatrentalinmarbella.com"],
        "url": f"{BASE}/{code}/",
        "logo": f"{BASE}/img/logo-480.png",
        "telephone": SITE["phone_e164"],
        "email": SITE["email"],
        "areaServed": SITE["departure_ports"],
        "sameAs": [
            u for u in [SITE.get("instagram_url"), SITE.get("facebook_url"), SITE.get("youtube_url"), SITE.get("x_url")] if u
        ],
        "priceRange": FLEET_PRICE_RANGE,
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "Marbella",
            "addressRegion": "Andalucía",
            "postalCode": "29602",
            "addressCountry": "ES",
        },
        "geo": {"@type": "GeoCoordinates", "latitude": SITE["geo_lat"], "longitude": SITE["geo_lng"]},
    }

    # Language switcher chips (links to all alternates)
    switcher = '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:12px;">'
    switcher += f'<a href="{BASE}/" style="display:inline-flex;align-items:center;gap:6px;padding:6px 12px;border-radius:50px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.10);color:rgba(244,244,242,0.65);font-size:12px;font-weight:600;text-decoration:none;">🇬🇧 English</a>'
    switcher += f'<a href="{BASE}/es/" style="display:inline-flex;align-items:center;gap:6px;padding:6px 12px;border-radius:50px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.10);color:rgba(244,244,242,0.65);font-size:12px;font-weight:600;text-decoration:none;">🇪🇸 Español</a>'
    for lc, ln, fl, _ in LANGUAGES:
        active = (lc == code)
        bg = "rgba(201,168,78,0.12)" if active else "rgba(255,255,255,0.05)"
        bd = "rgba(201,168,78,0.30)" if active else "rgba(255,255,255,0.10)"
        co = "#c9a84e" if active else "rgba(244,244,242,0.65)"
        switcher += f'<a href="{BASE}/{lc}/" style="display:inline-flex;align-items:center;gap:6px;padding:6px 12px;border-radius:50px;background:{bg};border:1px solid {bd};color:{co};font-size:12px;font-weight:600;text-decoration:none;">{fl} {ln}</a>'
    switcher += "</div>"

    html_out = f'''<!DOCTYPE html>
<html lang="{code}" dir="{dir_}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{c["title"]}</title>
<meta name="description" content="{c["desc"]}">
<link rel="canonical" href="{BASE}/{code}/">
{hreflang_links}
<link rel="stylesheet" href="{BASE}/styles-dark.css">
<link rel="icon" href="{BASE}/favicon.ico">
<meta property="og:type" content="website">
<meta property="og:title" content="{c["title"]}">
<meta property="og:description" content="{c["desc"]}">
<meta property="og:url" content="{BASE}/{code}/">
<meta property="og:image" content="{BASE}/og-image.jpg">
<meta property="og:locale" content="{code}">
<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>
</head>
<body style="margin:0;background:#07101e;color:#f4f4f2;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.6;">

<!-- Skip to English -->
<div style="background:rgba(201,168,78,0.05);border-bottom:1px solid rgba(201,168,78,0.15);padding:8px 0;text-align:center;font-size:12px;">
  <a href="{BASE}/" style="color:#c9a84e;text-decoration:none;font-weight:600;">🇬🇧 English</a>
  &nbsp;·&nbsp;
  <a href="{BASE}/es/" style="color:rgba(244,244,242,0.55);text-decoration:none;">🇪🇸 Español</a>
  &nbsp;·&nbsp;
  <span style="color:#c9a84e;font-weight:600;">{flag} {lang_name}</span>
</div>

<!-- Header -->
<header style="padding:24px 0;border-bottom:1px solid rgba(201,168,78,0.10);">
  <div style="max-width:1100px;margin:0 auto;padding:0 24px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px;">
    <a href="{BASE}/" style="font-size:20px;font-weight:800;color:#f4f4f2;text-decoration:none;">Boat<span style="color:#c9a84e;">RentalMarbella</span></a>
    <a href="{wa_url}" rel="nofollow noopener" target="_blank" style="display:inline-flex;align-items:center;gap:6px;padding:10px 22px;border-radius:50px;background:#25d366;color:#fff;font-size:13px;font-weight:700;text-decoration:none;">💬 WhatsApp</a>
  </div>
</header>

<!-- Hero -->
<section style="padding:64px 24px;text-align:center;">
  <div style="max-width:780px;margin:0 auto;">
    <p style="font-size:12px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#c9a84e;margin-bottom:18px;">⚓ {flag} Marbella · Costa del Sol</p>
    <h1 style="font-size:clamp(32px,5vw,52px);font-weight:800;line-height:1.1;margin:0 0 16px;letter-spacing:-0.02em;">{c["h1"]}</h1>
    <p style="font-size:18px;color:#c9a84e;font-weight:600;margin:0 0 24px;">{c["tagline"]}</p>
    <p style="font-size:16px;color:rgba(244,244,242,0.65);max-width:620px;margin:0 auto 36px;">{c["hero_sub"]}</p>
    <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
      <a href="{wa_url}" rel="nofollow noopener" target="_blank" style="display:inline-flex;align-items:center;gap:8px;padding:14px 32px;border-radius:50px;background:#25d366;color:#fff;font-size:15px;font-weight:700;text-decoration:none;box-shadow:0 4px 18px rgba(37,211,102,0.32);">💬 {c["cta_wa"]}</a>
      <a href="{BASE}/boats/" style="display:inline-flex;align-items:center;gap:8px;padding:14px 32px;border-radius:50px;background:transparent;border:1px solid rgba(201,168,78,0.30);color:#c9a84e;font-size:15px;font-weight:700;text-decoration:none;">{c["cta_browse"]} →</a>
    </div>
  </div>
</section>

<!-- Boats -->
<section style="padding:48px 24px;background:rgba(201,168,78,0.03);border-top:1px solid rgba(201,168,78,0.10);border-bottom:1px solid rgba(201,168,78,0.10);">
  <div style="max-width:1100px;margin:0 auto;">
    <h2 style="font-size:24px;font-weight:800;text-align:center;margin:0 0 36px;">{c["section_boats"]}</h2>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;">
      {boat_cards}
    </div>
  </div>
</section>

<!-- Why us -->
<section style="padding:64px 24px;">
  <div style="max-width:780px;margin:0 auto;">
    <h2 style="font-size:24px;font-weight:800;text-align:center;margin:0 0 28px;">{c["section_why"]}</h2>
    <ul style="list-style:none;padding:0;margin:0;background:#0c1828;border:1px solid rgba(201,168,78,0.18);border-radius:16px;padding:8px 20px;">
      {why_rows}
    </ul>
  </div>
</section>

<!-- Destinations -->
<section style="padding:48px 24px;background:rgba(201,168,78,0.03);border-top:1px solid rgba(201,168,78,0.10);">
  <div style="max-width:780px;margin:0 auto;">
    <h2 style="font-size:22px;font-weight:800;text-align:center;margin:0 0 12px;">{c["h2_destinations"]}</h2>
    <p style="text-align:center;color:rgba(244,244,242,0.55);font-size:14px;margin:0 0 24px;">{c["destinations_intro"]}</p>
    <ul style="list-style:none;padding:0;margin:0;max-width:420px;margin-left:auto;margin-right:auto;">
      {destinations_list}
    </ul>
  </div>
</section>

<!-- Final CTA -->
<section style="padding:64px 24px;text-align:center;">
  <a href="{wa_url}" rel="nofollow noopener" target="_blank" style="display:inline-flex;align-items:center;gap:10px;padding:18px 44px;border-radius:50px;background:#25d366;color:#fff;font-size:17px;font-weight:700;text-decoration:none;box-shadow:0 6px 24px rgba(37,211,102,0.40);">💬 {c["cta_wa"]}</a>
</section>

<!-- Footer with language switcher -->
<footer style="padding:32px 24px;border-top:1px solid rgba(201,168,78,0.10);background:rgba(0,0,0,0.3);">
  <div style="max-width:1100px;margin:0 auto;">
    <p style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.10em;color:#c9a84e;margin:0 0 12px;">Language / Idioma / Sprache</p>
    {switcher}
    <p style="font-size:12px;color:rgba(244,244,242,0.35);margin:24px 0 0;">© {date.today().year} BoatRentalInMarbella · {PHONE} · {SITE.get("email", "hello@boatrentalinmarbella.com")}</p>
  </div>
</footer>

</body>
</html>
'''

    out_dir = SITE_DIR / code
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(html_out)
    print(f"  ✓ /{code}/index.html")


def main():
    print("Building language hubs:")
    for code, name, flag, dir_ in LANGUAGES:
        build_hub(code, name, flag, dir_)
    print(f"\nDone — {len(LANGUAGES)} languages built.")


if __name__ == "__main__":
    main()
