"""BoatHire24 travel-blog partnership outreach.

Discovers travel blogs via DuckDuckGo (keyword sweep + listicle outbound-link
crawl), enriches each with a contact-form URL + emails, stores everything in an
isolated set of SQLite tables (`blogs`, `blog_outreach`) and a dedicated Google
Sheet, then reaches out proposing a reciprocal content partnership — primarily
by filling the blog's contact form (Playwright), falling back to email.

Kept fully separate from the operator-listing campaign (`outreach`/`followup`)
so it can't disturb that sender-reputation-sensitive pipeline.

Subcommands:
  discover     keyword sweep → blogs table
  enrich       find contact form + emails for un-enriched blogs
  push-sheet   mirror blogs → "BoatHire24 Travel Blogs" Google Sheet
  send-form    fill contact forms (Playwright)      [outward action]
  send-email   email blogs with no form             [outward action]
  stats        counts

Contact identity used in every message:
  Mardo · info@boathire24.com · WhatsApp +37258155779
"""
from __future__ import annotations
import argparse, json, re, sys, time, pathlib, html as html_mod, urllib.parse, contextlib

from . import store, http as http_mod
from . import enrich as enrich_mod

# ── identity / message ──────────────────────────────────────────────────────
CONTACT_NAME  = "Mardo"
CONTACT_EMAIL = "info@boathire24.com"
CONTACT_WA    = "+37258155779"
SITE          = "https://boathire24.com"
SUBJECT       = "Content partnership with BoatHire24"

MESSAGE = """Hi,

I hope you're doing well.

We're reaching out from BoatHire24 to propose a simple content partnership. We'd publish an article featuring and linking to your travel blog, and we'd appreciate it if you could do the same for BoatHire24.

It's a great way for both of us to gain exposure and provide useful content to our audiences.

Let us know if you're interested!

Best regards,
Mardo
BoatHire24 Team
{email} · WhatsApp {wa}
{site}""".format(email=CONTACT_EMAIL, wa=CONTACT_WA, site=SITE)

# ── discovery keyword universe ──────────────────────────────────────────────
_NICHE = [
    "travel blog", "travel blogger", "sailing blog", "yacht blog", "boating blog",
    "boat travel blog", "adventure travel blog", "luxury travel blog",
    "family travel blog", "couples travel blog", "solo travel blog",
    "coastal travel blog", "island hopping blog", "beach travel blog",
    "digital nomad travel blog", "budget travel blog", "outdoor adventure blog",
    "watersports blog", "scuba diving blog", "yacht charter blog",
    "mediterranean travel blog", "greek islands travel blog", "croatia travel blog",
    "spain travel blog", "italy travel blog", "portugal travel blog",
    "caribbean travel blog", "thailand travel blog", "dubai travel blog",
    "france travel blog", "turkey travel blog", "amalfi coast travel blog",
    "cruise travel blog", "luxury yacht lifestyle blog",
]
_MODIFIERS = ["", "best ", "top "]
_TAILS = ["", " write for us", " 2026", " contact us"]

def keyword_universe():
    seen, out = set(), []
    for niche in _NICHE:
        for mod in _MODIFIERS:
            for tail in _TAILS:
                q = f"{mod}{niche}{tail}".strip()
                if q not in seen:
                    seen.add(q); out.append(q)
    return out

# ── domain filtering ────────────────────────────────────────────────────────
# Hosts we never want as outreach targets (social, video, OTAs, big media,
# marketplaces, competitors, our own properties, tooling).
BLOCK_SUBSTR = {
    "facebook", "instagram", "twitter", "x.com", "youtube", "youtu.be",
    "pinterest", "tiktok", "linkedin", "reddit", "quora", "tumblr.com",
    "flickr", "vimeo", "snapchat", "whatsapp", "telegram", "t.me",
    "tripadvisor", "booking.com", "expedia", "airbnb", "agoda", "hotels.com",
    "kayak", "skyscanner", "trivago", "getyourguide", "viator", "vrbo",
    "lonelyplanet", "nomadicmatt", "wikipedia", "wikivoyage", "amazon.",
    "google.", "bing.com", "duckduckgo", "yelp", "trustpilot",
    "getmyboat", "clickandboat", "samboat", "boatsetter", "boataround",
    "sailogy", "borrowaboat", "zizoo", "nautal", "boatjump", "yachtcharterfleet",
    "boathire24", "boatrentalmarbella", "boat-rental-marbella",
    "apple.com", "microsoft", "cloudflare", "wixsite.com/blog",
    "feedspot", "medium.com/tag", "goodreads",
}
# Blog *platforms* — the bare root is not a target, but a subdomain is one blog.
PLATFORM_ROOTS = {
    "wordpress.com", "blogspot.com", "substack.com", "wixsite.com",
    "weebly.com", "ghost.io", "medium.com", "blog.com", "typepad.com",
    "squarespace.com", "webflow.io", "over-blog.com",
}
ASSET_TLD = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".css", ".js",
             ".pdf", ".xml", ".ico")

