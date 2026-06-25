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
    {
        "slug": "de/katamaran-mieten-marbella",
        "en_alt": "/catamaran-rental-marbella/",
        "title": "Katamaran mieten Marbella 2026: stabil, geräumig, familienfreundlich",
        "meta": "Katamaran mieten in Marbella — Doppelrumpf-Stabilität, große Sonnenflächen, ideal für Familien & Gruppen. Ab €749/2h mit Skipper, Getränken & MwSt. ab Puerto Banús.",
        "h1": "Katamaran mieten Marbella — stabil, geräumig, ideal für Familien",
        "sub": "Doppelrumpf, kaum Schaukeln, riesige Liegeflächen und flacher Tiefgang für versteckte Buchten. Ab €749/2h mit Skipper.",
        "eyebrow": "Katamaran · Marbella",
        "hero_base": "/img/boats/lagoon-380/hero",
        "hero_alt": "Lagoon 380 Segelkatamaran-Charter in Marbella",
        "breadcrumb_name": "Katamaran mieten",
        "body": f"""
<p>Ein Katamaran ist die ruhigste und stabilste Art, die Küste von Marbella zu erleben. Durch die zwei Rümpfe schaukelt er kaum — perfekt für Familien mit Kindern, Großeltern oder alle, die seekrankheitsempfindlich sind. Dazu kommt viel mehr Deckfläche als auf einer gleich langen Motoryacht: ein großes Trampolin am Bug, ein schattiger Cockpit-Bereich und breite Sonnenliegen. Unser <a href="/boats/lagoon-380/">Lagoon 380</a> startet ab Puerto Banús.</p>

<h2>Warum ein Katamaran in Marbella?</h2>
<ul>
  <li><strong>Stabilität</strong> — fast kein Rollen, ideal gegen Seekrankheit.</li>
  <li><strong>Platz</strong> — Trampolin-Netze am Bug zum Sonnen, separater Schattenbereich.</li>
  <li><strong>Flacher Tiefgang</strong> — kommt näher an Strände und kleine Buchten (Calas) als eine tiefkielige Yacht.</li>
  <li><strong>Familienfreundlich</strong> — Kinder können sich sicher bewegen, viel Platz für Schwimmpausen.</li>
</ul>

<h2>Preise</h2>
<table>
<thead><tr><th>Dauer</th><th>Preis</th><th>Ideal für</th></tr></thead>
<tbody>
<tr><td>2 Stunden</td><td><strong>€749</strong></td><td>Schnuppertour + ein Schwimmstopp</td></tr>
<tr><td>4 Stunden</td><td>€1.299</td><td>Halbtag mit Mittagessen an Bord</td></tr>
<tr><td>6 Stunden</td><td>€1.799</td><td>Mehrere Buchten, Paddleboard, Schnorcheln</td></tr>
<tr><td>8 Stunden</td><td><strong>€2.299</strong></td><td>Ganzer Tag — bis Sotogrande oder Cabopino</td></tr>
</tbody>
</table>
<p>Skipper, Treibstoff, Getränke, Schnorchelausrüstung und 21% MwSt. sind inklusive. Größere Gruppen sehen sich die <a href="/de/familien-yachtcharter-marbella/">Familien-Yachtcharter</a> oder die <a href="/de/luxusyacht-mieten-marbella/">Luxusyachten</a> an.</p>

<h2>Häufige Fragen</h2>
<details><summary>Ist ein Katamaran gut gegen Seekrankheit?</summary><p>Ja — die zwei Rümpfe machen ihn deutlich stabiler als ein Einrumpfboot. Wer schnell seekrank wird, ist hier am besten aufgehoben.</p></details>
<details><summary>Wie viele Personen passen drauf?</summary><p>Komfortabel für Familien und Gruppen bis ~10 Personen tagsüber. Schreib uns die genaue Gruppengröße auf <a href="{WA_LINK}">WhatsApp</a> und wir empfehlen das passende Boot.</p></details>
<details><summary>Wo startet der Katamaran?</summary><p>Ab <a href="/de/bootsverleih-puerto-banus/">Puerto Banús</a>. Pickup in Marbella Marina, Cabopino oder Estepona auf Anfrage möglich.</p></details>
"""
    },
    {
        "slug": "de/angelboot-mieten-marbella",
        "en_alt": "/fishing-boat-rental-marbella/",
        "title": "Angelboot mieten Marbella: Hochsee-Angeln Costa del Sol ab €220",
        "meta": "Angelboot mieten in Marbella — geführtes Hochsee- und Küstenangeln an der Costa del Sol. Bis 6 Angler, Ausrüstung & Skipper inklusive. Ab €220 für eine Tour.",
        "h1": "Angelboot mieten Marbella — geführtes Hochsee-Angeln",
        "sub": "Thunfisch, Bonito, Dorade und Tintenfisch vor Marbella. Bis 6 Angler, Ruten und Köder inklusive, lizenzierter Skipper an Bord.",
        "eyebrow": "Angeln · Costa del Sol",
        "hero_base": "/img/boats/red-tide-fishing-boat/hero",
        "hero_alt": "Angelboot-Charter in Marbella — Hochsee-Angeln Costa del Sol",
        "breadcrumb_name": "Angelboot mieten",
        "body": f"""
<p>Die Gewässer vor Marbella und der Costa del Sol sind reich an Fisch — Bonito, Thunfisch, Dorade, Wolfsbarsch und im Spätsommer Tintenfisch. Wir bieten geführte Angeltouren mit lizenziertem Skipper, der die produktiven Stellen kennt. Ruten, Rollen und Köder sind an Bord; du brauchst nur Sonnenschutz und gute Laune. <strong>Bis zu 6 Angler</strong> pro Tour.</p>

<h2>Tourarten</h2>
<ul>
  <li><strong>Küstenangeln (Halbtag)</strong> — entspanntes Angeln nah an der Küste, gut für Einsteiger und Familien. Ab €220.</li>
  <li><strong>Hochsee-Angeln (Ganztag)</strong> — weiter raus für größere Fische, Big-Game-Stil.</li>
  <li><strong>Nacht-Tintenfischangeln</strong> — saisonal, mit Lichtern, ein besonderes Erlebnis.</li>
</ul>

<h2>Was inklusive ist</h2>
<p>Lizenzierter Skipper · Angelausrüstung (Ruten, Rollen, Köder) · Treibstoff · Wasser und alkoholfreie Getränke · Versicherung · MwSt. Der gefangene Fisch gehört dir — viele Restaurants in Puerto Banús bereiten ihn dir am Abend zu.</p>

<h2>Brauche ich eine Angellizenz?</h2>
<p>Für Touren mit unserem Skipper ist die Bootslizenz abgedeckt. Eine persönliche andalusische Freizeit-Angellizenz wird für das Angeln empfohlen — wir erklären dir auf <a href="{WA_LINK}">WhatsApp</a>, wie du sie in 5 Minuten online bekommst. Mehr zu den allgemeinen Regeln im <a href="/de/blog/bootsfuehrerschein-spanien/">Bootsführerschein-Guide für Spanien</a>.</p>

<h2>Buchung</h2>
<p>Schreib uns Datum, Anzahl Angler und gewünschte Tourart. Frühe Vormittage (Abfahrt 7–8 Uhr) bringen meist die besten Fänge. Auch als <a href="/de/privat-bootscharter-marbella/">privater Charter</a> kombinierbar mit Schwimmen und Schnorcheln.</p>
"""
    },
    {
        "slug": "de/sonnenuntergang-bootstour-marbella",
        "en_alt": "/sunset-cruise-marbella/",
        "title": "Sonnenuntergang-Bootstour Marbella: Sunset Cruise ab €749",
        "meta": "Sonnenuntergang-Bootstour in Marbella — Cava an Deck, goldenes Licht über der Goldenen Meile, Skipper inklusive. Ab €749/2h ab Puerto Banús.",
        "h1": "Sonnenuntergang-Bootstour Marbella — Cava, Goldlicht, La Concha",
        "sub": "Die schönste Tageszeit auf dem Wasser: warmes Licht, ruhige See, Cava in der Hand. Ab €749 für 2 Stunden mit Skipper.",
        "eyebrow": "Sunset Cruise · Marbella",
        "hero_base": "/img/boats/azimut-39/hero",
        "hero_alt": "Sonnenuntergang-Bootstour Marbella — Yacht im Abendlicht",
        "breadcrumb_name": "Sonnenuntergang-Tour",
        "body": f"""
<p>Der späte Nachmittag ist die magischste Zeit, um vor Marbella aufs Wasser zu gehen: Der Wind legt sich, die See wird glatt, und die Sonne taucht den Berg La Concha und die Skyline von Puerto Banús in goldenes Licht. Unsere Sonnenuntergang-Touren starten so, dass ihr genau zum Sonnenuntergang mit einem Glas Cava in der Hand draußen seid.</p>

<h2>Was eine Sunset-Tour besonders macht</h2>
<ul>
  <li><strong>Cava & Getränke an Deck</strong> — angestoßen wird, wenn die Sonne den Horizont berührt.</li>
  <li><strong>Ruhigste See des Tages</strong> — abends ist das Wasser meist spiegelglatt.</li>
  <li><strong>Bestes Licht für Fotos</strong> — perfekt auch für <a href="/de/privat-bootscharter-marbella/">private Anlässe</a>, Heiratsanträge oder Jubiläen.</li>
  <li><strong>Schwimmstopp möglich</strong> — bei warmem Wasser ein Bad im Abendlicht.</li>
</ul>

<h2>Zeiten & Preis</h2>
<p>Die ideale 2-Stunden-Tour startet je nach Jahreszeit zwischen 18:30 und 20:30 Uhr. Preis <strong>ab €749</strong> für 2 Stunden auf einer 12,5 m Yacht (<a href="/boats/astondoa-40/">Astondoa 40</a> oder <a href="/boats/azimut-39/">Azimut 39</a>) — Skipper, Treibstoff, Cava, Getränke und MwSt. inklusive. Für einen feierlichen Anlass empfehlen sich auch die <a href="/de/luxusyacht-mieten-marbella/">Luxusyachten</a>.</p>

<h2>Häufige Fragen</h2>
<details><summary>Wann genau geht die Sonne unter?</summary><p>Im Hochsommer gegen 21:30 Uhr, im Frühling/Herbst gegen 19:00–20:00 Uhr. Wir stimmen die Startzeit auf den exakten Sonnenuntergang ab — sag uns einfach dein Datum.</p></details>
<details><summary>Ist das romantisch genug für einen Heiratsantrag?</summary><p>Sehr — schreib uns vorab auf <a href="{WA_LINK}">WhatsApp</a>, wir kümmern uns diskret um Extras wie Blumen oder eine Torte.</p></details>
"""
    },
    {
        "slug": "de/bootsparty-marbella",
        "en_alt": "/boat-party-marbella/",
        "title": "Bootsparty Marbella 2026: Party-Yacht mieten ab Puerto Banús",
        "meta": "Bootsparty in Marbella — Party-Yacht mit Sound-System, DJ-Option und Drinks an Bord. Ideal für Junggesellenabschiede & Gruppen. Ab Puerto Banús buchen.",
        "h1": "Bootsparty Marbella — Party-Yacht mit Musik & Drinks",
        "sub": "Sound-System an Bord, Schwimmstopps, Drinks und Sonnendeck. Perfekt für Junggesellenabschiede, Geburtstage und Gruppen.",
        "eyebrow": "Bootsparty · Puerto Banús",
        "hero_base": "/img/boats/mangusta-80/hero",
        "hero_alt": "Party-Yacht Marbella — Bootsparty in Puerto Banús",
        "breadcrumb_name": "Bootsparty",
        "body": f"""
<p>Marbella ist die Partyhauptstadt der Costa del Sol — und nichts toppt eine Party auf dem Wasser. Unsere Party-Yachten haben ein Sound-System an Bord, große Sonnendecks und Platz zum Tanzen, Schwimmen und Feiern. Auf der Flaggschiff-Yacht <a href="/boats/mangusta-80/">Mangusta 80 'Nina'</a> (24 m) ist sogar ein Jetski dabei.</p>

<h2>Perfekt für</h2>
<ul>
  <li><strong>Junggesellen- & Junggesellinnenabschiede</strong> — siehe auch <a href="/de/privat-bootscharter-marbella/">privater Charter</a>.</li>
  <li><strong>Geburtstage</strong> — wir dekorieren auf Wunsch.</li>
  <li><strong>Firmenfeiern & Gruppen</strong> — Teambuilding mit Schwimmstopp und Drinks.</li>
  <li><strong>DJ-Boot</strong> — auf Anfrage ein DJ an Bord.</li>
</ul>

<h2>Was an Bord ist</h2>
<p>Bluetooth-Sound-System · gekühlte Getränke (Bier, Wein, Cava, alkoholfrei) · Eis · Schwimmplattform · Paddleboard · Donut · große Liegeflächen. Auf Wunsch organisieren wir Catering, Champagner-Pakete oder einen DJ.</p>

<h2>Preise & Gruppengröße</h2>
<p>Die 12,5 m Yachten (<a href="/de/yachtcharter-marbella/">Astondoa 40 / Azimut 39</a>) fassen tagsüber bis ~11 Gäste ab €749/2h. Für größere Gruppen und das ganz große Fest ist die <a href="/de/luxusyacht-mieten-marbella/">Mangusta 80</a> ab €4.719/4h die richtige Wahl. Beachte die <a href="/de/bootsparty-marbella/">Gruppengrößen-Limits</a> der spanischen Behörden — wir beraten dich auf <a href="{WA_LINK}">WhatsApp</a>.</p>

<h2>Wichtig zu wissen</h2>
<p>An Bord gelten Sicherheitsregeln des Skippers; Glasflaschen und übermäßiger Alkohol sind eingeschränkt. Die Party läuft entlang der Küste mit Schwimmstopps — keine durchgehende Hochsee-Fahrt, damit alle sicher feiern können.</p>
"""
    },
    {
        "slug": "de/luxusyacht-mieten-marbella",
        "en_alt": "/luxury-yacht-rental-marbella/",
        "title": "Luxusyacht mieten Marbella: Superyacht-Charter ab Puerto Banús",
        "meta": "Luxusyacht mieten in Marbella — Premium-Yachten wie die Mangusta 80 mit Crew, Jetski & Wassersport. Ab €4.719 für 4h ab Puerto Banús.",
        "h1": "Luxusyacht mieten Marbella — Premium-Charter mit Crew",
        "sub": "Die größten und schönsten Yachten an der Costa del Sol, mit Crew, Wasserspielzeug und vollem Service. Flaggschiff: Mangusta 80 'Nina'.",
        "eyebrow": "Luxus · Marbella",
        "hero_base": "/img/boats/mangusta-80/hero",
        "hero_alt": "Mangusta 80 Luxusyacht-Charter Marbella",
        "breadcrumb_name": "Luxusyacht mieten",
        "body": f"""
<p>Für besondere Anlässe geht in Marbella nichts über eine echte Luxusyacht. Unser Flaggschiff, die <a href="/boats/mangusta-80/">Mangusta 80 'Nina'</a>, ist mit 24 m die größte Charter-Yacht der Region — italienisches Design, mehrere Decks, Innensalon, und ein eigener Jetski plus Wassersportausrüstung an Bord.</p>

<h2>Die Luxusflotte</h2>
<ul>
  <li><strong><a href="/boats/mangusta-80/">Mangusta 80 'Nina'</a></strong> — 24 m Flaggschiff, ab €4.719/4h, Jetski inklusive.</li>
  <li><strong><a href="/boats/maiora-26m/">Maiora 26 m</a></strong> — klassische Superyacht-Eleganz für größere Gruppen.</li>
  <li><strong><a href="/boats/canados-86/">Canados 86</a></strong> & <strong><a href="/boats/ferretti-94/">Ferretti 94</a></strong> — auf Anfrage für den ganz großen Auftritt.</li>
</ul>

<h2>Was Luxus hier bedeutet</h2>
<p>Professionelle Crew (Skipper + Deckhand) · Premium-Getränke und Champagner-Option · Catering auf Wunsch · Wasserspielzeug (Jetski, Seabob, Paddleboard, Donut) · klimatisierter Innenbereich · diskreter, persönlicher Service. Ideal für <a href="/de/sonnenuntergang-bootstour-marbella/">Sunset-Feiern</a>, Anträge, Jubiläen oder VIP-Gäste.</p>

<h2>Preise</h2>
<p>Luxus-Charter starten bei <strong>€4.719 für 4 Stunden</strong> auf der Mangusta 80. Ganztags- und Mehrtages-Charter (inkl. <a href="/de/tagescharter-marbella/">Tagescharter</a>) auf Anfrage. Jede Anfrage ist individuell — schreib uns deine Wünsche auf <a href="{WA_LINK}">WhatsApp</a> für ein maßgeschneidertes Angebot.</p>
"""
    },
    {
        "slug": "de/jetski-mieten-marbella",
        "en_alt": "/jet-ski-rental-marbella/",
        "title": "Jetski mieten Marbella: Jet-Ski-Verleih ab €200/Stunde",
        "meta": "Jetski mieten in Marbella — geführte Jet-Ski-Touren und Verleih ab Puerto Banús. Ab €200 pro Stunde. Auch als Kombi mit Bootscharter buchbar.",
        "h1": "Jetski mieten Marbella — Jet-Ski-Touren ab Puerto Banús",
        "sub": "Adrenalin auf dem Wasser: geführte Jet-Ski-Touren entlang der Goldenen Meile. Ab €200 pro Stunde.",
        "eyebrow": "Jetski · Marbella",
        "hero_base": "/img/boats/speedboat/hero",
        "hero_alt": "Jetski mieten Marbella — Jet-Ski-Tour Costa del Sol",
        "breadcrumb_name": "Jetski mieten",
        "body": f"""
<p>Ein Jetski ist der schnellste Weg, den Adrenalinkick vor Marbella zu spüren. Wir bieten geführte Jet-Ski-Touren ab Puerto Banús — du fährst selbst, ein Guide führt die Gruppe entlang der Küste zu den schönsten Spots der Goldenen Meile.</p>

<h2>Preise</h2>
<table>
<thead><tr><th>Dauer</th><th>Preis</th></tr></thead>
<tbody>
<tr><td>1 Stunde</td><td><strong>€200</strong></td></tr>
<tr><td>2 Stunden</td><td>€380</td></tr>
<tr><td>Halbtags-Tour</td><td>ab €700</td></tr>
</tbody>
</table>
<p>Schwimmweste und kurze Einweisung inklusive. Preise je nach Saison und Modell — aktuelle Verfügbarkeit auf <a href="{WA_LINK}">WhatsApp</a> bestätigen.</p>

<h2>Brauche ich einen Führerschein?</h2>
<p>Für geführte Touren ist kein Bootsführerschein nötig — der Guide übernimmt die Verantwortung, du fährst innerhalb der Gruppe. Der Fahrer muss volljährig sein. Mehr dazu im <a href="/de/blog/bootsfuehrerschein-spanien/">Führerschein-Guide</a> oder bei den <a href="/de/bootsverleih-ohne-fuehrerschein-marbella/">führerscheinfreien Booten</a>.</p>

<h2>Beliebte Kombi</h2>
<p>Viele Gäste buchen den Jetski als Add-on zu einem <a href="/de/yachtcharter-marbella/">Yachtcharter</a>: Auf der <a href="/boats/mangusta-80/">Mangusta 80</a> ist ein Jetski bereits an Bord. So habt ihr Yacht-Komfort und Jetski-Action am selben Tag.</p>
"""
    },
    {
        "slug": "de/privat-bootscharter-marbella",
        "en_alt": "/private-boat-charter-marbella/",
        "title": "Privater Bootscharter Marbella: exklusiv, nur eure Gruppe",
        "meta": "Privater Bootscharter in Marbella — die ganze Yacht nur für eure Gruppe, kein Sharing. Skipper, Getränke & MwSt. inklusive. Ab €749/2h ab Puerto Banús.",
        "h1": "Privater Bootscharter Marbella — die Yacht nur für euch",
        "sub": "Kein geteiltes Boot, keine Fremden — die komplette Yacht und der Skipper gehören für eure Zeit nur euch. Ab €749/2h.",
        "eyebrow": "Privat · Exklusiv",
        "hero_base": "/img/boats/astondoa-40/hero",
        "hero_alt": "Privater Bootscharter Marbella — exklusive Yacht für die Gruppe",
        "breadcrumb_name": "Privater Charter",
        "body": f"""
<p>Bei uns ist jeder Charter <strong>privat</strong> — ihr teilt das Boot mit niemandem. Die ganze Yacht, der Skipper und die Route gehören für die gebuchte Zeit nur eurer Gruppe. Das macht den Unterschied zu den großen Marketplace-Anbietern: kein Shared-Boat-Modell, keine fremden Gäste an Bord.</p>

<h2>Warum privat besser ist</h2>
<ul>
  <li><strong>Eure Route</strong> — ihr entscheidet, wo geschwommen, geankert und gegessen wird.</li>
  <li><strong>Eure Musik & euer Tempo</strong> — entspannt oder feierlich, ganz wie ihr wollt.</li>
  <li><strong>Ideal für Anlässe</strong> — Geburtstage, Anträge, <a href="/de/sonnenuntergang-bootstour-marbella/">Sunset-Feiern</a>, Familientage.</li>
  <li><strong>Privatsphäre</strong> — perfekt für Paare und kleine Gruppen.</li>
</ul>

<h2>Boot & Preis nach Gruppengröße</h2>
<table>
<thead><tr><th>Gruppe</th><th>Empfohlenes Boot</th><th>Ab Preis</th></tr></thead>
<tbody>
<tr><td>Paar / bis 8</td><td><a href="/boats/astondoa-40/">Astondoa 40</a></td><td>€749/2h</td></tr>
<tr><td>bis 11</td><td><a href="/boats/azimut-39/">Azimut 39</a></td><td>€749/2h</td></tr>
<tr><td>große Gruppe</td><td><a href="/boats/mangusta-80/">Mangusta 80</a></td><td>€4.719/4h</td></tr>
</tbody>
</table>
<p>Alle Preise inkl. Skipper, Treibstoff, Getränke und 21% MwSt. Sag uns Gruppengröße und Anlass auf <a href="{WA_LINK}">WhatsApp</a> — wir empfehlen das passende Boot.</p>
"""
    },
    {
        "slug": "de/speedboot-mieten-marbella",
        "en_alt": "/speedboat-rental-marbella/",
        "title": "Speedboot mieten Marbella: schnelle Boote ab Puerto Banús",
        "meta": "Speedboot mieten in Marbella — schnelle, sportliche Boote für Küstentouren und Wassersport. Mit oder ohne Skipper. Ab Puerto Banús buchen.",
        "h1": "Speedboot mieten Marbella — schnell, sportlich, flexibel",
        "sub": "Sportliche Boote für Tempo, Wassersport und schnelle Küstentrips. Mit Skipper oder als führerscheinfreie Variante.",
        "eyebrow": "Speedboot · Marbella",
        "hero_base": "/img/boats/speedboat/hero",
        "hero_alt": "Speedboot mieten Marbella — sportliches Boot Costa del Sol",
        "breadcrumb_name": "Speedboot mieten",
        "body": f"""
<p>Wer Tempo und Agilität sucht, mietet in Marbella ein Speedboot. Sportliche Boote bringen euch schnell zu den schönsten Buchten, eignen sich für Wassersport (Donut, Wakeboard) und sind ideal für kürzere, dynamische Touren entlang der Goldenen Meile.</p>

<h2>Optionen</h2>
<ul>
  <li><strong>Mit Skipper</strong> — entspannt zurücklehnen, der Skipper bringt euch zu den besten Spots. Kein Führerschein nötig.</li>
  <li><strong>Führerscheinfrei selbst fahren</strong> — kleinere Boote bis 5 m / 15 PS könnt ihr ohne Lizenz selbst steuern, siehe <a href="/de/bootsverleih-ohne-fuehrerschein-marbella/">Boote ohne Führerschein</a> ab €230/2h.</li>
  <li><strong>Sportyacht</strong> — für mehr Komfort und Tempo die <a href="/boats/pershing-46/">Pershing 46</a> oder <a href="/boats/fairline-targa-12m/">Fairline Targa</a>.</li>
</ul>

<h2>Wofür sich ein Speedboot eignet</h2>
<p>Schnelle Hin- und Rückfahrt zu einer Bucht zum Schwimmen · Wassersport-Sessions · Sightseeing entlang der Küste · Paare oder kleine Gruppen, die Action wollen. Für reine Entspannung mit viel Platz sind eine <a href="/de/katamaran-mieten-marbella/">Katamaran-</a> oder <a href="/de/yachtcharter-marbella/">Yacht-Tour</a> die bessere Wahl.</p>

<h2>Buchung</h2>
<p>Schreib uns auf <a href="{WA_LINK}">WhatsApp</a>, ob du mit Skipper oder selbst fahren willst, plus Datum und Gruppengröße — wir machen dir ein passendes Angebot.</p>
"""
    },
    {
        "slug": "de/segelboot-mieten-marbella",
        "en_alt": "/sailboat-rental-marbella/",
        "title": "Segelboot mieten Marbella: Segeltörn an der Costa del Sol",
        "meta": "Segelboot mieten in Marbella — entspannte Segeltörns und Katamaran-Segeln an der Costa del Sol. Mit Skipper, ruhig und nachhaltig. Ab Puerto Banús.",
        "h1": "Segelboot mieten Marbella — entspanntes Segeln mit Skipper",
        "sub": "Wind statt Motor: ruhiges, nachhaltiges Segeln entlang der Goldenen Meile. Segelkatamaran oder Yacht, mit erfahrenem Skipper.",
        "eyebrow": "Segeln · Marbella",
        "hero_base": "/img/boats/lagoon-380/hero",
        "hero_alt": "Segelboot mieten Marbella — Segelkatamaran Costa del Sol",
        "breadcrumb_name": "Segelboot mieten",
        "body": f"""
<p>Segeln ist die ruhigste und nachhaltigste Art, die Küste von Marbella zu genießen — kaum Motorengeräusch, nur Wind und Wasser. Unser Segelkatamaran <a href="/boats/lagoon-380/">Lagoon 380</a> verbindet die Stabilität eines Katamarans mit dem Erlebnis des Segelns, geführt von einem erfahrenen Skipper.</p>

<h2>Warum ein Segeltörn?</h2>
<ul>
  <li><strong>Ruhe</strong> — entspanntes Gleiten ohne Motorlärm.</li>
  <li><strong>Nachhaltig</strong> — geringer Treibstoffverbrauch, wenn unter Segeln.</li>
  <li><strong>Stabil</strong> — als <a href="/de/katamaran-mieten-marbella/">Katamaran</a> kaum Schaukeln, gut gegen Seekrankheit.</li>
  <li><strong>Mitmachen erlaubt</strong> — der Skipper lässt euch gern beim Segeln helfen.</li>
</ul>

<h2>Für wen geeignet</h2>
<p>Paare und Familien, die einen entspannten Tag suchen; Segel-Enthusiasten, die das Steuer mit anpacken wollen; und alle, die statt Party lieber Ruhe und Natur möchten. Die Touren beinhalten Schwimmstopps und Schnorcheln. Wer es schneller mag, schaut sich das <a href="/de/speedboot-mieten-marbella/">Speedboot</a> an.</p>

<h2>Preise & Buchung</h2>
<p>Halbtags- und Ganztagstörns ab Puerto Banús, Skipper, Getränke und MwSt. inklusive. Da Segeltörns wind- und saisonabhängig sind, machen wir dir ein individuelles Angebot — schreib uns Datum und Gruppengröße auf <a href="{WA_LINK}">WhatsApp</a>.</p>
"""
    },
    {
        "slug": "de/motoryacht-mieten-marbella",
        "en_alt": "/motor-yacht-rental-marbella/",
        "title": "Motoryacht mieten Marbella: Flybridge-Yachten ab €749/2h",
        "meta": "Motoryacht mieten in Marbella — moderne Flybridge-Motoryachten mit Skipper. Schnell, komfortabel, ab €749/2h ab Puerto Banús. Getränke & MwSt. inklusive.",
        "h1": "Motoryacht mieten Marbella — Komfort & Tempo mit Flybridge",
        "sub": "Moderne Motoryachten mit oberem Sonnendeck (Flybridge), schnell zwischen den Buchten und komfortabel an Bord. Ab €749/2h.",
        "eyebrow": "Motoryacht · Marbella",
        "hero_base": "/img/boats/azimut-58/hero",
        "hero_alt": "Motoryacht-Charter Marbella — Azimut Flybridge-Yacht",
        "breadcrumb_name": "Motoryacht mieten",
        "body": f"""
<p>Die Motoryacht ist die beliebteste Charter-Wahl in Marbella: schnell genug, um mehrere Buchten an einem Tag zu erreichen, und komfortabel genug für einen entspannten Tag an Deck. Unsere Flybridge-Yachten haben ein oberes Sonnendeck mit Panoramablick über die Costa del Sol.</p>

<h2>Unsere Motoryachten</h2>
<ul>
  <li><strong><a href="/boats/astondoa-40/">Astondoa 40 'Fufi'</a></strong> — 12,5 m, bis 9 Gäste, klassisch-elegant. €749/2h.</li>
  <li><strong><a href="/boats/azimut-39/">Azimut 39</a></strong> — 12,5 m italienische Flybridge, bis 11 Gäste. €749/2h.</li>
  <li><strong><a href="/boats/azimut-58/">Azimut 58</a></strong> & <strong><a href="/boats/pershing-46/">Pershing 46</a></strong> — größer und sportlicher, auf Anfrage.</li>
  <li><strong><a href="/boats/mangusta-80/">Mangusta 80</a></strong> — 24 m Flaggschiff für den großen Auftritt.</li>
</ul>

<h2>Preise</h2>
<table>
<thead><tr><th>Dauer</th><th>Preis (12,5 m)</th></tr></thead>
<tbody>
<tr><td>2 Stunden</td><td><strong>€749</strong></td></tr>
<tr><td>4 Stunden</td><td>€1.299</td></tr>
<tr><td>6 Stunden</td><td>€1.799</td></tr>
<tr><td>8 Stunden</td><td><strong>€2.299</strong></td></tr>
</tbody>
</table>
<p>Skipper, Treibstoff, Getränke und 21% MwSt. inklusive. Ruhiger und stabiler ist ein <a href="/de/katamaran-mieten-marbella/">Katamaran</a>; mehr Luxus bietet die <a href="/de/luxusyacht-mieten-marbella/">Luxus-Flotte</a>. Fragen? <a href="{WA_LINK}">Schreib uns auf WhatsApp</a>.</p>
"""
    },
    {
        "slug": "de/yachtcharter-puerto-banus",
        "en_alt": "/yacht-charter-puerto-banus/",
        "title": "Yachtcharter Puerto Banús: Luxusyachten ab Marbellas Top-Marina",
        "meta": "Yachtcharter Puerto Banús — Yachten direkt ab dem berühmtesten Yachthafen Marbellas. Ab €749/2h mit Skipper, Getränken & MwSt. inklusive.",
        "h1": "Yachtcharter Puerto Banús — direkt ab der berühmten Marina",
        "sub": "Tiefliegeplätze, Luxus-Promenade, kürzeste Wege aufs Wasser. Yachtcharter ab €749/2h direkt aus Puerto Banús.",
        "eyebrow": "Yachtcharter · Puerto Banús",
        "hero_base": "/img/boats/astondoa-40/hero",
        "hero_alt": "Yachtcharter Puerto Banús Marbella — Yacht am Liegeplatz",
        "breadcrumb_name": "Yachtcharter Puerto Banús",
        "body": f"""
<p>Puerto Banús ist der ikonische Yachthafen von Marbella und der natürliche Startpunkt für jeden Yachtcharter. Hier liegen unsere Yachten an tiefen Liegeplätzen, nur wenige Schritte von der berühmten Boutique-Promenade entfernt. Vom Pontoon bis zur offenen See sind es nur Minuten.</p>

<h2>Yachten ab Puerto Banús</h2>
<ul>
  <li><strong><a href="/boats/astondoa-40/">Astondoa 40 'Fufi'</a></strong> & <strong><a href="/boats/azimut-39/">Azimut 39</a></strong> — 12,5 m, ab €749/2h.</li>
  <li><strong><a href="/boats/mangusta-80/">Mangusta 80 'Nina'</a></strong> — 24 m Luxus-Flaggschiff ab €4.719/4h.</li>
  <li>Weitere Yachten und <a href="/de/katamaran-mieten-marbella/">Katamarane</a> auf Anfrage.</li>
</ul>

<h2>Anreise zur Marina</h2>
<p>Vom Flughafen Málaga (AGP) ca. 50 Minuten über die AP-7, vom Flughafen Gibraltar ca. 45 Minuten. Der Hafen hat ein eigenes Parkhaus (~€1,50/Std). Wir schicken dir den genauen Treffpunkt-Pin 24 Stunden vor dem Charter per WhatsApp. Mehr Details auf der Seite <a href="/de/bootsverleih-puerto-banus/">Bootsverleih Puerto Banús</a>.</p>

<h2>Preise & Buchung</h2>
<p>Ab €749 für 2 Stunden bis €2.299 für einen ganzen Tag, alles inklusive (Skipper, Treibstoff, Getränke, MwSt.). Für den vollen Tag siehe <a href="/de/tagescharter-marbella/">Tagescharter Marbella</a>. Verfügbarkeit prüfen: <a href="{WA_LINK}">WhatsApp an Andra</a>.</p>
"""
    },
    {
        "slug": "de/familien-yachtcharter-marbella",
        "en_alt": "/family-yacht-charter-marbella/",
        "title": "Familien-Yachtcharter Marbella: sicherer Bootstag mit Kindern",
        "meta": "Familien-Yachtcharter in Marbella — kinderfreundliche Boote, Schwimmstopps, Schnorcheln & Paddleboard. Stabile Katamarane verfügbar. Ab €749/2h.",
        "h1": "Familien-Yachtcharter Marbella — entspannter Bootstag mit Kindern",
        "sub": "Sicher, stabil und voller Spaß: Schwimmstopps, Schnorcheln, Paddleboard und Donut. Ideal mit Kindern und Großeltern.",
        "eyebrow": "Familie · Marbella",
        "hero_base": "/img/boats/lagoon-380/hero",
        "hero_alt": "Familien-Yachtcharter Marbella — Bootstag mit Kindern",
        "breadcrumb_name": "Familien-Charter",
        "body": f"""
<p>Ein Bootstag ist eines der besten Familienerlebnisse in Marbella — vorausgesetzt, das Boot passt zur Familie. Wir empfehlen stabile, sichere Boote mit viel Platz, Schwimmplattform und Schattenbereichen. Ein <a href="/de/katamaran-mieten-marbella/">Katamaran</a> ist besonders kinder- und großelternfreundlich, weil er kaum schaukelt.</p>

<h2>Was den Tag familienfreundlich macht</h2>
<ul>
  <li><strong>Schwimmstopps</strong> in ruhigen Buchten mit Leiter und Schwimmplattform.</li>
  <li><strong>Schnorchelausrüstung, Paddleboard und Donut</strong> an Bord — Spaß für Kinder.</li>
  <li><strong>Schatten & Liegeflächen</strong> für die Mittagspause.</li>
  <li><strong>Rettungswesten in Kindergrößen</strong> — bitte Alter und Anzahl der Kinder vorab angeben.</li>
</ul>

<h2>Tipps für den Bootstag mit Kindern</h2>
<p>Vormittags ist die See am ruhigsten und das Sonnenlicht sanfter. Bringt Sonnencreme, Hüte und leichte Snacks für die Kleinen mit. Bei sehr kleinen Kindern empfehlen wir kürzere 2–4-Stunden-Touren. Mehr Praxistipps im Guide <a href="/de/blog/beste-reisezeit-boot-marbella/">beste Reisezeit für einen Bootstag</a>.</p>

<h2>Preise & Buchung</h2>
<p>Ab €749 für 2 Stunden, Skipper und Getränke inklusive. Sag uns auf <a href="{WA_LINK}">WhatsApp</a>, wie viele Erwachsene und Kinder mitkommen — wir empfehlen das stabilste passende Boot und die richtige Route.</p>
"""
    },
    {
        "slug": "de/superyacht-charter-marbella",
        "en_alt": "/superyacht-charter-marbella/",
        "title": "Superyacht Charter Marbella: Großyachten mit Crew mieten",
        "meta": "Superyacht-Charter in Marbella — Großyachten ab 24 m mit professioneller Crew, Wasserspielzeug & Catering. Ab Puerto Banús, auf Anfrage.",
        "h1": "Superyacht Charter Marbella — Großyachten mit voller Crew",
        "sub": "Ab 24 m aufwärts: Crew, mehrere Decks, Wasserspielzeug und Premium-Service für den großen Auftritt an der Costa del Sol.",
        "eyebrow": "Superyacht · Marbella",
        "hero_base": "/img/boats/maiora-26m/hero",
        "hero_alt": "Superyacht-Charter Marbella — Großyacht ab Puerto Banús",
        "breadcrumb_name": "Superyacht Charter",
        "body": f"""
<p>Für das absolute Premium-Erlebnis bietet Marbella Superyacht-Charter ab Puerto Banús. Diese Großyachten kommen mit professioneller Crew, mehreren Decks, Innensalons, Wasserspielzeug und vollem Service — die Bühne für besondere Anlässe, VIP-Gäste und unvergessliche Feiern.</p>

<h2>Unsere Großyachten</h2>
<ul>
  <li><strong><a href="/boats/mangusta-80/">Mangusta 80 'Nina'</a></strong> — 24 m, ab €4.719/4h, Jetski inklusive.</li>
  <li><strong><a href="/boats/maiora-26m/">Maiora 26 m</a></strong> — klassische Superyacht-Eleganz.</li>
  <li><strong><a href="/boats/canados-86/">Canados 86</a></strong> & <strong><a href="/boats/ferretti-94/">Ferretti 94</a></strong> — für den ganz großen Rahmen, auf Anfrage.</li>
</ul>

<h2>Service an Bord</h2>
<p>Kapitän und Crew · Premium-Bar und Champagner-Option · Catering und Privatkoch auf Wunsch · Wasserspielzeug (Jetski, Seabob, Paddleboard) · klimatisierte Innenbereiche und Kabinen für Mehrtages-Charter. Perfekt kombiniert mit einer <a href="/de/sonnenuntergang-bootstour-marbella/">Sunset-Feier</a> oder einem <a href="/de/tagescharter-marbella/">Ganztagescharter</a>.</p>

<h2>Anfrage</h2>
<p>Superyacht-Charter werden individuell zusammengestellt — Preise hängen von Yacht, Dauer und Service ab. Schreib uns deine Wünsche (Datum, Gästezahl, Anlass) auf <a href="{WA_LINK}">WhatsApp</a> für ein maßgeschneidertes Angebot.</p>
"""
    },
    {
        "slug": "de/tagescharter-marbella",
        "en_alt": "/day-charter-marbella/",
        "title": "Tagescharter Marbella: ganzer Tag auf der Yacht ab €2.299",
        "meta": "Tagescharter in Marbella — 8 Stunden auf der Yacht mit mehreren Schwimmstopps, Mittagessen an Bord und Routen bis Sotogrande. Ab €2.299, alles inklusive.",
        "h1": "Tagescharter Marbella — der ganze Tag gehört euch",
        "sub": "8 Stunden, mehrere Buchten, Mittagessen an Bord, Schnorcheln und Paddleboard. Der entspannteste Weg, die Küste zu sehen. Ab €2.299.",
        "eyebrow": "Tagescharter · Marbella",
        "hero_base": "/img/boats/pershing-46/hero",
        "hero_alt": "Tagescharter Marbella — Ganztagestörn entlang der Costa del Sol",
        "breadcrumb_name": "Tagescharter",
        "body": f"""
<p>Ein Tagescharter ist die schönste Art, Marbella vom Wasser aus zu erleben — ohne Zeitdruck. Mit 8 Stunden habt ihr genug Zeit für mehrere Schwimmstopps, ein entspanntes Mittagessen an Bord oder in einem Strandrestaurant, Schnorcheln, Paddleboarden und das Erkunden weiter entfernter Buchten.</p>

<h2>Beliebte Ganztagsrouten</h2>
<ul>
  <li><strong>Richtung Westen nach Sotogrande</strong> — eleganter Hafen, ruhige Ankerbuchten.</li>
  <li><strong>Richtung Osten nach Cabopino</strong> — Dünen, kleiner Hafen, schöne Strände.</li>
  <li><strong>Calas-Tour</strong> — die versteckten Buchten zwischen Marbella und Estepona.</li>
</ul>

<h2>Was inklusive ist</h2>
<p>Skipper für den ganzen Tag · Treibstoff für die Standardroute · Getränke (Bier, Wein, Cava, alkoholfrei) · Eis · Schnorchelausrüstung · Paddleboard · Donut · Handtücher · 21% MwSt. Mittagessen an Bord oder Stopp an einem <a href="/de/sonnenuntergang-bootstour-marbella/">Strandrestaurant</a> auf Wunsch.</p>

<h2>Preis</h2>
<p><strong>€2.299 für 8 Stunden</strong> auf einer 12,5 m Yacht (<a href="/boats/astondoa-40/">Astondoa 40</a> / <a href="/boats/azimut-39/">Azimut 39</a>). Größere Gruppen und Luxus: <a href="/de/luxusyacht-mieten-marbella/">Mangusta 80</a>. Mehrtages-Charter auf Anfrage. Verfügbarkeit auf <a href="{WA_LINK}">WhatsApp</a> prüfen.</p>
"""
    },
    {
        "slug": "de/blog/was-kostet-bootsverleih-marbella",
        "en_alt": "/blog/how-much-does-it-cost-to-rent-a-boat-in-marbella/",
        "title": "Was kostet ein Boot mieten in Marbella? Preise 2026 erklärt",
        "meta": "Was kostet Bootsverleih in Marbella? Komplette Preisübersicht 2026 — von €230 (führerscheinfrei) über €749/2h (Yacht) bis €4.719 (Luxus). Inklusivleistungen erklärt.",
        "h1": "Was kostet es, ein Boot in Marbella zu mieten? (Preise 2026)",
        "sub": "Ehrliche Preisübersicht ohne versteckte Kosten — vom günstigen Selbstfahrer bis zur Luxusyacht. Stand 2026.",
        "eyebrow": "Ratgeber · Preise",
        "hero_base": "/img/boats/astondoa-40/hero",
        "hero_alt": "Bootsverleih Marbella Preise 2026 — Yacht vor der Küste",
        "breadcrumb_name": "Was kostet Bootsverleih?",
        "body": f"""
<p>Die Kosten für einen Bootsverleih in Marbella hängen vor allem von <strong>Bootstyp, Dauer und Saison</strong> ab. Hier ist die ehrliche Übersicht für 2026 — inklusive der Frage, was wirklich im Preis steckt und welche Zusatzkosten es gibt.</p>

<h2>Preisübersicht nach Bootstyp</h2>
<table>
<thead><tr><th>Bootstyp</th><th>Ab Preis</th><th>Hinweis</th></tr></thead>
<tbody>
<tr><td><a href="/de/bootsverleih-ohne-fuehrerschein-marbella/">Führerscheinfrei (selbst fahren)</a></td><td>€230 / 2h</td><td>bis 5 m / 15 PS, Treibstoff extra</td></tr>
<tr><td><a href="/de/jetski-mieten-marbella/">Jetski</a></td><td>€200 / Std</td><td>geführte Tour</td></tr>
<tr><td><a href="/de/yachtcharter-marbella/">Yacht 12,5 m mit Skipper</a></td><td>€749 / 2h</td><td>alles inklusive</td></tr>
<tr><td><a href="/de/tagescharter-marbella/">Ganztag (8h)</a></td><td>€2.299</td><td>mehrere Buchten</td></tr>
<tr><td><a href="/de/luxusyacht-mieten-marbella/">Luxusyacht (Mangusta 80)</a></td><td>€4.719 / 4h</td><td>Crew + Jetski</td></tr>
</tbody>
</table>

<h2>Was ist im Skipper-Preis enthalten?</h2>
<p>Bei unseren Yacht-Charters ist alles drin: lizenzierter <strong>Skipper, Treibstoff</strong> für die Standardroute, <strong>Getränke</strong> (Bier, Weißwein, Cava, Wasser, alkoholfrei), leichte Snacks, Schnorchelausrüstung, Paddleboard, Donut, Handtücher, Versicherung und <strong>21% spanische MwSt. (IVA)</strong>. Es gibt keinen Aufpreis am Hafen.</p>

<h2>Mögliche Zusatzkosten</h2>
<ul>
  <li><strong>Treibstoff bei führerscheinfreien Booten</strong> (~€15–€25 für 2h Küstenfahrt).</li>
  <li><strong>Trinkgeld für den Skipper</strong> (freiwillig, üblich 10%).</li>
  <li><strong>Catering / Champagner</strong> auf Wunsch.</li>
  <li><strong>Hochsaison-Aufschlag</strong> im Juli/August möglich.</li>
</ul>

<h2>Wie man Geld spart</h2>
<p>Bucht im <strong>Juni oder September</strong> statt Juli/August — warmes Wasser, weniger Andrang, oft günstiger (siehe <a href="/de/blog/beste-reisezeit-boot-marbella/">beste Reisezeit</a>). Teilt die Kosten in der Gruppe: Eine Yacht für 8–11 Personen kostet pro Kopf oft weniger als gedacht. Fragen zum Preis? <a href="{WA_LINK}">Schreib uns auf WhatsApp</a> für ein konkretes Angebot.</p>
"""
    },
    {
        "slug": "de/blog/beste-reisezeit-boot-marbella",
        "en_alt": "/blog/best-month-to-rent-a-boat-in-marbella/",
        "title": "Beste Reisezeit für einen Bootstag in Marbella (Monat für Monat)",
        "meta": "Wann ist die beste Zeit zum Bootfahren in Marbella? Wassertemperatur, Wind und Preise Monat für Monat — und warum Juni & September ideal sind.",
        "h1": "Beste Reisezeit für einen Bootstag in Marbella",
        "sub": "Wassertemperatur, Wind, Andrang und Preise im Jahresverlauf — damit ihr den perfekten Tag erwischt.",
        "eyebrow": "Ratgeber · Saison",
        "hero_base": "/img/boats/azimut-39/hero",
        "hero_alt": "Beste Reisezeit Bootstag Marbella — ruhige See und Sonne",
        "breadcrumb_name": "Beste Reisezeit",
        "body": f"""
<p>Marbella hat über 300 Sonnentage im Jahr, und Bootscharter sind ganzjährig möglich. Aber es gibt klare Unterschiede bei <strong>Wassertemperatur, Wind, Andrang und Preisen</strong>. Hier die ehrliche Monatsübersicht.</p>

<h2>Monat für Monat</h2>
<table>
<thead><tr><th>Zeitraum</th><th>Wasser</th><th>Bewertung</th></tr></thead>
<tbody>
<tr><td>April–Mai</td><td>16–19°C</td><td>Sonnig, ruhig, günstig — Wasser noch frisch zum Schwimmen</td></tr>
<tr><td><strong>Juni</strong></td><td>20–22°C</td><td>★ Ideal — warm, ruhig, vor dem großen Andrang</td></tr>
<tr><td>Juli–August</td><td>23–25°C</td><td>Hochsaison — wärmstes Wasser, aber voll & nachmittags windig</td></tr>
<tr><td><strong>September</strong></td><td>22–24°C</td><td>★ Ideal — warmes Wasser, weniger Andrang, ruhiger</td></tr>
<tr><td>Oktober</td><td>20–22°C</td><td>Mild und ruhig, gutes Preis-Leistungs-Verhältnis</td></tr>
<tr><td>Nov–März</td><td>15–17°C</td><td>Charter möglich (Sightseeing, Delfine), zum Schwimmen kühl</td></tr>
</tbody>
</table>

<h2>Die beste Wahl: Juni & September</h2>
<p>Wer flexibel ist, bucht <strong>Juni oder September</strong>: Das Meer ist warm genug zum Schwimmen (22–24°C), der Wind ist meist schwach, es ist deutlich weniger los als im Hochsommer — und die Preise sind oft niedriger als im Juli/August. Mehr dazu in unserer <a href="/de/blog/was-kostet-bootsverleih-marbella/">Preisübersicht</a>.</p>

<h2>Tageszeit zählt auch</h2>
<p>Unabhängig vom Monat ist der <strong>Vormittag</strong> meist am ruhigsten — der typische Costa-del-Sol-Nachmittagswind („viento de poniente“) frischt erst später auf. Für Romantik ist die <a href="/de/sonnenuntergang-bootstour-marbella/">Sonnenuntergang-Tour</a> unschlagbar, dann ist die See abends wieder glatt.</p>

<h2>Fragen zur besten Zeit für euch?</h2>
<p>Sagt uns euer Reisedatum auf <a href="{WA_LINK}">WhatsApp</a>, und wir sagen euch ehrlich, was an dem Tag zu erwarten ist — und welche Tour am besten passt.</p>
"""
    },
    {
        "slug": "de/blog/bootsfuehrerschein-spanien",
        "en_alt": "/blog/boat-license-rules-spain/",
        "title": "Bootsführerschein in Spanien: Regeln 2026 für Marbella einfach erklärt",
        "meta": "Bootsführerschein in Spanien — wann du keinen brauchst, welche deutschen Scheine gelten und wie führerscheinfreies Fahren in Marbella funktioniert (5 m / 15 PS).",
        "h1": "Bootsführerschein in Spanien — die Regeln einfach erklärt",
        "sub": "Wann du keinen Schein brauchst, welche deutschen Lizenzen anerkannt werden und wie du in Marbella legal selbst fährst.",
        "eyebrow": "Ratgeber · Recht",
        "hero_base": "/img/boats/dubhe/hero",
        "hero_alt": "Bootsführerschein Spanien — führerscheinfreies Boot in Marbella",
        "breadcrumb_name": "Bootsführerschein Spanien",
        "body": f"""
<p>Die häufigste Frage deutscher Gäste: „Brauche ich für ein Boot in Marbella einen Führerschein?“ Die kurze Antwort: <strong>oft nicht.</strong> Hier sind die Regeln für 2026 klar erklärt.</p>

<h2>Wann du KEINEN Führerschein brauchst</h2>
<ul>
  <li><strong>Mit Skipper</strong> — bei ~95% unserer Charters fährt ein lizenzierter Skipper. Du brauchst gar nichts und kannst dich entspannen.</li>
  <li><strong>Führerscheinfrei selbst fahren</strong> — erlaubt bei Booten bis <strong>5 m Rumpflänge und max. 15 PS</strong>, innerhalb 2 Seemeilen von der Küste, nur bei Tageslicht, Fahrer mindestens 18 Jahre. Siehe unsere <a href="/de/bootsverleih-ohne-fuehrerschein-marbella/">Boote ohne Führerschein</a> ab €230/2h.</li>
</ul>

<h2>Welche deutschen Scheine in Spanien gelten</h2>
<p>Wer ein größeres Boot selbst steuern will, braucht eine anerkannte Lizenz. In der Praxis werden gängige internationale Scheine akzeptiert:</p>
<ul>
  <li><strong>SBF-See</strong> (Sportbootführerschein See) — für küstennahe Fahrten meist ausreichend.</li>
  <li><strong>SKS</strong> (Sportküstenschifferschein) — für größere/weitere Charter.</li>
  <li><strong>ICC</strong> (International Certificate of Competence) — international anerkannt.</li>
</ul>
<p>Bring immer das <strong>Original-Zertifikat</strong> (kein Foto) mit. Im Zweifel schick uns vorab ein Bild auf <a href="{WA_LINK}">WhatsApp</a> — wir sagen dir, ob es für das gewünschte Boot reicht.</p>

<h2>Die führerscheinfreien Grenzen im Detail</h2>
<table>
<thead><tr><th>Regel</th><th>Grenze</th></tr></thead>
<tbody>
<tr><td>Bootslänge</td><td>max. 5 m</td></tr>
<tr><td>Motorleistung</td><td>max. 15 PS</td></tr>
<tr><td>Abstand zur Küste</td><td>max. 2 Seemeilen</td></tr>
<tr><td>Tageszeit</td><td>nur bei Tageslicht</td></tr>
<tr><td>Mindestalter Fahrer</td><td>18 Jahre</td></tr>
</tbody>
</table>

<h2>Unser Tipp</h2>
<p>Die meisten Gäste buchen einfach <strong>mit Skipper</strong> — kein Papierkram, kein Stress, und ihr lernt die besten Buchten von einem Local. Wer den Nervenkitzel selbst fahren will, nimmt ein <a href="/de/bootsverleih-ohne-fuehrerschein-marbella/">führerscheinfreies Boot</a> oder eine <a href="/de/jetski-mieten-marbella/">geführte Jetski-Tour</a>.</p>
"""
    },
]


