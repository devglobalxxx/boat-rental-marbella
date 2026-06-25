"""Follow-up + reply-tagging for BoatHire24 outreach.

  python3 -m scripts.scraper.followup scan      # poll Gmail, tag replies, auto-reply interested
  python3 -m scripts.scraper.followup send      # send follow-ups (404-recovery for pre-fix sends)
  python3 -m scripts.scraper.followup status
  python3 -m scripts.scraper.followup auth      # one-time Gmail OAuth (gmail.readonly)
"""
from __future__ import annotations
import argparse, base64, os, pathlib, re, sys, time, random
from email.utils import parseaddr
from . import store, outreach, sheets

GMAIL_SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive.file",
                "https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_PATH = pathlib.Path.home() / ".boathire24_gmail_token.json"
FOLLOWUP_DAYS = 3
FIX_DATE = "2026-06-01"   # sends before this date hit the /list-your-boat 404

# ── schema additions ────────────────────────────────────────────────────────
def ensure_schema(con):
    outreach.ensure_outreach_table(con)
    cols = {r[1] for r in con.execute("PRAGMA table_info(outreach)")}
    for col, t in [("replied","INTEGER DEFAULT 0"),("replied_at","TEXT"),
                   ("reply_class","TEXT"),("reply_snippet","TEXT"),
                   ("followup_sent_at","TEXT"),("followup_resend_id","TEXT"),
                   ("interested_reply_sent_at","TEXT")]:
        if col not in cols:
            con.execute(f"ALTER TABLE outreach ADD COLUMN {col} {t}")
    con.commit()

# ── standard follow-up ──────────────────────────────────────────────────────
FOLLOWUP = {
 "en": ("Following up — {city} boats on BoatHire24?",
        "Hi{name_clause},\n\nJust bumping this up in case it got lost. I'd really like to add your {city} boats to BoatHire24 — zero cost to list, only commission on bookings.\n\n5-minute setup: {list_url}\n\nA \"yes / no / not now\" reply is all I need. Thanks!\n\nAndra"),
 "es": ("Siguiendo — ¿barcos de {city} en BoatHire24?",
        "Hola{name_clause},\n\nSolo retomo el hilo por si se quedó perdido. Me encantaría añadir tus barcos de {city} a BoatHire24 — sin coste de alta, solo comisión por reserva.\n\n5 minutos: {list_url}\n\nCon un \"sí / no / ahora no\" me basta. ¡Gracias!\n\nAndra"),
 "it": ("Risposta? — barche di {city} su BoatHire24?",
        "Ciao{name_clause},\n\nTi riscrivo nel caso si fosse perso. Mi piacerebbe aggiungere le tue barche di {city} su BoatHire24 — iscrizione gratuita, solo commissione sulle prenotazioni.\n\n5 minuti: {list_url}\n\nUn \"sì / no / non ora\" basta. Grazie!\n\nAndra"),
 "fr": ("Suite — bateaux de {city} sur BoatHire24 ?",
        "Bonjour{name_clause},\n\nJe relance au cas où mon premier message serait passé inaperçu. J'aimerais beaucoup ajouter vos bateaux de {city} sur BoatHire24 — inscription gratuite, commission uniquement sur les réservations.\n\n5 minutes : {list_url}\n\nUn \"oui / non / pas maintenant\" me suffit. Merci !\n\nAndra"),
 "pt": ("Voltando — barcos de {city} no BoatHire24?",
        "Olá{name_clause},\n\nSó retomando caso meu primeiro email tenha se perdido. Adoraria adicionar seus barcos de {city} no BoatHire24 — cadastro gratuito, só comissão por reserva.\n\n5 minutos: {list_url}\n\nUm \"sim / não / agora não\" já basta. Obrigada!\n\nAndra"),
}

