"""Competitor-marketplace listing scraper — harvest boat operators from
COMPETITOR platforms (operators already proven willing to list elsewhere) into
leads.db. Mirrors seed_maps.py: writes leads via store.add_seed(...), dedups
query-units via store.url_seen / store.mark_url, and EXCLUDEs aggregator domains.

Discovery only — NEVER sends email. Uses urllib (stdlib) + a browser UA.

SEED RULE: store.add_seed is called ONLY when a listing resolves to a real
EXTERNAL operator domain (never a competitor's own domain — those are
aggregators). Listings that yield only name+location with no external site are
collected into a report list and printed, but NOT seeded (not yet contactable).

Per-platform reality (see module docstrings / RECON below):
  - boatsetter : has `company_website` on each /boats/<id> detail page -> SEEDABLE
  - getmyboat  : intermediated; only owner first-name -> report-only
  - sailo      : intermediated; boat name + owner first-name -> report-only
  - clickandboat / boataround : listings rendered via robots-Disallowed or
                 WAF-protected XHR; no server-side data -> report-only / skip

  python3 -m scripts.scraper.competitor_scrape --dry-run --platform boatsetter --limit-cities 1
  python3 -m scripts.scraper.competitor_scrape --platform boatsetter --shard 0 --shards 4
"""
from __future__ import annotations
import argparse, json, re, time, random, urllib.parse, urllib.request, urllib.error
import tldextract
from . import store

# Browser UA pool — matches the recon that returned CF=0 on a plain curl.
UAS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
]

# Aggregator / non-operator domains we must NEVER seed (superset of seed_maps EXCLUDE
# plus the competitor hosts themselves and common CDNs that can leak into hrefs).
EXCLUDE = {
    "clickandboat.com", "samboat.com", "boatsetter.com", "getmyboat.com",
    "boataround.com", "sailo.com", "sailogy.com", "yachtcharterfleet.com",
    "bednblue.com", "facebook.com", "instagram.com", "tripadvisor.com",
    "viator.com", "getyourguide.com", "google.com", "expedia.com", "booking.com",
    "youtube.com", "linkedin.com", "twitter.com", "x.com", "pinterest.com",
    "wa.me", "whatsapp.com", "apple.com", "apps.apple.com", "play.google.com",
    "amazonaws.com", "cloudfront.net", "googleapis.com", "gstatic.com",
    "schema.org", "w3.org", "doubleclick.net", "yachtsbt.com", "awswaf.com",
}

# City list mirrors seed_maps (name, ISO country). Trimmed to the proven boating
# markets; --limit-cities / --shard / --shards behave exactly like seed_maps.
CITIES = [
    ("Dubai", "AE"), ("Abu Dhabi", "AE"),
    ("Miami", "US"), ("Fort Lauderdale", "US"), ("Key West", "US"),
    ("San Diego", "US"), ("Los Angeles", "US"), ("New York", "US"),
    ("Tampa", "US"), ("Naples Florida", "US"), ("Newport Beach", "US"),
    ("Marbella", "ES"), ("Barcelona", "ES"), ("Ibiza", "ES"),
    ("Palma de Mallorca", "ES"), ("Valencia", "ES"), ("Alicante", "ES"),
    ("Lisbon", "PT"), ("Vilamoura", "PT"),
    ("Nice", "FR"), ("Cannes", "FR"), ("Antibes", "FR"), ("Marseille", "FR"),
    ("Naples", "IT"), ("Capri", "IT"), ("Olbia", "IT"), ("Palermo", "IT"),
    ("Split", "HR"), ("Dubrovnik", "HR"), ("Zadar", "HR"),
    ("Athens", "GR"), ("Mykonos", "GR"), ("Rhodes", "GR"), ("Corfu", "GR"),
    ("Bodrum", "TR"), ("Marmaris", "TR"), ("Fethiye", "TR"),
    ("Cancun", "MX"), ("Cabo San Lucas", "MX"), ("Puerto Vallarta", "MX"),
    ("Nassau", "BS"), ("Tortola", "VG"), ("St Thomas", "VI"),
    ("Phuket", "TH"), ("Singapore", "SG"), ("Bali", "ID"),
    ("Sydney", "AU"), ("Gold Coast", "AU"),
]

# ---------------------------------------------------------------------------
# HTTP / parsing helpers (urllib stdlib + browser UA, like seed_maps).
# ---------------------------------------------------------------------------