# --- DE chrome localisation -------------------------------------------------
# The shared template ships English UI chrome (nav, CTAs, trust strip, booking
# card + modal, footer headings). We translate the user-visible strings for the
# German locale only, as a post-pass over the rendered HTML. Order matters: the
# WhatsApp pre-fill text is swapped first, then literal label strings.
EN_WA_TEXT = "Hi%2C%20I%27d%20like%20to%20book%20a%20boat%20in%20Marbella"
DE_WA_TEXT = "Hallo%2C%20ich%20m%C3%B6chte%20ein%20Boot%20in%20Marbella%20mieten"

CHROME_DE = [
    # WhatsApp pre-filled message (header + book card buttons)
    (EN_WA_TEXT, DE_WA_TEXT),
    # Primary nav
    (">Our Boats<", ">Unsere Boote<"),
    (">Experiences<", ">Erlebnisse<"),
    (">Yachts<", ">Yachten<"),
    # Header CTA button
    ("📅 Book</button>", "📅 Buchen</button>"),
    # Hero
    ('class="hero-price">From <strong>', 'class="hero-price">Ab <strong>'),
    ("Skipper, drinks (beer · wine · cava), snacks &amp; VAT included",
     "Skipper, Getränke (Bier · Wein · Cava), Snacks &amp; MwSt. inklusive"),
    ("See boats ↓", "Boote ansehen ↓"),
    (">\n        Book on WhatsApp", ">\n        Auf WhatsApp buchen"),
    ("Book on WhatsApp", "Auf WhatsApp buchen"),
    # Trust strip
    ("Skipper, fuel &amp; VAT included", "Skipper, Treibstoff &amp; MwSt. inklusive"),
    ("Beer, white wine &amp; cava on board", "Bier, Weißwein &amp; Cava an Bord"),
    ("WhatsApp reply in &lt;5 min", "WhatsApp-Antwort in &lt;5 Min"),
    ("Year-round on the Costa del Sol", "Ganzjährig an der Costa del Sol"),
    # Booking card
    ("87 verified reviews", "87 verifizierte Bewertungen"),
    ("Read 87 verified reviews, average 4.9 out of 5",
     "87 verifizierte Bewertungen lesen, Durchschnitt 4,9 von 5"),
    ("From <strong>€", "Ab <strong>€"),  # book-card price (hero already handled above)
    ("💬 Message on WhatsApp", "💬 Auf WhatsApp schreiben"),
    ("Avg reply &lt; 5 min · No deposit until you confirm",
     "Ø Antwort &lt; 5 Min · keine Anzahlung bis zur Bestätigung"),
    ("📅 Book now", "📅 Jetzt buchen"),
    ("Browse the full fleet →", "Ganze Flotte ansehen →"),
    ("All charters include", "In jedem Charter enthalten"),
    ("Licensed skipper &amp; fuel", "Lizenzierter Skipper &amp; Treibstoff"),
    ("Drinks: water, soft drinks, beer, white wine, cava",
     "Getränke: Wasser, alkoholfreie Drinks, Bier, Weißwein, Cava"),
    ("Light snacks", "Leichte Snacks"),
    ("Insurance &amp; safety equipment", "Versicherung &amp; Sicherheitsausrüstung"),
    ("Snorkel gear &amp; inflatables", "Schnorchelausrüstung &amp; Wasserspielzeug"),
    ("VAT 21% — no surprises", "21% MwSt. — keine Überraschungen"),
    # Booking modal
    ('aria-label="Close">×', 'aria-label="Schließen">×'),
    (">Book your charter<", ">Charter buchen<"),
    ("Send your details — we'll reply on WhatsApp within 5 minutes with available boats &amp; final price.",
     "Schick uns deine Daten — wir antworten innerhalb von 5 Minuten auf WhatsApp mit verfügbaren Booten &amp; Endpreis."),
    (">Your name", ">Dein Name"),
    ('placeholder="e.g. Sophie"', 'placeholder="z. B. Sophie"'),
    (">Date\n", ">Datum\n"),
    (">Guests\n", ">Gäste\n"),
    (">Boat (optional)", ">Boot (optional)"),
    (">Recommend me a boat<", ">Empfiehl mir ein Boot<"),
    ("9 guests", "9 Gäste"), ("11 guests", "11 Gäste"),
    ("12 guests + jet ski", "12 Gäste + Jetski"),
    ("(licence-free)", "(führerscheinfrei)"), ("5 guests", "5 Gäste"),
    (">Another boat from the fleet<", ">Ein anderes Boot der Flotte<"),
    (">Anything else?", ">Sonstige Wünsche?"),
    ('placeholder="Sunset preferred, one birthday on board…"',
     'placeholder="Sonnenuntergang bevorzugt, ein Geburtstag an Bord…"'),
    ("💬 Continue in WhatsApp", "💬 Weiter in WhatsApp"),
    ("Opens WhatsApp with your message pre-filled — you send it from your own number. Average reply under 5 minutes.",
     "Öffnet WhatsApp mit vorausgefüllter Nachricht — du sendest sie von deiner eigenen Nummer. Antwort meist unter 5 Minuten."),
    # Footer headings
    (">Boats</p>", ">Boote</p>"),
    (">Guides</p>", ">Ratgeber</p>"),
    (">Contact</p>", ">Kontakt</p>"),
    ("Independent local guide to renting boats, yachts and catamarans on the Costa del Sol.",
     "Unabhängiger lokaler Anbieter für Boote, Yachten und Katamarane an der Costa del Sol."),
    # Footer copyright line
    ("Independent operator from Puerto Banús.", "Unabhängiger Anbieter aus Puerto Banús."),
    (">Home</a>", ">Start</a>"),
    (">About</a>", ">Über uns</a>"),
    (">Contact</a>", ">Kontakt</a>"),
    (">Reviews</a>", ">Bewertungen</a>"),
    (">Cancellation</a>", ">Stornierung</a>"),
    (">Site map</a>", ">Sitemap</a>"),
]


def localize_chrome(out: str) -> str:
    for en, de in CHROME_DE:
        out = out.replace(en, de)
    return out


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
    out = localize_chrome(out)
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