# ── 404-recovery follow-up (pre-fix sends) ──────────────────────────────────
FOLLOWUP_404 = {
 "en": ("Sorry — my BoatHire24 link was broken (fixed now)",
        "Hi{name_clause},\n\nI owe you an apology: the link in my last email about adding your {city} boats to BoatHire24 was broken and led to a dead page. That's fixed now.\n\nHere's the working 5-minute setup link:\n{list_url}\n\nFree to list, only a small commission on completed bookings. Don't want to set it up yourself? Just reply and our team will create the listing for you (photos, pricing, calendar).\n\nA quick \"yes / no / not now\" is all I need — thanks for your patience.\n\nAndra"),
 "es": ("Disculpa — el enlace de BoatHire24 estaba roto (ya arreglado)",
        "Hola{name_clause},\n\nTe debo una disculpa: el enlace de mi email anterior para añadir tus barcos de {city} a BoatHire24 estaba roto y llevaba a una página caída. Ya está arreglado.\n\nAquí tienes el enlace que funciona (5 minutos):\n{list_url}\n\nAlta gratis, solo una pequeña comisión por reserva completada. ¿No quieres hacerlo tú? Responde y nuestro equipo crea el anuncio por ti (fotos, precios, calendario).\n\nCon un \"sí / no / ahora no\" me basta — gracias por tu paciencia.\n\nAndra"),
 "it": ("Scusa — il link BoatHire24 era rotto (ora risolto)",
        "Ciao{name_clause},\n\nTi devo una scusa: il link nella mia email precedente per aggiungere le tue barche di {city} su BoatHire24 era rotto. Ora è risolto.\n\nEcco il link funzionante (5 minuti):\n{list_url}\n\nIscrizione gratuita, solo una piccola commissione sulle prenotazioni. Non vuoi farlo da solo? Rispondi e il nostro team crea l'annuncio per te.\n\nUn \"sì / no / non ora\" mi basta — grazie per la pazienza.\n\nAndra"),
 "fr": ("Désolée — mon lien BoatHire24 était cassé (corrigé)",
        "Bonjour{name_clause},\n\nJe vous dois des excuses : le lien de mon précédent email pour ajouter vos bateaux de {city} sur BoatHire24 était cassé. C'est corrigé.\n\nVoici le lien qui fonctionne (5 minutes) :\n{list_url}\n\nInscription gratuite, seulement une petite commission sur les réservations. Vous ne voulez pas le faire vous-même ? Répondez et notre équipe crée l'annonce pour vous.\n\nUn \"oui / non / pas maintenant\" me suffit — merci de votre patience.\n\nAndra"),
 "pt": ("Desculpe — meu link do BoatHire24 estava quebrado (corrigido)",
        "Olá{name_clause},\n\nDevo um pedido de desculpas: o link do meu email anterior para adicionar seus barcos de {city} ao BoatHire24 estava quebrado. Já está corrigido.\n\nAqui está o link que funciona (5 minutos):\n{list_url}\n\nCadastro gratuito, só uma pequena comissão por reserva. Não quer fazer sozinho? Responda e nossa equipe cria o anúncio para você.\n\nUm \"sim / não / agora não\" já basta — obrigada pela paciência.\n\nAndra"),
}

INTERESTED_REPLY = {
 "en": ("Welcome — let's get your boats live on BoatHire24",
        "Hi{name_clause},\n\nThanks for replying — really glad you're interested.\n\nQuickest path:\n1. Create your listing here: {list_url}\n2. Reply with any questions and I'll personally help you finish setup.\n\nI'll keep an eye on your inbox today.\n\nAndra Kiirkivi\nFounder · BoatHire24\n{site}"),
 "es": ("Bienvenido — vamos a publicar tus barcos en BoatHire24",
        "Hola{name_clause},\n\nGracias por responder — me alegra mucho que te interese.\n\nEl camino más rápido:\n1. Crea tu anuncio: {list_url}\n2. Responde con cualquier duda y te ayudo personalmente.\n\nUn saludo,\nAndra Kiirkivi\nFundadora · BoatHire24\n{site}"),
}

# ── reply classification ────────────────────────────────────────────────────
STOP_RX = re.compile(r"\b(stop|unsubscribe|remove me|baja|desuscrib|me retir|no me escrib|d[ée]sabonn|nicht mehr)\b", re.I)
NEGATIVE_RX = re.compile(r"\bnot? (interested|inter[eé]s|interesado|interessato|interesse)\b|no thanks|no gracias|non grazie|non merci", re.I)
POSITIVE_RX = re.compile(r"\b(yes|si|s[íi]|oui|interested|interesado|interessato|tell me more|m[áa]s informaci|details|let'?s talk|call me|cu[ée]ntame)\b", re.I)
OOO_RX = re.compile(r"\b(out of office|vacation|holiday|away|fuera de la oficina|vacaciones|automatic|automatische|autosvar|automatico)\b", re.I)
BOUNCE_RX = re.compile(r"(mail delivery|delivery (status|failure)|undeliver|mailbox.{0,20}full|address (rejected|not found)|user unknown)", re.I)

def classify(subject, body):
    t = f"{subject}\n{body}"[:3000]
    if BOUNCE_RX.search(t): return "bounce"
    if OOO_RX.search(t): return "ooo"
    if STOP_RX.search(t): return "stop"
    if NEGATIVE_RX.search(t): return "no"
    if POSITIVE_RX.search(t): return "interested"
    return "reply"