def _fetch(url, timeout=25, retries=2, accept="text/html,application/xhtml+xml,*/*;q=0.8"):
    """GET a URL with a browser UA. Returns decoded body or None."""
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, headers={
            "User-Agent": random.choice(UAS),
            "Accept": accept,
            "Accept-Language": "en-US,en;q=0.9",
        })
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                return raw.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < retries:
                time.sleep(2 ** attempt + random.random()); continue
            return None
        except Exception:
            if attempt < retries:
                time.sleep(1 + random.random()); continue
            return None
    return None


def _sleep():
    """Polite throttle between requests."""
    time.sleep(1.0 + random.random() * 1.2)


def _root(url):
    """Registrable root domain (example.com) or None."""
    if not url:
        return None
    if not re.match(r"^https?://", url):
        url = "http://" + url.lstrip("/")
    try:
        ext = tldextract.extract(url)
        return f"{ext.domain}.{ext.suffix}".lower() if ext.domain and ext.suffix else None
    except Exception:
        return None


def _excluded(root):
    return (not root) or root in EXCLUDE or any(root.endswith("." + b) for b in EXCLUDE)


def _next_data(html):
    """Parse a Next.js __NEXT_DATA__ blob -> dict, or {}."""
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(1))
    except Exception:
        return {}


def _ld_json(html):
    """Yield parsed application/ld+json objects."""
    for m in re.finditer(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S):
        try:
            yield json.loads(m.group(1))
        except Exception:
            continue


# ---------------------------------------------------------------------------
# BOATSETTER — the only platform that exposes an external operator website.
#
# Search : GET /a/boat-rentals/search?near=<City>&page=N
#          -> HTML carrying __NEXT_DATA__.props.pageProps.ssrBoats (18/page)
#             and .ssrMeta.total_pages / .ssrMeta.total_count.
#          Each ssrBoats item: boat_public_id, title, location.display_location.
# Detail : GET /boats/<boat_public_id>
#          -> __NEXT_DATA__ ... dehydratedState.queries[boatDetail].state.data
#             which carries `company_website` (EXTERNAL operator site, when the
#             owner filled it in) + primary_manager{first,last} + location.
# ---------------------------------------------------------------------------

BS_BASE = "https://www.boatsetter.com"


def _bs_search_page(city, page):
    """Return (ssrBoats list, total_pages) for one search page, or ([], 0)."""
    q = urllib.parse.urlencode({"near": city, "page": page})
    html = _fetch(f"{BS_BASE}/a/boat-rentals/search?{q}")
    if not html:
        return [], 0
    pp = _next_data(html).get("props", {}).get("pageProps", {})
    boats = pp.get("ssrBoats") or []
    total_pages = (pp.get("ssrMeta") or {}).get("total_pages") or 0
    return (boats if isinstance(boats, list) else []), int(total_pages or 0)


def _bs_detail(boat_id):
    """Fetch a Boatsetter boat detail -> dict with company_website/manager/location."""
    html = _fetch(f"{BS_BASE}/boats/{boat_id}")
    if not html:
        return None
    dh = _next_data(html).get("props", {}).get("pageProps", {}).get("dehydratedState", {})
    for q in (dh.get("queries", []) if isinstance(dh, dict) else []):
        if (q.get("queryKey") or [None])[0] == "boatDetail":
            data = q.get("state", {}).get("data")
            if isinstance(data, dict):
                return data
    return None


def scrape_boatsetter(con, city, country, dry_run, max_pages_per_city=3, max_details=40):
    """Search a city, walk detail pages, seed any external company_website.
    Returns (added, n_listings, n_with_site, report_rows)."""
    added = 0
    report = []
    seen_ids = []
    # 1) gather boat ids across a few search pages (each query-unit is dedup-tracked)
    page = 1
    total_pages = 1
    while page <= min(max_pages_per_city, total_pages or 1):
        ck = f"boatsetter::search::{city}::p{page}"
        if store.url_seen(con, ck) and not dry_run:
            page += 1
            continue
        boats, tp = _bs_search_page(city, page)
        total_pages = tp or total_pages
        if not dry_run:
            store.mark_url(con, ck, 200 if boats else 1)
        for b in boats:
            bid = b.get("boat_public_id")
            if bid and bid not in seen_ids:
                seen_ids.append(bid)
        if not boats:
            break
        page += 1
        _sleep()

    n_listings = len(seen_ids)
    n_with_site = 0

    # 2) visit detail pages to pull company_website (cap to stay polite)
    for bid in seen_ids[:max_details]:
        ck = f"boatsetter::detail::{bid}"
        if store.url_seen(con, ck) and not dry_run:
            continue
        bd = _bs_detail(bid)
        if not dry_run:
            store.mark_url(con, ck, 200 if bd else 1)
        _sleep()
        if not bd:
            continue
        loc = bd.get("location") or {}
        lcity = loc.get("city") or city
        lcountry = loc.get("country_code") or country
        mgr = bd.get("primary_manager") or {}
        name = (" ".join(x for x in (mgr.get("first_name"), mgr.get("last_name")) if x)
                or bd.get("listing_tagline") or "")[:120]
        site = (bd.get("company_website") or "").strip()
        root = _root(site) if site else None
        if root and not _excluded(root):
            n_with_site += 1
            if dry_run:
                print(f"    [SEED] {root:<28} {name[:30]:<30} {lcity},{lcountry}  (boat {bid})")
            else:
                store.add_seed(con, root, lcity, lcountry, "competitor_boatsetter", company=name)
                added += 1
        else:
            # name + location only, no external site -> report, do NOT seed
            report.append({"platform": "boatsetter", "name": name, "city": lcity,
                           "country": lcountry, "listing": f"{BS_BASE}/boats/{bid}",
                           "company_website": site or None})
    return added, n_listings, n_with_site, report