def host_of(url):
    try:
        h = (urllib.parse.urlparse(url).hostname or "").lower()
    except Exception:
        return None
    return h[4:] if h.startswith("www.") else h

def registrable(host):
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host

def is_blog_candidate(host):
    if not host or "." not in host:
        return False
    if host.endswith(ASSET_TLD):
        return False
    low = host
    for b in BLOCK_SUBSTR:
        if b in low:
            return False
    reg = registrable(host)
    if reg in PLATFORM_ROOTS and host == reg:
        return False  # bare platform root, not an individual blog
    return True

# ── DuckDuckGo HTML search ──────────────────────────────────────────────────
DDG = "https://html.duckduckgo.com/html/"
_RESULT_RX = re.compile(r'href="(//duckduckgo\.com/l/\?[^"]+|https?://[^"]+)"[^>]*class="result__a"', re.I)

def _unwrap(href):
    if href.startswith("//duckduckgo.com/l/"):
        qs = urllib.parse.parse_qs(urllib.parse.urlparse("https:" + href).query)
        return urllib.parse.unquote(qs.get("uddg", [""])[0]) or None
    return href

def ddg_search(query):
    """Return a list of (url, title) result tuples, or None if the request
    failed / was blocked (so the caller can retry the keyword later)."""
    try:
        r = requests_post(DDG, {"q": query, "kl": "us-en"})
    except Exception:
        return None
    if not r or r.status_code != 200:
        return None
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(r.text, "lxml")
    anchors = soup.select("a.result__a")
    # A 200 with a challenge/empty body and no anchors is almost always a soft
    # block, not a truly empty SERP for these broad keywords → treat as failure.
    if not anchors:
        return None
    out = []
    for a in anchors:
        href = _unwrap(a.get("href", "") or "")
        if href:
            out.append((href, a.get_text(" ", strip=True)))
    return out

def requests_post(url, data):
    import requests, random
    headers = {"User-Agent": random.choice(http_mod.UAS),
               "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
               "Accept-Language": "en-US,en;q=0.9"}
    return requests.post(url, data=data, headers=headers, timeout=15)

# ── DB layer ────────────────────────────────────────────────────────────────
def ensure_tables(con):
    con.executescript("""
    CREATE TABLE IF NOT EXISTS blogs (
        domain        TEXT PRIMARY KEY,
        title         TEXT,
        source_kw     TEXT,
        first_seen    TEXT,
        last_enriched TEXT,
        emails        TEXT,
        phones        TEXT,
        contact_form  TEXT,
        whatsapp      TEXT,
        confidence    INTEGER DEFAULT 0,
        pushed_to_sheet INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS blog_kw_done ( kw TEXT PRIMARY KEY, done_at TEXT );
    CREATE TABLE IF NOT EXISTS blog_outreach (
        domain     TEXT PRIMARY KEY,
        channel    TEXT,          -- form / email
        target     TEXT,          -- form url or email
        sent_at    TEXT,
        status     TEXT,          -- submitted / sent / captcha / js_form / no_form / no_target / failed / skipped
        http_status INTEGER,
        detail     TEXT,
        replied    INTEGER DEFAULT 0
    );
    """)
    con.commit()

def add_blog(con, domain, title, kw):
    with contextlib.suppress(Exception):
        con.execute("INSERT OR IGNORE INTO blogs(domain,title,source_kw,first_seen) VALUES(?,?,?,?)",
                    (domain, (title or "")[:200], kw, store.now()))

