"""Per-domain enrichment: crawl key pages → emails, phones, contact-form URL,
and social handles (Instagram / Facebook / WhatsApp)."""
from __future__ import annotations
import re, urllib.parse, html as html_mod
from bs4 import BeautifulSoup
from . import http as http_mod

EMAIL_RX = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RX = re.compile(r"(?:(?:\+|00)\d{1,3}[\s\-.]?)?(?:\(?\d{2,4}\)?[\s\-.]?){2,5}\d{2,4}")
OBFUSC_AT = re.compile(r"\s*(?:\[at\]|\(at\)|\s+at\s+)\s*", re.I)
OBFUSC_DOT = re.compile(r"\s*(?:\[dot\]|\(dot\)|\s+dot\s+)\s*", re.I)
IG_RX = re.compile(r"(?:instagram\.com|instagr\.am)/([A-Za-z0-9_.]+)", re.I)
FB_RX = re.compile(r"facebook\.com/([A-Za-z0-9_.\-/]+)", re.I)
WA_RX = re.compile(r"(?:wa\.me/|api\.whatsapp\.com/send\?phone=)(\+?\d{7,15})", re.I)

CANDIDATE_PATHS = ["/", "/contact", "/contact-us", "/contacto", "/contatti", "/kontakt",
                   "/about", "/about-us", "/imprint", "/impressum", "/legal", "/aviso-legal",
                   "/mentions-legales", "/team"]

BAD_EMAIL_DOMAINS = {"sentry.io","wixpress.com","example.com","domain.com","youremail.com",
                     "test.com","google-analytics.com","googletagmanager.com","godaddy.com"}
BAD_LOCALS = {"u003e","u003c","you","your","name","example"}
IG_SKIP = {"p","reel","reels","explore","tv","stories","accounts","about"}
FB_SKIP = {"sharer","share","dialog","tr","plugins","profile.php","login","pages"}

def normalize_email(e):
    e = e.strip().strip(".,;:()<>[]'\"").lower()
    if not e or "@" not in e: return None
    local, _, dom = e.partition("@")
    if not local or "." not in dom: return None
    if dom in BAD_EMAIL_DOMAINS or local in BAD_LOCALS: return None
    if any(dom.endswith(x) for x in (".png",".jpg",".jpeg",".gif",".webp",".svg",".css",".js")): return None
    return e if len(e) <= 80 else None

def normalize_phone(p):
    d = re.sub(r"[^\d+]", "", p)
    if d.startswith("00"): d = "+" + d[2:]
    if not d.startswith("+"): return None
    return d if 9 <= len(d) <= 16 else None

def deobfuscate(t):
    return OBFUSC_DOT.sub(".", OBFUSC_AT.sub("@", t))

def extract_from_html(html, base_url):
    soup = BeautifulSoup(html, "lxml")
    emails, phones = set(), set()
    contact_form = None; insta = None; fb = None; wa = None
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        low = href.lower()
        if low.startswith("mailto:"):
            e = normalize_email(urllib.parse.unquote(href[7:].split("?")[0]))
            if e: emails.add(e)
        elif low.startswith("tel:"):
            p = normalize_phone(urllib.parse.unquote(href[4:]))
            if p: phones.add(p)
        else:
            m = IG_RX.search(href)
            if m and not insta and m.group(1).lower() not in IG_SKIP: insta = m.group(1)
            m = FB_RX.search(href)
            if m and not fb and m.group(1).split("/")[0].lower() not in FB_SKIP: fb = m.group(1).split("/")[0]
            m = WA_RX.search(href)
            if m and not wa: wa = m.group(1)
    if any(k in base_url.lower() for k in ("/contact","/contacto","/contatti","/kontakt")):
        if soup.find("form"): contact_form = base_url
    text = html_mod.unescape(deobfuscate(soup.get_text(" ", strip=True)))
    for m in EMAIL_RX.findall(text):
        e = normalize_email(m)
        if e: emails.add(e)
    for m in PHONE_RX.findall(text):
        p = normalize_phone(m)
        if p: phones.add(p)
    return emails, phones, contact_form, insta, fb, wa

def enrich_domain(domain, max_pages=7):
    base = f"https://{domain}"
    emails, phones = set(), set()
    contact_form = insta = fb = wa = None
    pages = 0; visited = set(); queue = [base + p for p in CANDIDATE_PATHS]
    home = http_mod.get(base)
    if home and home.status_code == 200:
        pages += 1; visited.add(base)
        e,p,cf,ig,f,w = extract_from_html(home.text, base)
        emails|=e; phones|=p
        contact_form = contact_form or cf; insta = insta or ig; fb = fb or f; wa = wa or w
        soup = BeautifulSoup(home.text, "lxml")
        for a in soup.find_all("a", href=True)[:200]:
            href = a["href"]
            if any(k in href.lower() for k in ("contact","contacto","contatti","kontakt","about","impressum","legal")):
                full = urllib.parse.urljoin(base, href)
                h = urllib.parse.urlparse(full).hostname
                if h and domain in h and full not in queue: queue.append(full)
        http_mod.polite_sleep(0.4, 0.4)
    for url in queue:
        if pages >= max_pages: break
        if url in visited: continue
        visited.add(url)
        r = http_mod.get(url)
        if not r or r.status_code != 200: continue
        pages += 1
        e,p,cf,ig,f,w = extract_from_html(r.text, url)
        emails|=e; phones|=p
        contact_form = contact_form or cf; insta = insta or ig; fb = fb or f; wa = wa or w
        http_mod.polite_sleep(0.3, 0.3)
    root = domain.split(".")[-2] if "." in domain else domain
    on = {e for e in emails if root in e.split("@")[1]}
    if on: emails = on
    conf = (50 if emails else 0) + (25 if phones else 0) + (15 if contact_form else 0) + (10 if insta else 0) + min(5, pages)
    return {"emails": sorted(emails), "phones": sorted(phones), "contact_form": contact_form,
            "instagram": insta, "facebook": fb, "whatsapp": wa, "confidence": conf, "pages_hit": pages}