# ---------------------------------------------------------------------------
# GETMYBOAT — intermediated. City page (200) carries __NEXT_DATA__ but the live
# search results hydrate client-side; only landingPageData.top_categories[].results
# is server-rendered, and each result's user_details exposes just a first name +
# initial (no company, no external website). REPORT-ONLY.
# ---------------------------------------------------------------------------

GMB_BASE = "https://www.getmyboat.com"


def _gmb_city_path(city, country):
    # mirrors the on-site format: "Dubai--Dubai--United-Arab-Emirates"
    parts = [p for p in (city, _COUNTRY_NAME.get(country, country)) if p]
    slug = "--".join(parts).replace(" ", "-")
    return f"{GMB_BASE}/boat-rental/{urllib.parse.quote(slug)}/"


def scrape_getmyboat(con, city, country, dry_run, **_):
    report = []
    ck = f"getmyboat::city::{city}"
    if store.url_seen(con, ck) and not dry_run:
        return 0, 0, 0, report
    html = _fetch(_gmb_city_path(city, country))
    if not dry_run:
        store.mark_url(con, ck, 200 if html else 1)
    if not html:
        return 0, 0, 0, report
    pp = _next_data(html).get("props", {}).get("pageProps", {})
    results = []
    for cat in (pp.get("landingPageData", {}) or {}).get("top_categories", []) or []:
        results += cat.get("results", []) or []
    n = 0
    for r in results:
        ud = r.get("user_details") or {}
        name = (" ".join(x for x in (ud.get("first_name"), ud.get("last_name")) if x)
                or r.get("headline") or "")[:120]
        if not name:
            continue
        n += 1
        report.append({"platform": "getmyboat", "name": name, "city": city,
                       "country": country,
                       "listing": GMB_BASE + (r.get("listing_url") or ""),
                       "company_website": None})
    # No external website ever exposed -> 0 seeded, 0 with-site.
    return 0, n, 0, report


# ---------------------------------------------------------------------------
# SAILO — intermediated. Listing page (200) ld+json ItemList enumerates internal
# /boats/.../rental_boat_<id>/ detail URLs; detail pages expose boat name + owner
# first-name but NO external operator website. REPORT-ONLY.
# ---------------------------------------------------------------------------

SAILO_BASE = "https://www.sailo.com"

# Sailo listing path uses /boat-rentals/<STATE>/<City> for US, /boat-rentals/<Country>
# elsewhere. We only have a US-state map for the few US cities; non-US falls back
# to a country-name path which Sailo redirects/handles.
_US_STATE = {
    "Miami": "FL", "Fort Lauderdale": "FL", "Key West": "FL", "Tampa": "FL",
    "Naples Florida": "FL", "San Diego": "CA", "Los Angeles": "CA",
    "Newport Beach": "CA", "New York": "NY",
}


def _sailo_listing_url(city, country):
    if country == "US" and city in _US_STATE:
        return f"{SAILO_BASE}/boat-rentals/{_US_STATE[city]}/{city.replace(' ', '_')}"
    cn = _COUNTRY_NAME.get(country, country).replace(" ", "_")
    return f"{SAILO_BASE}/boat-rentals/{cn}"