def kw_done(con, kw):
    return con.execute("SELECT 1 FROM blog_kw_done WHERE kw=?", (kw,)).fetchone() is not None

def mark_kw(con, kw):
    con.execute("INSERT OR REPLACE INTO blog_kw_done(kw,done_at) VALUES(?,?)", (kw, store.now()))
    con.commit()

# ── discover ────────────────────────────────────────────────────────────────
LISTICLE_HINT = re.compile(r"\b(best|top|\d{2,3})\b", re.I)

def discover(con, limit_kw=None, crawl_listicles=True, sleep=2.0, verbose=True):
    ensure_tables(con)
    kws = [k for k in keyword_universe() if not kw_done(con, k)]
    if limit_kw:
        kws = kws[:limit_kw]
    total_new = 0
    for i, kw in enumerate(kws, 1):
        results = ddg_search(kw)
        if results is None:
            if verbose:
                print(f"[{i}/{len(kws)}] {kw!r:48} DDG blocked/failed — backing off, will retry")
            http_mod.polite_sleep(sleep * 3, sleep * 2)
            continue
        new = 0
        for url, title in results:
            h = host_of(url)
            if is_blog_candidate(h):
                before = con.total_changes
                add_blog(con, h, title, kw)
                if con.total_changes > before:
                    new += 1
            # crawl obvious listicles for outbound blog links (yield multiplier)
            if crawl_listicles and h and LISTICLE_HINT.search(title or "") \
               and not is_blog_candidate(h):  # listicle host itself is blocked media
                for oh, ot in _extract_outbound_blogs(url):
                    before = con.total_changes
                    add_blog(con, oh, ot, kw + " (listicle)")
                    if con.total_changes > before:
                        new += 1
        con.commit()
        mark_kw(con, kw)
        total_new += new
        if verbose:
            print(f"[{i}/{len(kws)}] {kw!r:48} +{new} new (total {total_new})")
        http_mod.polite_sleep(sleep, sleep)
    return total_new

def harvest_urls(con, urls, verbose=True):
    """Seed blogs by scraping outbound blog links from listicle/roundup URLs.
    Bypasses DDG rate-limiting: one 'best travel blogs' page yields ~40 blogs."""
    ensure_tables(con)
    total = 0
    for i, u in enumerate(urls, 1):
        u = u.strip()
        if not u:
            continue
        try:
            found = _extract_outbound_blogs(u, cap=80)
        except Exception as e:
            found = []
            if verbose:
                print(f"[{i}/{len(urls)}] {u[:60]:60} ERROR {e}")
            continue
        new = 0
        for oh, ot in found:
            before = con.total_changes
            add_blog(con, oh, ot, "listicle:" + (host_of(u) or ""))
            if con.total_changes > before:
                new += 1
        con.commit()
        total += new
        if verbose:
            print(f"[{i}/{len(urls)}] {u[:52]:52} +{new} blogs (total {total})")
        http_mod.polite_sleep(0.8, 0.8)
    return total

def _extract_outbound_blogs(listicle_url, cap=40):
    r = http_mod.get(listicle_url, timeout=12)
    if not r or r.status_code != 200:
        return []
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(r.text, "lxml")
    src_host = host_of(listicle_url)
    seen, out = set(), []
    for a in soup.find_all("a", href=True):
        h = host_of(a["href"])
        if not h or h == src_host or h in seen:
            continue
        if is_blog_candidate(h):
            seen.add(h)
            out.append((h, a.get_text(" ", strip=True)))
            if len(out) >= cap:
                break
    return out

# ── enrich ──────────────────────────────────────────────────────────────────
# Travel blogs bury their contact form on idiosyncratic pages and often render
# it with JS (no <form> in static HTML). We only need a good *URL* to hand to
# Playwright, which renders JS at submit time — so accept any page that either
# has a form/textarea OR is a known contact-ish path returning 200.
CONTACT_PATHS = ["/contact", "/contact-us", "/contact/", "/work-with-me",
                 "/work-with-us", "/collaborate", "/collaborations", "/partnerships",
                 "/partner-with-us", "/advertise", "/pr", "/press", "/hire-me",
                 "/lets-work-together", "/get-in-touch", "/about/contact"]
