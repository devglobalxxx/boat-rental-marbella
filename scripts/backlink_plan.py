#!/usr/bin/env python3
"""Stateless per-article PLANNER for BoatHire24 backlink articles.

Turns the SEO blueprint's link/anchor/image rules into a concrete assignment for
each article: which location to target, which secondary deep page (relevance
matched), how many links (weighted 25/50/25), the anchor text per link (archetype
mapped to target type), and 1-2 relevant images with alt/caption. Shared by the
DeepSeek generator (backlink_generate.py) and the Claude seed workflow so both
follow identical rules.

CLI (emit assignments as JSON for a workflow):
  python3 scripts/backlink_plan.py <channel> <count> [start_index]
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from boat_images import pick_images, figure_html  # noqa: E402

URLS = json.loads((ROOT / "config" / "boathire24_landing_urls.json").read_text())
LOCS = URLS["locations"]
BLOG = URLS["blog"]
BOATS = set(URLS["boats"])
HOME = "https://boathire24.com"
HOST = "https://boathire24.com/become-a-host"
YEAR = 2026

# Per-channel angle pools (keep the four channels reading differently).
ANGLES = {
    "telegraph": ["how to rent a boat in {loc}", "a first-timer's guide to boat rental in {loc}",
                  "what to know before chartering a boat in {loc}", "best time of year to rent a boat in {loc}"],
    "graph_org": ["renting a yacht in {loc}", "the best boats to charter in {loc}",
                  "a day on the water in {loc}", "boat rental costs in {loc}"],
    "livejournal": ["planning a boat day in {loc}", "boat rental in {loc}: a practical guide",
                    "family-friendly boating in {loc}", "what a charter in {loc} actually costs"],
    "rentry": ["boat rental tips for {loc}", "how to choose a boat to rent in {loc}",
               "a budget guide to renting a boat in {loc}", "things to do by boat in {loc}"],
}

# Anchor archetype pools (from the synthesised blueprint).
GEO = ["rent a boat in {loc}", "yacht charter in {loc}", "{loc} boat hire",
       "day charters in {loc}", "boat rental in {loc}", "skippered charters in {loc}"]
PARTIAL = ["rent a boat", "hire a boat", "book a charter online", "compare verified boat listings",
           "browse boats for your dates", "find a skippered charter", "book a boat online"]
EXACT = ["boat rental {loc}", "yacht charter {loc}", "boat hire {loc}"]   # max 1/article, primary only
BRANDED = ["BoatHire24", "on BoatHire24", "the BoatHire24 marketplace", "the BoatHire24 platform"]
NAKED = ["boathire24.com", "browse the listings", "see what is available", "check availability"]
PRODUCT = ["the {boat} listing", "this {btype}", "the {boat} charter page", "the {boat} for hire"]
OWNER = ["list your boat", "list a boat for free", "become a host", "rent out your boat"]

# Currency: default EUR (Mediterranean-heavy inventory); override by keyword.
_CUR = {
    "AED": ["dubai", "abu-dhabi", "abu dhabi", "sharjah", "ras-al", "uae", "ajman", "fujairah"],
    "USD": ["miami", "fort-lauderdale", "fort lauderdale", "new-york", "los-angeles", "san-diego",
            "san-francisco", "boston", "chicago", "tampa", "naples-florida", "key-west", "honolulu",
            "cancun", "cabo", "puerto-vallarta", "bahamas", "nassau", "tortola", "virgin-islands",
            "aruba", "curacao", "panama", "ecuador", "galapagos"],
    "GBP": ["london", "southampton", "brighton", "poole", "cowes", "portsmouth", "plymouth",
            "falmouth", "liverpool", "cardiff", "scotland", "edinburgh", "guernsey", "jersey"],
    "THB": ["phuket", "krabi", "koh-", "pattaya", "phang-nga", "samui"],
    "TRY": ["bodrum", "marmaris", "fethiye", "gocek", "antalya", "istanbul", "kas-"],
    "AUD": ["sydney", "melbourne", "brisbane", "gold-coast", "whitsundays", "perth", "cairns", "hamilton-island"],
    "SGD": ["singapore"],
    "HKD": ["hong-kong"],
    "ZAR": ["cape-town", "durban"],
    "MXN": [],
    "BRL": ["rio-de-janeiro", "florianopolis", "angra"],
    "EGP": ["hurghada", "sharm", "el-gouna", "cairo", "nile", "luxor", "aswan", "alexandria"],
    "INR": ["goa", "mumbai", "kochi"],
    "IDR": ["bali", "lombok", "komodo", "labuan-bajo", "gili"],
    "PHP": ["boracay", "palawan", "cebu", "el-nido", "coron"],
    "MYR": ["langkawi", "penang", "kota-kinabalu"],
    "MVR": ["maldives", "male"],
    "MUR": ["mauritius"],
    "SCR": ["seychelles", "mahe", "praslin"],
    "TZS": ["zanzibar", "dar-es-salaam"],
    "MAD": ["agadir", "tangier", "casablanca"],
    "QAR": ["doha", "qatar"],
    "OMR": ["muscat", "oman"],
    "BHD": ["bahrain", "manama"],
    "JPY": ["tokyo", "okinawa", "yokohama"],
    "CHF": ["zurich", "geneva", "lucerne", "thun", "lugano", "maggiore-ch", "interlaken", "brienz"],
    "CAD": ["toronto", "vancouver", "montreal", "muskoka", "okanagan", "halifax", "kelowna"],
}
# Inland/US lakes that the keyword map would otherwise default to EUR.
_CUR["USD"] += ["champlain", "tahoe", "powell", "michigan", "ozarks", "havasu", "george"]


# Words that describe a boat-rental landing page (not the place name). Used to
# split an SEO slug like 'luxury-yacht-charter-marbella-prices' into the real
# city ('Marbella') and the page theme ('luxury yacht charter prices').
SEO_WORDS = {
    "luxury", "luxurious", "affordable", "cheap", "budget", "best", "top", "premium",
    "exclusive", "private", "yacht", "yachts", "boat", "boats", "catamaran", "catamarans",
    "motor", "sailing", "sailboat", "speedboat", "speedboats", "jet", "ski", "jetski",
    "gulet", "superyacht", "megayacht", "fishing", "charter", "charters", "chartering",
    "hire", "hires", "rental", "rentals", "rent", "renting", "booking", "book",
    "prices", "price", "pricing", "cost", "costs", "deal", "deals", "offer", "offers",
    "day", "days", "daily", "hourly", "weekly", "half", "full", "overnight", "sunset",
    "morning", "evening", "for", "events", "event", "party", "parties", "wedding",
    "weddings", "birthday", "corporate", "family", "families", "with", "without",
    "skipper", "skippered", "skippers", "crewed", "crew", "bareboat", "self", "drive",
    "licence", "license", "near", "me", "in", "the", "and", "to", "of", "a", "your",
    "my", "tour", "tours", "trip", "trips", "cruise", "cruises", "guide", "tips",
    "services", "service", "company", "companies", "agency", "beginners", "first",
    "timers", "small", "large", "group", "groups", "couples", "kids", "children",
    "people", "person", "hire24", "rentals24",
    "list", "own", "owner", "owners", "host", "hosting", "earn", "income", "sell", "out",
    "hen", "stag", "bachelor", "bachelorette", "anniversary", "proposal", "celebration",
    # activity / experience descriptors that wrap a real city
    "dolphin", "dolphins", "watching", "swim", "swimming", "snorkel", "snorkelling",
    "snorkeling", "diving", "dive", "dinner", "lunch", "breakfast", "champagne", "bbq",
    "afternoon", "early", "late", "weekend", "midweek", "romantic", "scenic", "wildlife",
    "whale", "turtle", "swimwithdolphins", "experience", "experiences", "adventure",
    "click", "alternative", "do", "new", "years", "year", "eve", "nye", "season",
}
_OWNER_WORDS = {"list", "own", "owner", "owners", "host", "hosting", "earn", "income", "sell"}
_STOP = {"for", "in", "the", "and", "to", "of", "a", "me", "near", "with", "your", "my"}


def _known_city_tokens():
    """Tokens that appear in PLAIN location slugs (all-non-SEO) are real place names.
    Used to pull the city out of compound SEO/activity slugs robustly."""
    toks = set()
    for url in LOCS:
        slug = url.rstrip("/").split("/")[-1]
        parts = slug.split("-")
        if parts and all(p.lower() not in SEO_WORDS and not p.isdigit() for p in parts):
            for p in parts:
                if len(p) > 1:
                    toks.add(p.lower())
    return toks


_CITY_TOKENS = _known_city_tokens()


def _raw_name(url: str) -> str:
    return url.rstrip("/").split("/")[-1].replace("-", " ")


def _blog_topic(url: str) -> str:
    """A short, readable topic phrase (<=3 words) from a blog slug for anchor text."""
    return " ".join(_raw_name(url).split()[:3])


def _parse_slug(url: str):
    """Return (clean_city, page_theme) for a landing URL.
    'luxury-yacht-charter-marbella-prices' -> ('Marbella', 'luxury yacht charter prices').
    'dolphin-watching-afternoon-marbella'  -> ('Marbella', 'dolphin watching afternoon').
    A plain city slug -> ('Marbella', '')."""
    slug = url.rstrip("/").split("/")[-1]
    toks = [t for t in slug.split("-") if t]

    def _desc(t):
        return t.lower() in SEO_WORDS or t.isdigit()

    # Split into contiguous runs of NON-descriptor tokens (candidate place names).
    runs, cur = [], []
    for t in toks:
        if _desc(t):
            if cur:
                runs.append(cur); cur = []
        else:
            cur.append(t)
    if cur:
        runs.append(cur)
    # Prefer a run that contains a KNOWN real-city token (keeps multi-word cities
    # like 'puerto banus' intact); otherwise the longest run.
    known = [r for r in runs if any(x.lower() in _CITY_TOKENS for x in r)]
    pool = known or runs
    city_run = max(pool, key=len) if pool else []
    # Drop a trailing 2-letter country-code disambiguator (e.g. 'lake-maggiore-ch').
    _CC = {"ch", "de", "at", "it", "fr", "es", "pt", "hr", "gr", "us", "uk", "nl", "be"}
    if len(city_run) > 1 and city_run[-1].lower() in _CC:
        city_run = city_run[:-1]
    city = " ".join(city_run).title() if city_run else slug.replace("-", " ").title()
    theme_toks = [t for t in toks if t.lower() in SEO_WORDS and t.lower() not in _STOP]
    theme = " ".join(theme_toks)
    return city, theme


def _loc_name(url: str) -> str:
    return _parse_slug(url)[0]


def is_real_location(url: str) -> bool:
    """False for generic non-geo landing pages (e.g. /boat-rental, /jet-ski-rental)
    whose slug has no real place name. Such pages make poor 'article about <city>'
    targets, so the generator skips them as primaries (they can still be linked)."""
    city = _parse_slug(url)[0]
    words = [w for w in city.lower().split() if w]
    return bool(words) and not all(w in SEO_WORDS for w in words)


def _currency(loc_url: str) -> str:
    slug = loc_url.rstrip("/").split("/")[-1].lower()
    for cur, keys in _CUR.items():
        for k in keys:
            if k and k in slug:
                return cur
    return "EUR"


def _pick(seq, i):
    return seq[i % len(seq)] if seq else None


def _rotate(channel, idx):
    """Deterministic primary-location rotation (stable per channel, spread out)."""
    base = (abs(hash(channel)) % len(LOCS))
    primary = LOCS[(base + idx * 7) % len(LOCS)]
    sibling = LOCS[(base + idx * 7 + 173) % len(LOCS)]
    blog = _pick(BLOG, (base + idx * 11) % len(BLOG)) if BLOG else None
    return primary, sibling, blog


def _weighted_link_count(idx: int) -> int:
    # 25% -> 2, 50% -> 3, 25% -> 4  (deterministic, non-uniform)
    return {0: 2, 1: 3, 2: 3, 3: 4}[idx % 4]


def _primary_anchor(loc, idx, use_exact):
    if use_exact:
        return _pick(EXACT, idx).format(loc=loc), "exact"
    # alternate geo / partial
    if idx % 2 == 0:
        return _pick(GEO, idx // 2).format(loc=loc), "geo"
    return _pick(PARTIAL, idx // 2), "partial"


def plan_one(channel: str, idx: int) -> dict:
    primary_url, sibling_url, blog_url = _rotate(channel, idx)
    loc, theme = _parse_slug(primary_url)
    currency = _currency(primary_url)
    # If the landing page is an SEO page (has a theme), match the article topic to
    # it for stronger backlink relevance; otherwise use the channel's angle pool.
    owner_page = bool(theme) and any(w in theme.split() for w in _OWNER_WORDS)
    if theme:
        angle = f"{theme} in {loc}"
        title_hint = f"{theme.title()} in {loc}"
    else:
        angle = _pick(ANGLES[channel], idx).format(loc=loc)
        title_hint = f"Boat Rental in {loc}"
    link_count = _weighted_link_count(idx)

    # If the page theme names a boat type, prefer images (and a /boats link) of that
    # type so image + entity + backlink all align.
    prefer_type = None
    for t in ("catamaran", "speedboat", "sailing", "fishing", "luxury yacht", "motor yacht", "jet ski"):
        if t.split()[0] in (theme or "").lower():
            prefer_type = {"sailing": "sailing", "fishing": "fishing", "luxury": "luxury yacht",
                           "motor": "motor yacht", "jet": "jet ski"}.get(t.split()[0], t)
            break

    # Images: location-aware; 2 only on roughly half (longer) articles.
    n_imgs = 2 if idx % 2 == 0 else 1
    imgs = pick_images(loc, n=n_imgs, seed=idx + abs(hash(channel)) % 97, prefer_type=prefer_type)
    hero = imgs[0] if imgs else None
    boat_name = hero["boat"] if hero and hero.get("boat") else None
    boat_url = hero["boat_url"] if hero and hero.get("boat_url") in BOATS else None
    btype = "yacht"
    if hero and hero.get("caption"):
        for t in ("catamaran", "speedboat", "luxury yacht", "motor yacht", "sailing yacht", "jet ski", "yacht"):
            if t in hero["caption"].lower():
                btype = t
                break

    # Exact-match commercial anchor: only ~1 in 4 articles, only on primary.
    use_exact = (idx % 4 == 0)

    links = []
    # 1) PRIMARY deep page. Owner-acquisition landing pages get an owner anchor so the
    #    anchor matches the page intent (never a 'rent a boat' anchor on a 'list' page).
    if owner_page:
        pa = _pick([f"list your boat in {loc}", f"rent out your boat in {loc}",
                    f"become a host in {loc}", "list your boat"], idx)
        parch = "owner"
    else:
        pa, parch = _primary_anchor(loc, idx, use_exact)
    links.append({"role": "primary", "url": primary_url, "anchor": pa, "archetype": parch,
                  "place": "the orientation or cost section, deep inside a sentence"})

    # 2) SECONDARY deep page, relevance matched:
    #    prefer the hero image's boat page (image+entity+link alignment),
    #    else a blog page, else a sibling location.
    if boat_url and boat_name:
        sec_anchor = _pick(PRODUCT, idx).format(boat=boat_name, btype=btype)
        links.append({"role": "secondary", "url": boat_url, "anchor": sec_anchor, "archetype": "product",
                      "place": "the boat-choice section, in a sentence about that boat type"})
    elif blog_url:
        topic = _blog_topic(blog_url)
        sec_anchor = _pick(["a guide to {t}", "our {t} guide", "more on {t}", "tips on {t}"], idx).format(t=topic)
        links.append({"role": "secondary", "url": blog_url, "anchor": sec_anchor, "archetype": "topic",
                      "place": "the cost or season section, where the topic fits"})
    else:
        links.append({"role": "secondary", "url": sibling_url,
                      "anchor": _pick(GEO, idx + 1).format(loc=_loc_name(sibling_url)), "archetype": "geo",
                      "place": "a section comparing nearby cruising grounds"})

    # 3) HOME or OWNER (only if link_count >= 3), branded/naked or owner anchor.
    if link_count >= 3:
        owner = (idx % 7 in (0, 3))   # ~28% of articles use the owner CTA
        if owner:
            links.append({"role": "home", "url": HOST, "anchor": _pick(OWNER, idx), "archetype": "owner",
                          "place": "the closing paragraph, as the owner-side clause"})
        else:
            anc = _pick(BRANDED, idx) if idx % 2 == 0 else _pick(NAKED, idx)
            links.append({"role": "home", "url": HOME, "anchor": anc,
                          "archetype": "branded" if idx % 2 == 0 else "naked",
                          "place": "the closing paragraph"})

    # 4) Optional 4th link (only when link_count == 4): a CORE utility page
    #    (how-it-works / search / faq). These read naturally on any article
    #    regardless of city, diversify the target profile beyond money pages, and
    #    avoid the topical mismatch a random blog/sibling would create on, say, an
    #    inland city. Must be a DISTINCT URL from those already chosen.
    if link_count >= 4:
        used_urls = {l["url"] for l in links}
        CORE = [("https://boathire24.com/how-it-works", "how boat rental works", "resource"),
                ("https://boathire24.com/search", "the boat search", "resource"),
                ("https://boathire24.com/faq", "the booking FAQ", "resource")]
        for off in range(len(CORE)):
            url, anc, arch = CORE[(idx + off) % len(CORE)]
            if url not in used_urls:
                links.append({"role": "resource", "url": url, "anchor": anc, "archetype": arch,
                              "place": "a practical section about how booking works, a separate paragraph from other links"})
                break

    # De-dupe URLs (never two links to the same page); trim to link_count.
    seen, deduped = set(), []
    for l in links:
        if l["url"] in seen:
            continue
        seen.add(l["url"])
        deduped.append(l)
    deduped = deduped[:link_count]

    fig_html = [figure_html(im) for im in imgs]
    return {
        "channel": channel, "idx": idx, "angle": angle, "title_hint": title_hint,
        "location": loc, "theme": theme,
        "location_url": primary_url, "currency": currency, "year": YEAR,
        "link_count": len(deduped), "links": deduped,
        "images": imgs, "figure_html": fig_html,
        "boat_name": boat_name, "boat_type": btype,
        "topic_key": f"{angle}|{primary_url}",
    }


def plan(channel: str, count: int, start_index: int = 0):
    if channel not in ANGLES:
        sys.exit(f"unknown channel {channel}")
    return [plan_one(channel, start_index + i) for i in range(count)]


def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    channel = sys.argv[1]
    count = int(sys.argv[2])
    start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    print(json.dumps(plan(channel, count, start), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