def scrape_sailo(con, city, country, dry_run, **_):
    report = []
    ck = f"sailo::city::{city}"
    if store.url_seen(con, ck) and not dry_run:
        return 0, 0, 0, report
    html = _fetch(_sailo_listing_url(city, country))
    if not dry_run:
        store.mark_url(con, ck, 200 if html else 1)
    if not html:
        return 0, 0, 0, report
    urls = []
    for d in _ld_json(html):
        if d.get("@type") == "ItemList":
            for it in d.get("itemListElement", []) or []:
                u = it.get("url")
                if u and "/boats/" in u:
                    urls.append(u)
    urls = list(dict.fromkeys(urls))
    n = len(urls)
    for u in urls:
        report.append({"platform": "sailo", "name": None, "city": city,
                       "country": country, "listing": u, "company_website": None})
    # No external website exposed -> 0 seeded.
    return 0, n, 0, report


# ---------------------------------------------------------------------------
# CLICK&BOAT — city pages exist (country/region/city slugs) but the listing data
# loads from /api/ which robots.txt Disallows, and the server-side ld+json ItemList
# is a stub (name/url = None). No usable server-rendered operator data. SKIP.
# ---------------------------------------------------------------------------

def scrape_clickandboat(con, city, country, dry_run, **_):
    # Honestly non-viable via stdlib HTML: data is behind a Disallowed /api/ XHR.
    return 0, 0, 0, []


# ---------------------------------------------------------------------------
# BOATAROUND — /search?destinations=<slug> renders results via an AWS-WAF-guarded
# XHR; static HTML contains no boat detail links or operator data. SKIP.
# ---------------------------------------------------------------------------

def scrape_boataround(con, city, country, dry_run, **_):
    return 0, 0, 0, []


# ---------------------------------------------------------------------------

_COUNTRY_NAME = {
    "AE": "United-Arab-Emirates", "US": "United-States", "ES": "Spain",
    "PT": "Portugal", "FR": "France", "IT": "Italy", "HR": "Croatia",
    "GR": "Greece", "TR": "Turkey", "MX": "Mexico", "BS": "Bahamas",
    "VG": "British-Virgin-Islands", "VI": "U.S.-Virgin-Islands",
    "TH": "Thailand", "SG": "Singapore", "ID": "Indonesia", "AU": "Australia",
}

PLATFORMS = {
    "boatsetter": scrape_boatsetter,
    "getmyboat": scrape_getmyboat,
    "sailo": scrape_sailo,
    "clickandboat": scrape_clickandboat,
    "boataround": scrape_boataround,
}


def run(platform=None, shard=None, shards=None, limit_cities=None, dry_run=False):
    con = store.connect()
    cities = CITIES[:limit_cities] if limit_cities else CITIES
    if shards:
        cities = [c for i, c in enumerate(cities) if i % shards == shard]
    plats = [platform] if platform else list(PLATFORMS)

    totals = {p: {"added": 0, "listings": 0, "with_site": 0} for p in plats}
    report = []
    for p in plats:
        fn = PLATFORMS[p]
        print(f"\n=== {p.upper()} ({'DRY-RUN' if dry_run else 'LIVE'}) ===", flush=True)
        for ci, (city, country) in enumerate(cities, 1):
            added, n, n_site, rows = fn(con, city, country, dry_run)
            totals[p]["added"] += added
            totals[p]["listings"] += n
            totals[p]["with_site"] += n_site
            report += rows
            print(f"  [{ci:>2}/{len(cities)}] {city:<18} listings={n:<4} "
                  f"with_site={n_site:<3} seeded={added}", flush=True)

    print("\n==================== SUMMARY ====================")
    for p in plats:
        t = totals[p]
        print(f"  {p:<13} listings={t['listings']:<5} "
              f"resolvable_external_site={t['with_site']:<5} seeded={t['added']}")
    # Report-only (no external site) sample — these are NOT contactable yet.
    no_site = [r for r in report if not r.get("company_website")]
    if no_site:
        print(f"\n  REPORT-ONLY (name+location, no external site, NOT seeded): "
              f"{len(no_site)} listings. Sample:")
        for r in no_site[:12]:
            nm = r.get("name") or "(boat listing)"
            print(f"    - [{r['platform']}] {nm[:34]:<34} {r['city']},{r['country']}  {r['listing']}")
    return {"totals": totals, "report_count": len(report), "no_site": len(no_site)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Competitor-marketplace lead scraper (discovery only).")
    ap.add_argument("--platform", choices=list(PLATFORMS), help="limit to one platform")
    ap.add_argument("--shard", type=int)
    ap.add_argument("--shards", type=int)
    ap.add_argument("--limit-cities", type=int)
    ap.add_argument("--dry-run", action="store_true", help="print what it WOULD harvest; write nothing")
    a = ap.parse_args()
    print(run(a.platform, a.shard, a.shards, a.limit_cities, a.dry_run))