CONTACT_LINK_RX = re.compile(r"(contact|work[\s\-]?with|collaborat|partnership|advertise|get[\s\-]?in[\s\-]?touch|hire[\s\-]?me|press|\bpr\b)", re.I)

def find_contact_page(domain):
    """Return the best contact-page URL for a blog, or None."""
    base = f"https://{domain}"
    from bs4 import BeautifulSoup
    home = http_mod.get(base, timeout=12)
    # 1) scan homepage nav/footer links for a contact-ish anchor
    if home and home.status_code == 200:
        soup = BeautifulSoup(home.text, "lxml")
        for a in soup.find_all("a", href=True):
            blob = (a.get_text(" ", strip=True) + " " + a["href"]).lower()
            if CONTACT_LINK_RX.search(blob):
                full = urllib.parse.urljoin(base, a["href"])
                h = host_of(full)
                if h and (h == domain or h.endswith("." + domain) or domain.endswith("." + h)):
                    return full
        if soup.find("form") and soup.find("textarea"):
            return base  # homepage itself carries the form
    # 2) probe common contact paths
    for p in CONTACT_PATHS:
        r = http_mod.get(base + p, timeout=10)
        if r and r.status_code == 200 and ("<form" in r.text.lower() or "textarea" in r.text.lower()
                                           or CONTACT_LINK_RX.search(r.text[:4000] or "")):
            return base + p
        http_mod.polite_sleep(0.15, 0.2)
    return None

def _enrich_one(domain):
    try:
        info = enrich_mod.enrich_domain(domain)
    except Exception:
        info = {"emails": [], "phones": [], "contact_form": None, "whatsapp": None, "confidence": 0}
    if not info.get("contact_form"):
        try:
            info["contact_form"] = find_contact_page(domain)
        except Exception:
            pass
    return domain, info

def enrich(con, limit=200, workers=8, verbose=True):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    ensure_tables(con)
    rows = con.execute("SELECT domain FROM blogs WHERE last_enriched IS NULL LIMIT ?", (limit,)).fetchall()
    domains = [r[0] for r in rows]
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_enrich_one, d) for d in domains]
        for fut in as_completed(futs):
            domain, info = fut.result()
            con.execute("""UPDATE blogs SET emails=?, phones=?, contact_form=?, whatsapp=?,
                           confidence=?, last_enriched=? WHERE domain=?""",
                        (json.dumps(info.get("emails") or []), json.dumps(info.get("phones") or []),
                         info.get("contact_form"), info.get("whatsapp"),
                         info.get("confidence", 0), store.now(), domain))
            con.commit()
            done += 1
            if verbose:
                cf = "form" if info.get("contact_form") else "-"
                print(f"  [{done}/{len(domains)}] {domain:38} {cf:5} emails:{len(info.get('emails') or [])}")
    return done

# ── google sheet ────────────────────────────────────────────────────────────
BLOG_SHEET_STATE_KEY = "blog_spreadsheet_id"
BLOG_HEADER = ["domain", "website", "title", "contact_form_url", "emails",
               "whatsapp", "channel", "outreach_status", "sent_at", "first_seen", "source_kw"]

def _sheets():
    from . import sheets
    return sheets

def ensure_blog_sheet():
    sheets = _sheets()
    st = sheets._state()
    if st.get(BLOG_SHEET_STATE_KEY):
        return st[BLOG_SHEET_STATE_KEY]
    svc = sheets.service()
    res = svc.spreadsheets().create(
        body={"properties": {"title": "BoatHire24 Travel Blogs"},
              "sheets": [{"properties": {"title": "Blogs"}}]},
        fields="spreadsheetId").execute()
    sid = res["spreadsheetId"]
    svc.spreadsheets().values().update(spreadsheetId=sid, range="Blogs!A1",
        valueInputOption="RAW", body={"values": [BLOG_HEADER]}).execute()
    st[BLOG_SHEET_STATE_KEY] = sid
    sheets._save_state(st)
    return sid