# ── Gmail ───────────────────────────────────────────────────────────────────
def get_credentials(force=False):
    sheets._load_dotenv()
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    creds = None
    if not force and TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), GMAIL_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token and not force:
            creds.refresh(Request())
        else:
            cp = os.environ.get("GOOGLE_CREDENTIALS")
            flow = InstalledAppFlow.from_client_secrets_file(cp, GMAIL_SCOPES)
            creds = flow.run_local_server(port=8767, prompt="consent")
        TOKEN_PATH.write_text(creds.to_json())
    return creds

def gmail():
    from googleapiclient.discovery import build
    return build("gmail", "v1", credentials=get_credentials(), cache_discovery=False)

def _decode(part):
    data = part.get("body", {}).get("data")
    if not data: return ""
    try: return base64.urlsafe_b64decode(data + "===").decode("utf-8", errors="replace")
    except Exception: return ""

def _extract_text(payload):
    if not payload: return ""
    m = payload.get("mimeType", "")
    if m.startswith("text/plain"): return _decode(payload)
    if m.startswith("multipart/"):
        for p in payload.get("parts", []):
            t = _extract_text(p)
            if t: return t
    if m.startswith("text/html"): return re.sub(r"<[^>]+>", " ", _decode(payload))
    return ""

def cmd_scan(args):
    svc = gmail(); con = store.connect(); ensure_schema(con)
    sent_map = {e.lower(): d for d, e in con.execute("SELECT domain,email FROM outreach WHERE status='sent'")}
    tagged = 0; seen = set()
    for q in ["in:inbox newer_than:21d", "in:spam newer_than:21d", "in:anywhere newer_than:21d -in:sent -in:drafts -in:chats"]:
        page = None
        for _ in range(6):
            resp = svc.users().messages().list(userId="me", q=q, maxResults=100, pageToken=page, includeSpamTrash=True).execute()
            for m in resp.get("messages", []):
                if m["id"] in seen: continue
                seen.add(m["id"])
                full = svc.users().messages().get(userId="me", id=m["id"], format="full").execute()
                hdr = {h["name"].lower(): h["value"] for h in full["payload"].get("headers", [])}
                frm = parseaddr(hdr.get("from", ""))[1].lower()
                if frm not in sent_map: continue
                dom = sent_map[frm]
                already = con.execute("SELECT replied FROM outreach WHERE domain=? AND email=?", (dom, frm)).fetchone()
                if already and already[0]: continue
                klass = classify(hdr.get("subject",""), _extract_text(full["payload"]))
                con.execute("UPDATE outreach SET replied=1,replied_at=?,reply_class=?,reply_snippet=? WHERE domain=? AND email=?",
                            (store.now(), klass, full.get("snippet","")[:400], dom, frm))
                con.commit(); tagged += 1
                print(f"  • {frm:<38} → {klass}")
            page = resp.get("nextPageToken")
            if not page: break
    print(f"Scanned. Tagged {tagged} new replies.")
    auto = send_interested_replies(con)
    if auto: print(f"Auto-onboarding emails sent: {auto}")

def send_interested_replies(con):
    rows = con.execute("""SELECT o.domain,o.email,o.lang,l.company,l.city,l.country
        FROM outreach o LEFT JOIN leads l ON l.domain=o.domain
        WHERE o.replied=1 AND o.reply_class='interested' AND o.interested_reply_sent_at IS NULL""").fetchall()
    sent = 0
    for dom, em, lang, company, city, country in rows:
        subj_tpl, body_tpl = INTERESTED_REPLY.get(lang or "en", INTERESTED_REPLY["en"])
        nc = ""
        if company and len(company) < 60 and not any(s in company.lower() for s in ("rental","charter","boats","yacht","marina","tours")):
            nc = f" {company.split()[0]}"
        ctx = {"name_clause": nc, "site": outreach.SITE,
               "list_url": outreach._personalized_list_url({"domain":dom,"city":city,"country":country})}
        body = body_tpl.format(**ctx)
        rid, err = outreach.resend_send(em, subj_tpl, body, html=outreach._text_to_html(body, dom))
        if rid:
            con.execute("UPDATE outreach SET interested_reply_sent_at=? WHERE domain=? AND email=?", (store.now(), dom, em))
            con.commit(); sent += 1
            print(f"  ✦ auto-replied {em} ({dom})")
    return sent

