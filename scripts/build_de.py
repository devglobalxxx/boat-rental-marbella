#!/usr/bin/env python3
"""Build the German (DE) subset: /de/ hub + 3 priority spokes.

Mirrors build_es.py but with German prose. German market is the second-biggest
inbound charter market in Marbella after UK.
"""
from __future__ import annotations
import json, pathlib, html
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "templates" / "page.html.template").read_text()
SITE = json.loads((ROOT / "config" / "keyword_map.json").read_text())["site"]
SITE_DIR = ROOT / "site"

WA_NO_PLUS = SITE["whatsapp_e164"].lstrip("+")
WA_LINK = f"https://wa.me/{WA_NO_PLUS}?text=Hallo%2C%20ich%20m%C3%B6chte%20ein%20Boot%20in%20Marbella%20mieten"

PAGES = [
    {
        "slug": "de",
        "en_alt": "/",
        "title": "Bootsverleih Marbella 2026: Yachten, Katamarane & Charter aus Puerto Banús",
        "meta": "Bootsverleih in Marbella ab €749 für 2h auf unseren 12,5 m Flybridge-Motoryachten (Astondoa 40 + Azimut 39). Abfahrt Puerto Banús. Skipper, Treibstoff, Getränke, MwSt. inklusive.",
        "h1": "Bootsverleih Marbella — 17-Boote-Flotte, Yachten & Katamarane",
        "sub": "Direkter Anbieter aus Puerto Banús. Skipper, Treibstoff, Getränke und 21% IVA inklusive. WhatsApp-Antwort unter 5 Minuten.",
        "eyebrow": "Marbella · Puerto Banús",
        "hero_base": "/img/boats/mangusta-80/hero",
        "hero_alt": "Mangusta 80 — größte Charter-Yacht in Marbella, mit La Concha Berg im Hintergrund",
        "breadcrumb_name": "Bootsverleih",
        "body": """
<p>Bootsverleih in Marbella, betrieben direkt aus Puerto Banús. Wir sind keine Marketplace — jedes Boot auf dieser Seite wird von uns oder unseren Skipper-Partnern selbst betrieben. Skipper, Treibstoff, Getränke (Bier, Weißwein, Cava, Wasser), Snacks, Versicherung und 21% spanische MwSt. sind in jedem Charter enthalten. Preise ab <strong>€749 für 2 Stunden</strong> bis <strong>€2.299 für einen ganzen 8-Stunden-Tag</strong>.</p>

<h2>Unsere Hauptflotte</h2>
<ul>
  <li><strong><a href="/boats/astondoa-40/">Astondoa 40 'Fufi'</a></strong> — spanische 12,5 m Yacht, bis zu 9 Gäste, klassisches Teakholz-Interieur. €749/2h.</li>
  <li><strong><a href="/boats/azimut-39/">Azimut 39</a></strong> — italienische 12,5 m Flybridge-Yacht, bis zu 11 Gäste, modernes Sonnendeck. €749/2h.</li>
  <li><strong><a href="/boats/mangusta-80/">Mangusta 80 'Nina'</a></strong> — die größte Charter-Yacht in Marbella, 24 m, inklusive Jetski. €4.719 ab 4h.</li>
</ul>

<h2>Was inklusive ist</h2>
<p>Lizenzierter Skipper · Treibstoff für die Standard-Küstenroute · Bier · Weißwein · Cava · alkoholfreie Getränke · Wasser · Eis · leichte Snacks · Schnorchelausrüstung · Donut · Paddleboard · Handtücher · Versicherung · Spanische IVA (MwSt. 21%).</p>

<h2>Abfahrtshäfen</h2>
<p><strong>Puerto Banús</strong> ist der Hauptabfahrtshafen — die meisten Yachten ab 12 m starten hier. Alternative Pickup-Punkte: Marbella Marina (zentral), Cabopino (östlich, dünenfreundlich), Estepona und Sotogrande auf Anfrage. Siehe <a href="/boat-rental-puerto-banus/">Bootsverleih Puerto Banús</a> für Details zum Hauptmarina.</p>

<h2>Buchung in 60 Sekunden</h2>
<ol>
  <li><strong>WhatsApp an Andra</strong> mit Datum, Gruppengröße und Budget — sofortiges Angebot.</li>
  <li><strong>50% Anzahlung</strong> sichert das Datum, Rest am Tag des Charters.</li>
  <li><strong>Skipper holt euch ab</strong> in Puerto Banús — fertig.</li>
</ol>
<p>Tippt auf den <strong>Buchen</strong>-Button oben oder direkt auf <a href="""" + WA_LINK + """">WhatsApp schreiben</a>.</p>

<h2>Lizenzregeln in Spanien</h2>
<p>Du brauchst <strong>keinen spanischen Bootsführerschein</strong>, wenn (a) das Boot unter 5 m Länge / 15 PS bleibt (führerscheinfrei), oder (b) du mit Skipper buchst — was bei ~95% unserer Charters der Fall ist. Wenn du eine deutsche SBF-See oder höher hast, kannst du bestimmte größere Boote selbst steuern — bring das Original-Zertifikat mit.</p>

<h2>Häufige Fragen</h2>
<details><summary>Wie viel kostet ein Boot in Marbella?</summary><p>Ab €749 für 2 Stunden auf unseren 12,5 m Yachten (Astondoa oder Azimut), bis €2.299 für einen ganzen 8-Stunden-Tag. Skipper, Treibstoff, Getränke, MwSt. und Versicherung inklusive — kein Aufpreis am Hafen.</p></details>
<details><summary>Brauche ich einen Bootsführerschein?</summary><p>Nein — alle skipperten Charters auf dieser Seite sind führerscheinfrei für dich. Du kannst dich entspannt zurücklehnen.</p></details>
<details><summary>Was ist die beste Reisezeit?</summary><p>Juni und September sind ideal — warmes Meerwasser (22-24°C), wenig Wind, etwas günstiger als Hochsaison. Juli/August sind voll und manchmal windig am Nachmittag.</p></details>
<details><summary>Kann ich auf Deutsch reservieren?</summary><p>Ja — Andra antwortet auf Deutsch, Englisch, Spanisch und Estnisch. Schreib einfach auf WhatsApp.</p></details>
"""
    },
    {
        "slug": "de/yachtcharter-marbella",
        "en_alt": "/yacht-charter-marbella/",
        "title": "Yachtcharter Marbella 2026: Luxusyachten ab €749 / 2h",
        "meta": "Yachtcharter Marbella ab €749 für 2h. Astondoa 40 oder Azimut 39 mit Skipper, Treibstoff, Getränke & MwSt. — direkter Buchung über WhatsApp.",
        "h1": "Yachtcharter Marbella — Luxusyachten aus Puerto Banús",
        "sub": "Astondoa 40 oder Azimut 39 — 12,5 m Flybridge-Yachten ab €749/2h. Skipper, Treibstoff, Drinks und 21% MwSt. immer inklusive.",
        "eyebrow": "Yachtcharter · Marbella",
        "hero_base": "/img/boats/azimut-39/hero",
        "hero_alt": "Azimut 39 Yachtcharter Marbella — italienische Flybridge-Motoryacht",
        "breadcrumb_name": "Yachtcharter",
        "body": """
<p>Yachtcharter in Marbella ab €749 für 2 Stunden auf unseren beiden 12,5 m Flybridge-Yachten — der <a href="/boats/astondoa-40/">Astondoa 40 'Fufi'</a> oder der <a href="/boats/azimut-39/">Azimut 39</a>. Beide ab Puerto Banús. Beide mit Skipper, Treibstoff, Getränken (Bier, Weißwein, Cava, alkoholfrei), leichten Snacks, Schnorchelausrüstung und 21% MwSt. inklusive.</p>

<h2>Astondoa oder Azimut?</h2>
<ul>
  <li><strong>Astondoa 40 'Fufi'</strong> — spanisch gebaut, klassisches Teakholz-und-Creme-Interieur, bis zu 9 Gäste. Ideal für Paare und Gruppen bis 8.</li>
  <li><strong>Azimut 39</strong> — italienische Flybridge, modern, bis zu 11 Gäste. Für größere Gruppen oder wenn das Sonnendeck wichtig ist.</li>
</ul>
<p>Beide gleicher Preis (€749/2h → €2.299/8h), gleicher Hafen (Puerto Banús), gleiches All-Inclusive-Paket.</p>

<h2>Was eine 2-stündige Tour kostet</h2>
<table>
<thead><tr><th>Dauer</th><th>Preis</th><th>Was du bekommst</th></tr></thead>
<tbody>
<tr><td>2 Stunden</td><td><strong>€749</strong></td><td>Schnelle Tour entlang der Goldenen Meile, ein Schwimmstopp</td></tr>
<tr><td>4 Stunden</td><td>€1.299</td><td>Halbtag — Mittagessen + Schwimmen</td></tr>
<tr><td>6 Stunden</td><td>€1.799</td><td>Zwei Schwimmstopps, Paddleboard, richtiger Tagesausflug</td></tr>
<tr><td>8 Stunden</td><td><strong>€2.299</strong></td><td>Ganzer Tag — Sotogrande oder Cabopino Routen</td></tr>
</tbody>
</table>
<p>Größere Gruppen (12+) auf der <a href="/boats/mangusta-80/">Mangusta 80</a> ab €4.719 für 4 Stunden.</p>

<h2>Buchung</h2>
<p>WhatsApp an Andra mit Datum + Gruppengröße — Antwort in unter 5 Minuten in der Marbella-Tageszeit. Keine Anzahlung bis zur Bestätigung.</p>
"""
    },
    {
        "slug": "de/bootsverleih-puerto-banus",
        "en_alt": "/boat-rental-puerto-banus/",
        "title": "Bootsverleih Puerto Banús: Marbella's Top-Marina für Yachten",
        "meta": "Bootsverleih Puerto Banús — der wichtigste Yachthafen Marbellas. Ab €749/2h für skipperte Charters. Tiefe Liegeplätze, Luxusboutiquen-Promenade.",
        "h1": "Bootsverleih Puerto Banús — Marbellas führender Yachthafen",
        "sub": "Tiefliegeplätze, Ferrari-Promenade, der Hauptstart für jeden Yachtcharter in Marbella.",
        "eyebrow": "Puerto Banús · Marbella",
        "hero_base": "/img/boats/astondoa-40/lifestyle",
        "hero_alt": "Charter-Yacht in Puerto Banús, Marbella — Bootsverleih",
        "breadcrumb_name": "Puerto Banús",
        "body": """
<p>Puerto Banús ist der primäre Hafen für Yachtcharter in Marbella — der größte Marina an der Costa del Sol, mit den tiefsten Liegeplätzen, der berühmten Boutique-Promenade und direktem Zugang zur Goldenen Meile. Fast jede Yacht über 12 m startet von hier, einschließlich unserer gesamten Hauptflotte.</p>

<h2>Was Puerto Banús besonders macht</h2>
<ul>
  <li><strong>Tiefliegeplätze</strong> — Yachten bis 80 m liegen hier. Astondoa 40, Azimut 39 und Mangusta 80 sind alle hier stationiert.</li>
  <li><strong>Luxus-Promenade</strong> — Louis Vuitton, Cartier, Hermès, Sea Grill, Casanis, La Sala — alles 2 Minuten zu Fuß vom Pontoon.</li>
  <li><strong>Parken</strong> — der Hafen hat sein eigenes Parkhaus, €1.50/Stunde, immer Plätze verfügbar.</li>
  <li><strong>Nightlife</strong> — Olivia Valere, La Sala Banús, Pangea sind alle 5 Minuten vom Hafen.</li>
</ul>

<h2>Wie du Puerto Banús erreichst</h2>
<p>Vom Flughafen Málaga (AGP): 50 Minuten mit Taxi/Uber (~€85) oder Mietwagen über die AP-7. Vom Flughafen Gibraltar: 45 Minuten. Vom Bahnhof Marbella zur Marina: 12 Minuten mit Taxi.</p>

<h2>Yacht-Pickup-Punkt</h2>
<p>Wir treffen euch am Eingang zum Hafen-Bürozentrum (Marina Office), 5 Minuten vor der gebuchten Charter-Zeit. Andra schickt euch den genauen Pin per WhatsApp 24 Stunden vor dem Charter.</p>

<h2>Andere Häfen</h2>
<p>Wenn Puerto Banús zu hektisch ist, bieten wir auch Pickup in <strong>Marbella Marina</strong> (zentral, ruhiger), <strong>Cabopino</strong> (östlich, dünenfreundlich) oder <strong>Sotogrande</strong> (westlich, für Polo-Liebhaber). Schreib auf WhatsApp, wenn du einen anderen Pickup brauchst.</p>
"""
    },
    {
        "slug": "de/bootsverleih-ohne-fuehrerschein-marbella",
        "en_alt": "/boat-rental-no-license-marbella/",
        "title": "Bootsverleih ohne Führerschein Marbella: 5m / 15PS-Selbstfahrer",
        "meta": "Bootsverleih ohne Führerschein in Marbella — selbst fahren bis 5m Bootslänge / 15PS Motor, innerhalb 2 NM von der Küste. Ab €230/2h.",
        "h1": "Bootsverleih Marbella ohne Führerschein — Selbstfahrer 5m / 15PS",
        "sub": "Bis 5 m Bootslänge, 15 PS Motor, 2 Seemeilen von der Küste, Tageslicht, Kapitän mindestens 18. Ab €230/2h.",
        "eyebrow": "Führerscheinfrei · Selbstfahrer",
        "hero_base": "/img/boats/dubhe/hero",
        "hero_alt": "Dubhe — führerscheinfreies Boot in Puerto Banús, Marbella",
        "breadcrumb_name": "Ohne Führerschein",
        "body": """
<p>In Spanien kannst du ein Boot ohne Lizenz mieten, solange folgende Regeln eingehalten werden: <strong>maximal 5 m Rumpflänge, maximal 15 PS Motor, innerhalb 2 Seemeilen von der Küste, nur bei Tageslicht, Kapitän mindestens 18 Jahre alt</strong>. Auf dieser Basis bieten wir mehrere führerscheinfreie Boote ab Puerto Banús — billigstes ab €230 für 2 Stunden.</p>

<h2>Unser kleinster Selbstfahrer: Dubhe</h2>
<ul>
  <li><strong>Bis zu 5 Personen</strong></li>
  <li><strong>Bimini-Sonnenschutz</strong></li>
  <li><strong>Ab Puerto Banús</strong></li>
  <li><strong>Sicher &amp; komfortabel</strong></li>
  <li><strong>Treibstoff nicht inklusive</strong> (~€15-€25 für 2 Stunden Küstenfahrt)</li>
</ul>

<h2>Preise</h2>
<table>
<thead><tr><th>Dauer</th><th>Preis</th></tr></thead>
<tbody>
<tr><td>2 Stunden</td><td><strong>€230</strong></td></tr>
<tr><td>3 Stunden</td><td>€280</td></tr>
<tr><td>4 Stunden</td><td><strong>€350</strong></td></tr>
</tbody>
</table>

<h2>Was du selbst mitbringen musst</h2>
<ul>
  <li><strong>Pass oder EU-Personalausweis</strong> (Original)</li>
  <li><strong>Bargeld oder Karte</strong> für Treibstoff am Ende</li>
  <li><strong>Sonnencreme, Hut, Wasser</strong></li>
</ul>

<h2>Was wir am Pier zeigen</h2>
<p>15-minütige Einweisung: Starten, Lenkung, Gas, Wenden, Notfälle, lokale Boje, Hafenausfahrt. Auf Deutsch, Englisch, Spanisch oder Estnisch. Wir lassen niemanden raus, der nicht klar ist mit der Bedienung.</p>

<h2>Buchung</h2>
<p>WhatsApp an <a href="""" + WA_LINK + """">Andra</a> mit Datum + Anzahl Personen — direktes Angebot. Stornierung 7+ Tage vorher = 100% Rückerstattung.</p>
"""
    },
]