def push_sheet(con, verbose=True):
    ensure_tables(con)
    sheets = _sheets()
    sid = ensure_blog_sheet()
    svc = sheets.service()
    rows = con.execute("""SELECT b.domain, b.title, b.contact_form, b.emails, b.whatsapp,
                          b.first_seen, b.source_kw, o.channel, o.status, o.sent_at
                          FROM blogs b LEFT JOIN blog_outreach o ON o.domain=b.domain
                          WHERE b.pushed_to_sheet=0 AND b.last_enriched IS NOT NULL""").fetchall()
    out = []
    for (domain, title, cf, emails_j, wa, first_seen, kw, channel, status, sent_at) in rows:
        try:
            emails = ", ".join(json.loads(emails_j) if emails_j else [])
        except Exception:
            emails = ""
        out.append([domain, f"https://{domain}", title or "", cf or "", emails, wa or "",
                    channel or "", status or "pending", sent_at or "", first_seen or "", kw or ""])
    if out:
        svc.spreadsheets().values().append(spreadsheetId=sid, range="Blogs!A1",
            valueInputOption="RAW", insertDataOption="INSERT_ROWS", body={"values": out}).execute()
        con.executemany("UPDATE blogs SET pushed_to_sheet=1 WHERE domain=?",
                        [(r[0],) for r in out])
        con.commit()
    if verbose:
        print(f"pushed {len(out)} rows → https://docs.google.com/spreadsheets/d/{sid}")
    return sid, len(out)

def sync_sheet(con, verbose=True):
    """Update channel/outreach_status/sent_at (cols G:I) for rows already in the
    sheet, so post-send outcomes are reflected without re-appending."""
    sheets = _sheets()
    st = sheets._state()
    sid = st.get(BLOG_SHEET_STATE_KEY)
    if not sid:
        if verbose: print("no blog sheet yet — run push-sheet first")
        return 0
    svc = sheets.service()
    col_a = svc.spreadsheets().values().get(spreadsheetId=sid, range="Blogs!A2:A").execute().get("values", [])
    row_of = {}
    for i, r in enumerate(col_a):
        if r and r[0]:
            row_of[r[0].strip().lower()] = i + 2  # sheet row (1-based, +header)
    orec = {d: (ch, s, sa) for d, ch, s, sa in con.execute(
        "SELECT domain, channel, status, sent_at FROM blog_outreach")}
    data = []
    for domain, (ch, status, sa) in orec.items():
        row = row_of.get(domain)
        if not row:
            continue
        data.append({"range": f"Blogs!G{row}:I{row}",
                     "values": [[ch or "", status or "", sa or ""]]})
    n = 0
    for i in range(0, len(data), 200):  # batch to keep requests small
        chunk = data[i:i+200]
        svc.spreadsheets().values().batchUpdate(spreadsheetId=sid,
            body={"valueInputOption": "RAW", "data": chunk}).execute()
        n += len(chunk)
    if verbose:
        print(f"synced {n} outreach statuses → https://docs.google.com/spreadsheets/d/{sid}")
    return n

# ── outreach: record helper ─────────────────────────────────────────────────
def record_outreach(con, domain, channel, target, status, http_status=None, detail=""):
    con.execute("""INSERT OR REPLACE INTO blog_outreach
        (domain,channel,target,sent_at,status,http_status,detail) VALUES(?,?,?,?,?,?,?)""",
        (domain, channel, target, store.now(), status, http_status, (detail or "")[:300]))
    con.commit()

def already_contacted(con, domain):
    r = con.execute("SELECT status FROM blog_outreach WHERE domain=?", (domain,)).fetchone()
    return r and r[0] in ("submitted", "sent")

# ── outreach: contact form via Playwright ───────────────────────────────────
FIELD_HINTS = {
    "name":    ["name", "your-name", "fullname", "full_name", "author", "nome", "nom"],
    "email":   ["email", "e-mail", "your-email", "correo", "mail"],
    "phone":   ["phone", "tel", "telephone", "whatsapp", "mobile", "telefono"],
    "subject": ["subject", "asunto", "objet", "betreff", "your-subject"],
    "message": ["message", "comment", "your-message", "mensaje", "msg", "body", "enquiry", "inquiry", "content", "text"],
}
CAPTCHA_HINT = re.compile(r"(recaptcha|g-recaptcha|hcaptcha|h-captcha|cf-turnstile|captcha)", re.I)

