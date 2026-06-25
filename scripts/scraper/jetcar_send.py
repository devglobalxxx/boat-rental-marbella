"""Send the JetCar-operator outreach — a tailored 'list your JetCars on
BoatHire24' email to leads tagged source LIKE '%jetcar%'. Reuses outreach.py
for Resend sending, suppression, and the personalized list URL.

  python3 -m scripts.scraper.jetcar_send --dry-run
  python3 -m scripts.scraper.jetcar_send --to-self --limit 3
  python3 -m scripts.scraper.jetcar_send --all --sleep 3
"""
from __future__ import annotations
import argparse, json, time, random, urllib.parse
from . import store, outreach

JETCAR = {
 "en": ("List your JetCars on BoatHire24 — free, global bookings",
        """Hi{name_clause},

I came across {company} while researching JetCar / self-drive electric boat operators in {city}.

I'm building BoatHire24 — a global marketplace where travellers search, book and pay for boats and watercraft in one place (think Airbnb for boats). JetCars are exactly the kind of experience our renters are looking for.

Listing is free — only a small commission on completed bookings. Setup takes about 5 minutes:

{list_url}

Don't want to set it up yourself? Just reply and our team will create your JetCar listing for you (photos, pricing, calendar).

A quick "yes / no / not now" is all I need.

Best,
Andra Kiirkivi
{site}"""),
 "es": ("Publica tus JetCars en BoatHire24 — gratis, reservas globales",
        """Hola{name_clause},

Vi {company} mientras investigaba operadores de JetCar / barcos eléctricos self-drive en {city}.

Estoy lanzando BoatHire24 — un marketplace global donde los viajeros buscan, reservan y pagan barcos y vehículos acuáticos en un mismo lugar (un Airbnb de barcos). Los JetCars son justo el tipo de experiencia que buscan nuestros clientes.

Publicar es gratis — solo una pequeña comisión por reserva completada. Crear el anuncio lleva unos 5 minutos:

{list_url}

¿No quieres hacerlo tú? Responde y nuestro equipo crea tu anuncio de JetCar por ti (fotos, precios, calendario).

Con un "sí / no / ahora no" me basta.

Un saludo,
Andra Kiirkivi
{site}"""),
 "fr": ("Listez vos JetCars sur BoatHire24 — gratuit, réservations mondiales",
        """Bonjour{name_clause},

J'ai trouvé {company} en recherchant des opérateurs de JetCar / bateaux électriques en libre conduite à {city}.

Je lance BoatHire24 — une marketplace mondiale où les voyageurs cherchent, réservent et paient bateaux et engins nautiques au même endroit (un Airbnb des bateaux). Les JetCars sont exactement le type d'expérience recherché par nos clients.

L'inscription est gratuite — seulement une petite commission sur les réservations. La création prend ~5 minutes :

{list_url}

Vous ne voulez pas le faire vous-même ? Répondez et notre équipe crée votre annonce JetCar pour vous (photos, prix, calendrier).

Un "oui / non / pas maintenant" me suffit.

Cordialement,
Andra Kiirkivi
{site}"""),
 "it": ("Pubblica i tuoi JetCar su BoatHire24 — gratis, prenotazioni globali",
        """Ciao{name_clause},

Ho trovato {company} cercando operatori di JetCar / barche elettriche self-drive a {city}.

Sto lanciando BoatHire24 — un marketplace globale dove i viaggiatori cercano, prenotano e pagano barche e mezzi acquatici in un unico posto (un Airbnb delle barche). I JetCar sono proprio il tipo di esperienza che cercano i nostri clienti.

L'iscrizione è gratuita — solo una piccola commissione sulle prenotazioni. Creare l'annuncio richiede ~5 minuti:

{list_url}

Non vuoi farlo da solo? Rispondi e il nostro team crea il tuo annuncio JetCar per te (foto, prezzi, calendario).

Un "sì / no / non ora" mi basta.

A presto,
Andra Kiirkivi
{site}"""),
}

def jetcar_url(rec):
    p = {"ref":"outreach","vertical":"jetcar","city":rec.get("city") or "","op":rec.get("domain") or "",
         "lang":outreach.pick_lang(rec.get("country")),"utm_source":"cold_email","utm_medium":"email","utm_campaign":"jetcar_outreach_2026"}
    return outreach.LIST_URL + "?" + urllib.parse.urlencode({k:v for k,v in p.items() if v})

def render(rec):
    lang = outreach.pick_lang(rec.get("country"))
    subj_tpl, body_tpl = JETCAR.get(lang, JETCAR["en"])
    company = (rec.get("company") or "your company").strip()
    nc = ""
    if company and len(company) < 60 and not any(s in company.lower() for s in ("rental","charter","jetcar","boats","yacht","tours","water")):
        nc = f" {company.split()[0]}"
    ctx = {"name_clause":nc,"company":company,"city":rec.get("city") or "your area","site":outreach.SITE,"list_url":jetcar_url(rec)}
    return lang, subj_tpl.format(**ctx), body_tpl.format(**ctx)

def candidates(con, limit=None):
    outreach.ensure_outreach_table(con)
    suppressed = outreach.hard_suppressed_emails(con)
    cur = con.execute("""SELECT domain,company,city,country,emails FROM leads
        WHERE source LIKE '%jetcar%' AND emails IS NOT NULL AND emails NOT IN ('','[]') ORDER BY confidence DESC""")
    out = []
    for domain, company, city, country, emails_j in cur:
        try: emails = json.loads(emails_j) if emails_j else []
        except Exception: continue
        email = outreach.best_email_for_domain(emails, domain)
        if not email or email.lower() in suppressed: continue
        if outreach.already_sent(con, domain, email): continue
        out.append({"domain":domain,"company":company or "","city":city or "","country":country or "","email":email})
        if limit and len(out) >= limit: break
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--all", action="store_true")
    ap.add_argument("--limit", type=int, default=200); ap.add_argument("--to-self", action="store_true")
    ap.add_argument("--sleep", type=float, default=3.0)
    args = ap.parse_args()
    con = store.connect()
    recs = candidates(con, limit=None if args.all else args.limit)
    print(f"JetCar candidates: {len(recs)}")
    if args.dry_run:
        for r in recs[:3]:
            lang, subj, body = render(r)
            print(f"\n=== {r['domain']} → {r['email']} ({lang}) ===\nSubject: {subj}\n{body}")
        print(f"(dry-run; first 3 of {len(recs)})"); return
    sent = failed = 0
    for i, r in enumerate(recs, 1):
        lang, subj, body = render(r)
        target = "info@boathire24.com" if args.to_self else r["email"]
        rid, err = outreach.resend_send(target, subj, body, html=outreach._text_to_html(body, r["domain"]))
        if rid:
            outreach.record(con, r["domain"], r["email"], lang, subj, rid, "sent"); sent += 1
            print(f"  [{i:>3}/{len(recs)}] ✓ {r['domain']:<34} → {target} ({lang})")
        else:
            outreach.record(con, r["domain"], r["email"], lang, subj, None, "failed", err or ""); failed += 1
            print(f"  [{i:>3}/{len(recs)}] ✗ {r['domain']:<34} {err}")
        time.sleep(args.sleep + random.random())
    print(f"\nDone. sent={sent} failed={failed}")

if __name__ == "__main__":
    main()