def render(p):
    widths = [600, 900, 1200, 1600]
    hero_srcset = ", ".join(f"{p['hero_base']}-{w}.jpg {w}w" for w in widths)
    hero_img = f"{p['hero_base']}-1600.jpg"

    jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": ["LocalBusiness", "Organization"],
        "@id": SITE["base_url"] + "/#org",
        "name": SITE["name"],
        "url": SITE["base_url"] + "/",
        "logo": SITE["base_url"] + "/img/logo-480.png",
        "telephone": SITE["phone_e164"],
        "email": SITE["email"],
        "sameAs": [u for u in [SITE.get("instagram_url"), SITE.get("facebook_url")] if u],
        "priceRange": f"€{SITE['price_anchor_low_2h']}–€{SITE['price_anchor_fullday_8h']}",
        "address": {"@type": "PostalAddress", "addressLocality": "Marbella", "addressRegion": "Andalucía", "addressCountry": "ES"},
        "inLanguage": "de",
    }, ensure_ascii=False, separators=(",", ":"))

    canonical = f"{SITE['base_url']}/{p['slug']}/"

    breadcrumbs = (
        '<nav class="breadcrumbs" aria-label="Breadcrumb">'
        f'<a href="/de/">Bootsverleih</a> › <span>{html.escape(p["breadcrumb_name"])}</span></nav>'
        if p["slug"] != "de" else
        '<nav class="breadcrumbs" aria-label="Breadcrumb"><span>Bootsverleih Marbella</span></nav>'
    )

    sub = {
        "{{TITLE}}": html.escape(p["title"]),
        "{{META_DESCRIPTION}}": html.escape(p["meta"]),
        "{{CANONICAL_URL}}": canonical,
        "{{HREFLANG}}": (
            f'<link rel="alternate" hreflang="en" href="{SITE["base_url"]}{p["en_alt"]}">'
            f'<link rel="alternate" hreflang="de" href="{canonical}">'
            f'<link rel="alternate" hreflang="x-default" href="{SITE["base_url"]}{p["en_alt"]}">'
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
        "{{LANG_SWITCHER}}": f'<a href="{p["en_alt"]}" hreflang="en" rel="alternate">EN</a><span class="sep">|</span><a href="/es/" hreflang="es" rel="alternate">ES</a><span class="sep">|</span><strong>DE</strong>',
        "{{LANG_SWITCHER_FOOTER}}": f'<a href="{p["en_alt"]}" hreflang="en" rel="alternate">🇬🇧 English</a> &nbsp;·&nbsp; <a href="/es/" hreflang="es" rel="alternate">🇪🇸 Español</a> &nbsp;·&nbsp; <strong>🇩🇪 Deutsch</strong>',
        "{{HERO_IMG}}": hero_img,
        "{{HERO_IMG_ABS}}": SITE["base_url"] + hero_img,
        "{{HERO_SRCSET}}": html.escape(hero_srcset),
        "{{HERO_ALT}}": html.escape(p["hero_alt"]),
        "{{HERO_EYEBROW}}": f'<span class="eyebrow">{html.escape(p["eyebrow"])}</span>',
        "{{HERO_H1}}": html.escape(p["h1"]),
        "{{HERO_SUB}}": html.escape(p["sub"]),
        "{{PRICE_LOW}}": str(SITE["price_anchor_low_2h"]),
        "{{PRICE_LABEL}}": "2h Charter mit Skipper",
        "{{BOAT_GRID}}": "",
        "{{BREADCRUMBS}}": breadcrumbs,
        "{{BODY_HTML}}": p["body"],
        "{{MAP_BLOCK}}": "",
        "{{GUESTS_SECTION}}": "",
        "{{VIDEO_SECTION}}": "",
        "{{BOOK_PITCH}}": "WhatsApp jetzt — durchschnittliche Antwort in unter 5 Minuten. Keine Anzahlung bis zur Bestätigung.",
    }
    out = TEMPLATE
    for k, v in sub.items():
        out = out.replace(k, str(v))
    out_dir = SITE_DIR / p["slug"]
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(out)
    print(f"  ✓ /{p['slug']}/")


def main():
    print("=== German (DE) locale ===")
    for p in PAGES:
        render(p)


if __name__ == "__main__":
    main()