def _match_field(attrs, kind):
    blob = " ".join(str(attrs.get(a, "")) for a in ("name", "id", "placeholder", "aria-label")).lower()
    return any(h in blob for h in FIELD_HINTS[kind])

CONSENT_RX = re.compile(r"(accept|agree|got it|allow all|i understand|aceptar|acconsenti|accepter|zustimmen|ok)", re.I)

def _dismiss_overlays(page):
    """Click an obvious cookie/consent accept button so it doesn't cover the form."""
    for sel in ("button", "a[role=button]", "[class*=cookie] button", "[id*=consent] button"):
        for el in page.query_selector_all(sel)[:25]:
            try:
                txt = (el.inner_text() or "").strip()
            except Exception:
                continue
            if txt and len(txt) < 30 and CONSENT_RX.search(txt):
                with contextlib.suppress(Exception):
                    el.click(timeout=2000)
                    page.wait_for_timeout(400)
                    return
    return

def _iter_form_scopes(page):
    """Yield the main document plus every same-origin-ish iframe as form scopes —
    many blogs embed the contact form (Gravity/HubSpot/Google) in an iframe."""
    yield page
    for fr in page.frames:
        if fr is page.main_frame:
            continue
        yield fr

def _find_target_form(page):
    for scope in _iter_form_scopes(page):
        try:
            forms = scope.query_selector_all("form")
        except Exception:
            continue
        for f in forms:
            try:
                if f.query_selector("textarea") or _form_has_message(f):
                    return f
            except Exception:
                continue
    return None

def submit_form(page, form_url, domain=None):
    """Attempt to fill+submit one contact form. Returns (status, http_status, detail)."""
    resp = page.goto(form_url, wait_until="domcontentloaded", timeout=25000)
    http_status = resp.status if resp else None
    page.wait_for_timeout(1800)
    _dismiss_overlays(page)
    content = page.content()
    if CAPTCHA_HINT.search(content):
        return "captcha", http_status, "captcha present"
    target_form = _find_target_form(page)
    # Fallback: the stored URL had no fillable form → probe common contact paths.
    if not target_form and domain:
        base = f"https://{domain}"
        for p in CONTACT_PATHS:
            cand = base + p
            if cand == form_url:
                continue
            try:
                r2 = page.goto(cand, wait_until="domcontentloaded", timeout=15000)
            except Exception:
                continue
            page.wait_for_timeout(1500)
            if CAPTCHA_HINT.search(page.content()):
                return "captcha", (r2.status if r2 else None), f"captcha on {p}"
            target_form = _find_target_form(page)
            if target_form:
                form_url = cand
                http_status = r2.status if r2 else http_status
                break
    if not target_form:
        return "no_form", http_status, "no form with a message field"

    filled = {"name": False, "email": False, "message": False}
    # textareas → message
    for ta in target_form.query_selector_all("textarea"):
        _fill(ta, MESSAGE); filled["message"] = True
    # text inputs
    for inp in target_form.query_selector_all("input"):
        t = (inp.get_attribute("type") or "text").lower()
        if t in ("hidden", "submit", "button", "checkbox", "radio", "file", "image"):
            continue
        attrs = {a: inp.get_attribute(a) for a in ("name", "id", "placeholder", "aria-label")}
        if t == "email" or _match_field(attrs, "email"):
            _fill(inp, CONTACT_EMAIL); filled["email"] = True
        elif t == "tel" or _match_field(attrs, "phone"):
            _fill(inp, CONTACT_WA)
        elif _match_field(attrs, "name"):
            _fill(inp, CONTACT_NAME); filled["name"] = True
        elif _match_field(attrs, "subject"):
            _fill(inp, SUBJECT)
        elif _match_field(attrs, "message") and not filled["message"]:
            _fill(inp, MESSAGE); filled["message"] = True
    if not filled["email"] or not filled["message"]:
        return "js_form", http_status, f"could not fill required fields {filled}"

    # submit
    btn = (target_form.query_selector("button[type=submit]")
           or target_form.query_selector("input[type=submit]")
           or target_form.query_selector("button"))
    if not btn:
        return "js_form", http_status, "no submit button"
    try:
        btn.click(timeout=8000)
    except Exception as e:
        return "failed", http_status, f"click failed: {e}"
    page.wait_for_timeout(2500)
    after = page.content().lower()
    if CAPTCHA_HINT.search(after):
        return "captcha", http_status, "captcha after submit"
    if any(s in after for s in ("thank", "gracias", "merci", "received", "success",
                                "we'll be in touch", "message sent", "enviado", "grazie")):
        return "submitted", http_status, "confirmation text seen"
    # No explicit confirmation, but click succeeded → optimistic submitted.
    return "submitted", http_status, "submitted (no explicit confirmation)"