# ── send follow-ups ─────────────────────────────────────────────────────────
def render_followup(rec, lang, broken_link=False):
    table = FOLLOWUP_404 if broken_link else FOLLOWUP
    subj_tpl, body_tpl = table.get(lang, table["en"])
    company = (rec.get("company") or "").strip()
    nc = ""
    if company and len(company) < 60 and any(c.isalpha() for c in company):
        if not any(s in company.lower() for s in ("rental","charter","boats","yacht","marina","tours")):
            nc = f" {company.split()[0]}"
    ctx = {"name_clause": nc, "city": rec.get("city") or "your area",
           "site": outreach.SITE, "list_url": outreach._personalized_list_url(rec)}
    return subj_tpl.format(**ctx), body_tpl.format(**ctx)

def followup_candidates(con, limit=None, shard=None, shards=None):
    # wrap sent_at in datetime() so ISO 'T'-separated timestamps parse to the
    # same canonical form as datetime('now') (lexical compare otherwise breaks).
    cur = con.execute(f"""SELECT o.domain,o.email,o.lang,l.company,l.city,l.country,o.sent_at
        FROM outreach o JOIN leads l ON l.domain=o.domain
        WHERE o.status='sent' AND (o.replied=0 OR o.replied IS NULL)
          AND (o.followup_sent_at IS NULL OR o.followup_sent_at='')
          AND (o.sent_at IS NULL OR o.sent_at='' OR datetime(o.sent_at) < datetime('now','-{FOLLOWUP_DAYS} days'))
        ORDER BY o.sent_at ASC""")
    rows = cur.fetchall()
    if shards:
        rows = [r for r in rows if (hash(r[0]) % shards) == shard]
    return rows[:limit] if limit else rows

def cmd_send(args):
    con = store.connect(); ensure_schema(con)
    rows = followup_candidates(con, limit=None if args.all else args.limit,
                               shard=args.shard, shards=args.shards)
    print(f"Follow-up candidates: {len(rows)}" + (f" (shard {args.shard}/{args.shards})" if args.shards else ""))
    if args.dry_run:
        for r in rows[:3]:
            dom, e, lang, company, city, country, sent_at = r
            broken = (sent_at or "") < FIX_DATE
            subj, body = render_followup({"company":company,"city":city,"domain":dom,"country":country}, lang, broken_link=broken)
            print(f"\n=== {dom} → {e} ({lang}) [{'404-recovery' if broken else 'standard'}] ===\nSubject: {subj}\n{body}")
        print(f"(dry-run; first 3 of {len(rows)})"); return
    sent = failed = 0
    for i, (dom, e, lang, company, city, country, sent_at) in enumerate(rows, 1):
        broken = (sent_at or "") < FIX_DATE
        rec = {"company":company,"city":city,"domain":dom,"country":country}
        subj, body = render_followup(rec, lang, broken_link=broken)
        target = "info@boathire24.com" if args.to_self else e
        rid, err = outreach.resend_send(target, subj, body, html=outreach._text_to_html(body, dom))
        if rid:
            con.execute("UPDATE outreach SET followup_sent_at=?,followup_resend_id=? WHERE domain=? AND email=?",
                        (store.now(), rid, dom, e)); con.commit(); sent += 1
            print(f"  [{i:>4}/{len(rows)}] ✓ {dom:<34} → {target} ({'404' if broken else 'std'})")
        else:
            failed += 1
            print(f"  [{i:>4}/{len(rows)}] ✗ {dom:<34} {err}")
        time.sleep(args.sleep + random.random() * 0.5)
    print(f"\nDone. sent={sent} failed={failed}")

def cmd_status(args):
    con = store.connect(); ensure_schema(con)
    for s, n in con.execute("SELECT status,COUNT(*) FROM outreach GROUP BY status"): print(f"  status={s:<10} {n}")
    print("Replies:")
    for c, n in con.execute("SELECT reply_class,COUNT(*) FROM outreach WHERE replied=1 GROUP BY reply_class ORDER BY COUNT(*) DESC"):
        print(f"  {c or 'unclassified':<12} {n}")
    fu = con.execute("SELECT COUNT(*) FROM outreach WHERE followup_sent_at IS NOT NULL").fetchone()[0]
    print(f"followups_sent={fu}  eligible_now={len(followup_candidates(con))}")

def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth").set_defaults(func=lambda a: (get_credentials(force=True), print("ok")))
    sub.add_parser("scan").set_defaults(func=cmd_scan)
    f = sub.add_parser("send")
    f.add_argument("--dry-run", action="store_true"); f.add_argument("--all", action="store_true")
    f.add_argument("--limit", type=int, default=50); f.add_argument("--to-self", action="store_true")
    f.add_argument("--sleep", type=float, default=1.5)
    f.add_argument("--shard", type=int); f.add_argument("--shards", type=int)
    f.set_defaults(func=cmd_send)
    sub.add_parser("status").set_defaults(func=cmd_status)
    args = ap.parse_args(); args.func(args)

if __name__ == "__main__":
    main()
