"""Outreach sender — emails scraped operators about listing on BoatHire24.
Also provides the shared message templates + helpers used by formreach.py.
"""
from __future__ import annotations
import argparse, json, os, sys, time, pathlib, random, urllib.parse, urllib.request, urllib.error

ROOT = pathlib.Path(__file__).resolve().parents[2]
def _resend_key() -> str:
    """Key comes from the environment or ROOT/.env — never hardcode it here.
    (The previous hardcoded key was committed to git; rotate it in the Resend
    dashboard and update .env.)"""
    key = os.environ.get("RESEND_API_KEY", "").strip()
    if not key:
        env = ROOT / ".env"
        if env.exists():
            for line in env.read_text().splitlines():
                if line.startswith("RESEND_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not key:
        sys.exit("RESEND_API_KEY not set (env or .env) — refusing to run.")
    return key

RESEND_KEY = _resend_key()
FROM = "Andra Kiirkivi <info@boathire24.com>"
REPLY_TO = "info@boathire24.com"
SITE = "https://boathire24.com"
LIST_URL = "https://boathire24.com/list-your-boat"
SIGNATURE_PHOTO = ROOT / "site" / "img" / "team" / "andra-kiirkivi-200.jpg"

from . import store

LANG_BY_COUNTRY = {
    "ES": "es", "MX": "es", "AR": "es", "CO": "es", "UY": "es", "CL": "es", "PE": "es",
    "PA": "es", "CR": "es", "DO": "es", "EC": "es",
    "IT": "it",
    "FR": "fr", "MC": "fr", "BL": "fr", "MQ": "fr", "GP": "fr", "PF": "fr", "NC": "fr",
    "PT": "pt", "BR": "pt",
}

def pick_lang(country):
    return LANG_BY_COUNTRY.get((country or "").upper(), "en")

TEMPLATES = {
    "en": {"subject": "Quick question about your {city} boat rentals",
           "body_text": """Hi{name_clause},

I came across {domain} while researching boat rental operators in {city}.

I'm building BoatHire24 — a global marketplace where renters search, book and pay for boats in one place (think Airbnb for boats). We launch operators with zero upfront cost; only a small commission on completed bookings.

If extra booking volume in {city} sounds useful, I'd love to add your boats. Setting up a listing takes about 5 minutes:

{list_url}

Don't want to DIY? We offer free concierge onboarding — reply with your WhatsApp and we'll set up your listing for you (photos, pricing, calendar) in ~30 minutes.

Open to a quick reply either way — even "not interested" is fine and I'll take you off the list.

Best,
Andra Kiirkivi
{site}

— You're receiving this because your email is publicly listed on {domain} as a boat rental contact. Reply STOP and we'll never email you again."""},
    "es": {"subject": "Pregunta rápida sobre el alquiler de barcos en {city}",
           "body_text": """Hola{name_clause},

Vi {domain} mientras investigaba operadores de alquiler de barcos en {city}.

Estoy lanzando BoatHire24 — un marketplace global donde los clientes buscan, reservan y pagan barcos en un mismo lugar (algo así como un Airbnb de barcos). Damos de alta a los operadores sin coste inicial; solo una pequeña comisión por reserva completada.

Si te interesaría más volumen de reservas en {city}, me encantaría añadir tus barcos. Crear un anuncio lleva unos 5 minutos:

{list_url}

¿No quieres hacerlo tú? Ofrecemos onboarding concierge gratis — responde con tu WhatsApp y montamos tu anuncio por ti (fotos, precios, calendario) en unos 30 minutos.

Cualquier respuesta es bienvenida — incluso "no me interesa" y te quito de la lista.

Un saludo,
Andra Kiirkivi
{site}

— Recibes este correo porque tu email aparece públicamente en {domain} como contacto de alquiler de barcos. Responde STOP y no te volveremos a escribir."""},
    "it": {"subject": "Domanda veloce sul noleggio barche a {city}",
           "body_text": """Ciao{name_clause},

Ho trovato {domain} cercando operatori di noleggio barche a {city}.

Sto lanciando BoatHire24 — un marketplace globale dove i clienti cercano, prenotano e pagano barche in un unico posto (un po' come Airbnb per le barche). Gli operatori si iscrivono senza costi iniziali; solo una piccola commissione sulle prenotazioni completate.

Se ti interesserebbe più volume di prenotazioni a {city}, sarei felice di aggiungere le tue barche. Creare un annuncio richiede circa 5 minuti:

{list_url}

Non vuoi farlo da solo? Offriamo onboarding concierge gratuito — rispondi con il tuo WhatsApp e creiamo l'annuncio per te (foto, prezzi, calendario) in circa 30 minuti.

Ogni risposta è benvenuta — anche un "non mi interessa" e ti tolgo dalla lista.

A presto,
Andra Kiirkivi
{site}

— Ricevi questa email perché il tuo indirizzo è pubblicamente elencato su {domain} come contatto noleggio barche. Rispondi STOP per non essere più contattato."""},
    "fr": {"subject": "Petite question sur la location de bateaux à {city}",
           "body_text": """Bonjour{name_clause},

Je suis tombé sur {domain} en recherchant des opérateurs de location de bateaux à {city}.

Je lance BoatHire24 — une marketplace mondiale où les clients cherchent, réservent et paient leur bateau au même endroit (un peu comme Airbnb pour les bateaux). Inscription gratuite pour les opérateurs ; seulement une petite commission sur les réservations.

Si avoir plus de volume à {city} vous intéresse, je serais ravi d'ajouter vos bateaux. Créer une annonce prend environ 5 minutes :

{list_url}

Vous ne voulez pas le faire vous-même ? Onboarding conciergerie gratuit — répondez avec votre WhatsApp et nous créons votre annonce pour vous (photos, prix, calendrier) en ~30 minutes.

Toute réponse est bienvenue — même "pas intéressé" et je vous retire de la liste.

Cordialement,
Andra Kiirkivi
{site}

— Vous recevez ce message car votre email est publié sur {domain} comme contact location de bateaux. Répondez STOP et nous ne vous écrirons plus."""},
    "pt": {"subject": "Pergunta rápida sobre aluguel de barcos em {city}",
           "body_text": """Olá{name_clause},

Encontrei {domain} pesquisando operadores de aluguel de barcos em {city}.

Estou lançando o BoatHire24 — um marketplace global onde os clientes pesquisam, reservam e pagam barcos no mesmo lugar (tipo um Airbnb de barcos). Cadastramos operadores sem custo inicial; apenas uma pequena comissão por reserva concluída.

Se mais volume de reservas em {city} for útil, adoraria adicionar seus barcos. Criar um anúncio leva cerca de 5 minutos:

{list_url}

Não quer fazer sozinho? Onboarding concierge grátis — responda com seu WhatsApp e nós criamos seu anúncio (fotos, preços, calendário) em ~30 minutos.

Qualquer resposta é bem-vinda — até "não tenho interesse" e te retiro da lista.

Abraços,
Andra Kiirkivi
{site}

— Você está recebendo este email porque seu endereço aparece publicamente em {domain} como contato de aluguel de barcos. Responda STOP e não enviaremos mais nada."""},
}

COMPETITOR_DOMAINS = {
    "samboat.com", "samboat.co.uk", "samboat.fr", "samboat.es", "samboat.it",
    "clickandboat.com", "boatsetter.com", "getmyboat.com", "boataround.com",
    "yachtcharterfleet.com", "sailogy.com", "borrowaboat.com", "bednblue.com",
    "boatbookings.com", "yotha.com", "incrediblue.com", "zizoo.com",
    "boatjump.com", "nautal.com", "scansail.com", "ahoyclub.com",
}
BAD_LOCALS = {"noreply", "no-reply", "donotreply", "postmaster", "abuse",
              "webmaster", "spam", "mailer-daemon"}

def ensure_outreach_table(con):
    con.executescript("""
    CREATE TABLE IF NOT EXISTS outreach (
        domain TEXT, email TEXT, sent_at TEXT, lang TEXT, subject TEXT,
        resend_id TEXT, status TEXT, error TEXT,
        replied INTEGER DEFAULT 0, replied_at TEXT, reply_class TEXT, reply_snippet TEXT,
        followup_sent_at TEXT, followup_resend_id TEXT, interested_reply_sent_at TEXT,
        PRIMARY KEY (domain, email));
    """)
    con.commit()

def already_sent(con, domain, email):
    return con.execute("SELECT 1 FROM outreach WHERE domain=? AND email=? AND status IN ('sent','queued')",
                       (domain, email)).fetchone() is not None

def record(con, domain, email, lang, subject, resend_id, status, error=""):
    con.execute("""INSERT OR REPLACE INTO outreach
        (domain,email,sent_at,lang,subject,resend_id,status,error) VALUES(?,?,?,?,?,?,?,?)""",
        (domain, email, store.now(), lang, subject, resend_id, status, error))
    con.commit()

def hard_suppressed_emails(con):
    cur = con.execute("SELECT DISTINCT lower(email) FROM outreach WHERE reply_class IN ('stop','bounce') OR status='failed'")
    return {r[0] for r in cur if r[0]}

def good_email(e):
    if not e or "@" not in e: return False
    if e.partition("@")[0].lower() in BAD_LOCALS: return False
    return len(e) <= 80

def best_email_for_domain(emails, domain):
    if not emails: return None
    root = domain.split(".")[-2] if "." in domain else domain
    on = [e for e in emails if root in e.split("@")[1] and good_email(e)]
    if on:
        rank = {"info":0,"contact":1,"hello":2,"bookings":3,"booking":3,"sales":4,"reservations":5}
        on.sort(key=lambda e: rank.get(e.split("@")[0].lower(), 99))
        return on[0]
    others = [e for e in emails if good_email(e)]
    return others[0] if others else None

def _personalized_list_url(rec):
    import re as _re
    city_slug = _re.sub(r"[^a-z0-9]+", "-", (rec.get("city") or "").lower()).strip("-")
    params = {"ref":"outreach","city":rec.get("city") or "","op":rec.get("domain") or "",
              "lang":pick_lang(rec.get("country")),"utm_source":"cold_email","utm_medium":"email",
              "utm_campaign":"operator_outreach_2026","utm_content":city_slug or "global"}
    return LIST_URL + "?" + urllib.parse.urlencode({k:v for k,v in params.items() if v})

def render(rec, force_lang=None):
    lang = force_lang or pick_lang(rec["country"])
    tpl = TEMPLATES.get(lang, TEMPLATES["en"])
    company = (rec.get("company") or "").strip()
    name_clause = ""
    if company and len(company) < 60 and any(c.isalpha() for c in company):
        if not any(s in company.lower() for s in ("rental","charter","boats","yacht","marina","tours")):
            name_clause = f" {company.split()[0]}"
    ctx = {"name_clause":name_clause,"domain":rec["domain"],"city":rec.get("city") or "your area",
           "site":SITE,"list_url":_personalized_list_url(rec)}
    return lang, tpl["subject"].format(**ctx), tpl["body_text"].format(**ctx)

SIGNATURE_HTML = """
<table cellpadding="0" cellspacing="0" style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:14px;color:#1a1a1a;margin-top:8px;">
  <tr><td style="padding-top:18px;border-top:1px solid #e5e5e5;">
    <strong style="color:#07101e;font-size:15px;">Andra Kiirkivi</strong><br>
    <span style="color:#666;font-size:13px;">Founder · BoatHire24</span><br>
    <a href="https://boathire24.com" style="color:#c9a84e;text-decoration:none;font-size:13px;">boathire24.com</a> ·
    <a href="mailto:info@boathire24.com" style="color:#c9a84e;text-decoration:none;font-size:13px;">info@boathire24.com</a>
  </td></tr>
  <tr><td style="padding-top:14px;font-size:11px;color:#999;line-height:1.5;">
    © 2026 BoatHire24 Ltd · You're receiving this because your email is publicly listed on {domain} as a boat-rental contact. Reply <strong>STOP</strong> and we'll never email you again.
  </td></tr>
</table>"""

def _text_to_html(text, domain):
    lines = []
    for line in text.splitlines():
        if line.startswith("— ") or line.startswith("-- "): break
        lines.append(line)
    while lines and lines[-1].strip() == "": lines.pop()
    if lines and "boathire24.com" in lines[-1]: lines.pop()
    if lines and lines[-1].strip() in ("Andra Kiirkivi",): lines.pop()
    while lines and lines[-1].strip() == "": lines.pop()
    if lines and lines[-1].rstrip(",") in ("Best","Un saludo","A presto","Cordialement","Abraços"): lines.pop()
    body_html = ""
    for line in lines:
        if line.strip().startswith("https://"):
            url = line.strip()
            try:
                p = urllib.parse.urlparse(url); disp = p.netloc + (p.path if p.path not in ("","/") else "")
            except Exception: disp = url
            body_html += f'<p style="margin:0 0 14px;"><a href="{url}" style="color:#c9a84e;font-weight:600;text-decoration:none;">{disp} →</a></p>'
        elif line.strip() == "": body_html += "<br>"
        else: body_html += f'<p style="margin:0 0 12px;line-height:1.55;color:#1a1a1a;">{line}</p>'
    return f"""<!doctype html><html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f6f6f4;font-family:-apple-system,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f6f6f4;padding:30px 16px;"><tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:10px;padding:32px;max-width:600px;"><tr><td style="font-size:15px;color:#1a1a1a;">
{body_html}{SIGNATURE_HTML.format(domain=domain)}
</td></tr></table></td></tr></table></body></html>"""

def resend_send(to, subject, text, html=None, from_=None):
    if not RESEND_KEY: return None, "no RESEND_API_KEY"
    payload = {"from":from_ or FROM,"to":[to],"reply_to":REPLY_TO,"subject":subject,"text":text}
    if html: payload["html"] = html
    body = json.dumps(payload).encode()
    req = urllib.request.Request("https://api.resend.com/emails", data=body, method="POST",
        headers={"Authorization":f"Bearer {RESEND_KEY}","Content-Type":"application/json",
                 "User-Agent":"BoatHire24-Outreach/1.0","Accept":"application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read().decode()).get("id"), None
        except urllib.error.HTTPError as e:
            b = e.read().decode()[:300]
            if e.code == 429: time.sleep(5*(attempt+1)); continue
            return None, f"HTTP {e.code}: {b}"
        except Exception as e:
            if attempt < 3: time.sleep(3); continue
            return None, f"{type(e).__name__}: {e}"
    return None, "exhausted retries"

def candidates(con, limit=None):
    ensure_outreach_table(con)
    suppressed = hard_suppressed_emails(con)
    cur = con.execute("""SELECT domain, company, city, country, emails FROM leads
        WHERE emails IS NOT NULL AND emails != '[]' AND emails != '' ORDER BY confidence DESC""")
    out = []
    for domain, company, city, country, emails_j in cur:
        if domain in COMPETITOR_DOMAINS: continue
        if any(domain.endswith("."+c) for c in COMPETITOR_DOMAINS): continue
        try: emails = json.loads(emails_j) if emails_j else []
        except Exception: continue
        email = best_email_for_domain(emails, domain)
        if not email or email.lower() in suppressed: continue
        if already_sent(con, domain, email): continue
        out.append({"domain":domain,"company":company or "","city":city or "","country":country or "","email":email})
        if limit and len(out) >= limit: break
    return out