def _form_has_message(form):
    for inp in form.query_selector_all("input, textarea"):
        attrs = {a: inp.get_attribute(a) for a in ("name", "id", "placeholder", "aria-label")}
        if _match_field(attrs, "message"):
            return True
    return False

def _fill(el, value):
    with contextlib.suppress(Exception):
        el.fill(value)

def _email_fallback(con, domain, emails_j):
    """Reach a blog by email when its form couldn't be submitted. Returns
    (status, detail). Records nothing — caller records the combined outcome."""
    from . import outreach as ol
    try:
        emails = json.loads(emails_j) if emails_j else []
    except Exception:
        emails = []
    email = ol.best_email_for_domain(emails, domain)
    if not email:
        return None, None
    mid, err = ol.resend_send(email, SUBJECT, MESSAGE, from_=f"{CONTACT_NAME} <{CONTACT_EMAIL}>")
    if mid:
        return "sent", f"email→{email}"
    return None, f"email failed {err}"

def send_forms(con, limit=25, dry_run=False, headless=True, verbose=True, email_fallback=True):
    ensure_tables(con)
    rows = con.execute("""SELECT domain, contact_form, emails FROM blogs
        WHERE contact_form IS NOT NULL AND contact_form != ''
          AND domain NOT IN (SELECT domain FROM blog_outreach WHERE status IN ('submitted','sent','skipped'))
        LIMIT ?""", (limit,)).fetchall()
    if verbose:
        print(f"{len(rows)} blogs with a contact form to try (dry_run={dry_run})")
    if dry_run:
        for d, cf, _ in rows:
            print(f"  WOULD submit → {d}  {cf}")
        return 0
    from playwright.sync_api import sync_playwright
    n_ok = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        ctx = browser.new_context(user_agent=http_mod.UAS[0], locale="en-US")
        for domain, cf, emails_j in rows:
            page = ctx.new_page()
            try:
                status, hs, detail = submit_form(page, cf, domain)
            except Exception as e:
                status, hs, detail = "failed", None, f"{type(e).__name__}: {e}"
            with contextlib.suppress(Exception):
                page.close()
            channel = "form"
            # Form couldn't go through → try email so the lead isn't wasted.
            if status != "submitted" and email_fallback:
                fb_status, fb_detail = _email_fallback(con, domain, emails_j)
                if fb_status:
                    status, channel, detail = fb_status, "form→email", f"{detail[:30]} | {fb_detail}"
            record_outreach(con, domain, channel, cf, status, hs, detail)
            if status in ("submitted", "sent"):
                n_ok += 1
            if verbose:
                print(f"  {status:10} {channel:10} {domain:36} {detail[:50]}")
            http_mod.polite_sleep(1.2, 1.2)
        browser.close()
    return n_ok

# ── outreach: email fallback ────────────────────────────────────────────────
def send_emails(con, limit=50, dry_run=False, verbose=True, any_form=False):
    ensure_tables(con)
    from . import outreach as ol
    # Default: only form-less blogs (forms handled by send_forms). With any_form,
    # email every blog that has an address and hasn't been contacted yet — used to
    # guarantee daily volume when contact-form automation under-delivers.
    form_clause = "" if any_form else "(contact_form IS NULL OR contact_form='') AND"
    rows = con.execute(f"""SELECT domain, emails FROM blogs
        WHERE {form_clause}
          emails IS NOT NULL AND emails NOT IN ('','[]')
          AND domain NOT IN (SELECT domain FROM blog_outreach WHERE status IN ('submitted','sent','skipped'))
        LIMIT ?""", (limit,)).fetchall()
    if verbose:
        print(f"{len(rows)} blogs (form-less, have email) to email (dry_run={dry_run})")
    sent = 0
    for domain, emails_j in rows:
        try:
            emails = json.loads(emails_j)
        except Exception:
            emails = []
        email = ol.best_email_for_domain(emails, domain)
        if not email:
            record_outreach(con, domain, "email", "", "no_target", None, "no usable email")
            continue
        if dry_run:
            print(f"  WOULD email → {email}  ({domain})")
            continue
        mid, err = ol.resend_send(email, SUBJECT, MESSAGE,
                                  from_=f"{CONTACT_NAME} <{CONTACT_EMAIL}>")
        status = "sent" if mid else "failed"
        record_outreach(con, domain, "email", email, status, None, err or mid or "")
        if mid:
            sent += 1
        if verbose:
            print(f"  {status:8} {email:40} {err or ''}")
        time.sleep(1.5)
    return sent

# ── stats ───────────────────────────────────────────────────────────────────
def stats(con):
    ensure_tables(con)
    g = lambda q: con.execute(q).fetchone()[0]
    print("blogs                :", g("SELECT COUNT(*) FROM blogs"))
    print("  enriched           :", g("SELECT COUNT(*) FROM blogs WHERE last_enriched IS NOT NULL"))
    print("  with contact form  :", g("SELECT COUNT(*) FROM blogs WHERE contact_form IS NOT NULL AND contact_form!=''"))
    print("  with email         :", g("SELECT COUNT(*) FROM blogs WHERE emails NOT IN ('','[]') AND emails IS NOT NULL"))
    print("  pushed to sheet    :", g("SELECT COUNT(*) FROM blogs WHERE pushed_to_sheet=1"))
    print("keywords swept       :", g("SELECT COUNT(*) FROM blog_kw_done"), "/", len(keyword_universe()))
    for status, n in con.execute("SELECT status, COUNT(*) FROM blog_outreach GROUP BY status ORDER BY 2 DESC"):
        print(f"  outreach {status:12}: {n}")

# ── CLI ─────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="BoatHire24 travel-blog partnership outreach")
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("discover"); d.add_argument("--limit-kw", type=int)
    d.add_argument("--no-listicles", action="store_true"); d.add_argument("--sleep", type=float, default=2.0)
    hv = sub.add_parser("harvest-urls"); hv.add_argument("--file", required=True,
        help="newline-separated listicle/roundup URLs to scrape outbound blog links from")
    e = sub.add_parser("enrich"); e.add_argument("--limit", type=int, default=200)
    e.add_argument("--workers", type=int, default=8)
    sub.add_parser("push-sheet")
    sub.add_parser("sync-sheet")
    f = sub.add_parser("send-form"); f.add_argument("--limit", type=int, default=25)
    f.add_argument("--dry-run", action="store_true"); f.add_argument("--headed", action="store_true")
    m = sub.add_parser("send-email"); m.add_argument("--limit", type=int, default=50)
    m.add_argument("--dry-run", action="store_true"); m.add_argument("--any", action="store_true",
        help="email every blog with an address (incl. form-havers), not just form-less ones")
    sub.add_parser("stats")

    a = ap.parse_args()
    con = store.connect()
    if a.cmd == "discover":
        n = discover(con, limit_kw=a.limit_kw, crawl_listicles=not a.no_listicles, sleep=a.sleep)
        print(f"discover done: +{n} new blogs")
    elif a.cmd == "harvest-urls":
        urls = pathlib.Path(a.file).read_text().splitlines()
        print(f"harvested: +{harvest_urls(con, urls)} new blogs from {len(urls)} URLs")
    elif a.cmd == "enrich":
        print("enriched:", enrich(con, limit=a.limit, workers=a.workers))
    elif a.cmd == "push-sheet":
        push_sheet(con)
    elif a.cmd == "sync-sheet":
        sync_sheet(con)
    elif a.cmd == "send-form":
        print("submitted:", send_forms(con, limit=a.limit, dry_run=a.dry_run, headless=not a.headed))
    elif a.cmd == "send-email":
        print("sent:", send_emails(con, limit=a.limit, dry_run=a.dry_run, any_form=a.any))
    elif a.cmd == "stats":
        stats(con)

if __name__ == "__main__":
    main()
