#!/usr/bin/env python3
"""Generate a Boat Rental in Marbella blog post — DeepSeek body + hero image +
linked boat cards — ready to inject into Blogger.

The article BODY is written by DeepSeek; we then prepend a hero image and append
illustrated cards that link to each featured boat's page on boatrentalinmarbella.com.
Output is ASCII-safe HTML (so it survives the clipboard) written to:
  /tmp/blog_today.html   (raw HTML)
  /tmp/blog_today.json   (JSON-encoded string, for JS injection)
and copied to the macOS clipboard via pbcopy.

Usage:
  python3 scripts/gen_blog_post.py                 # auto-pick today's topic (rotation)
  python3 scripts/gen_blog_post.py --topic "Sunset cruises" --boats astondoa-40,azimut-39
  python3 scripts/gen_blog_post.py --list          # show topic rotation + recent-used state
"""
from __future__ import annotations
import argparse, datetime, html, json, os, pathlib, subprocess, sys

ROOT  = pathlib.Path(__file__).resolve().parents[1]
BOATS = json.loads((ROOT / "config" / "boats.json").read_text())
BOATS_BY_SLUG = {b["slug"]: b for b in BOATS.get("boats", [])}
SITE  = "https://boatrentalinmarbella.com"
STATE = ROOT / "config" / "blog_topic_state.json"

# ── env (DEEPSEEK_API_KEY) ─────────────────────────────────────────────────────
def load_env():
    for p in [ROOT / ".env", pathlib.Path.home() / ".env"]:
        if p.exists():
            for ln in p.read_text().splitlines():
                ln = ln.strip()
                if ln and not ln.startswith("#") and "=" in ln:
                    k, _, v = ln.partition("=")
                    if k.strip() and k.strip() not in os.environ:
                        os.environ[k.strip()] = v.strip().strip('"').strip("'")
load_env()

# ── topic rotation: (title, angle, [boat slugs to feature]) ────────────────────
TOPICS = [
    ("Hen Party Boat Hire in Marbella", "planning the ultimate hen do on a private yacht from Puerto Banus", ["mangusta-80-white", "lagoon-380", "azimut-39"]),
    ("Dolphin Watching Cruises from Puerto Banus", "seeing wild dolphins on a morning cruise, best times and tips", ["astondoa-40", "azimut-39"]),
    ("Luxury Superyacht Charter Marbella", "chartering a crewed superyacht for a day", ["mangusta-80-white", "maiora-26m", "canados-86", "ferretti-94"]),
    ("Sunset Cruises in Marbella", "golden hour on the Mediterranean, romantic evenings", ["azimut-39", "astondoa-40", "fairline-targa-12m"]),
    ("Deep Sea Fishing Charters Marbella", "offshore fishing for bream, bass and tuna", ["red-tide-fishing-boat", "bandido"]),
    ("Catamaran Charter Marbella", "spacious, stable sailing for groups and families", ["lagoon-380"]),
    ("Boat Hire Without a Licence in Marbella", "self-drive boats you can legally hire with no licence", ["speedboat", "mariah-sx21"]),
    ("Sport Cruisers & Day Boats in Marbella", "fast, comfortable day boats for the perfect outing", ["astondoa-40", "azimut-39", "pershing-46", "fairline-targa-12m"]),
    ("Yacht Weddings & Proposals in Marbella", "ceremonies and proposals at sea", ["mangusta-80-white", "maiora-26m"]),
    ("Corporate Yacht Charter Marbella", "client entertaining and team days on the water", ["canados-86", "ferretti-94", "azimut-58"]),
    ("Family Boat Days in Marbella", "swimming, snorkelling and sunshine for all ages", ["lagoon-380", "astondoa-40"]),
    ("Speedboat Rental Marbella", "feeling the rush across the Costa del Sol", ["speedboat", "mariah-sx21"]),
    ("The Mangusta 80 Experience", "Marbella's flagship sport superyacht", ["mangusta-80-white", "mangusta-80-grey"]),
    ("Secret Coves Near Marbella by Boat", "quiet swim spots only reachable by sea", ["astondoa-40", "fairline-targa-12m", "lagoon-380"]),
    ("Best Month to Charter a Boat in Marbella", "season, sea temperatures and value", ["azimut-39", "astondoa-40"]),
    ("Big-Group Celebrations on the Water", "birthdays and parties for up to 12 guests", ["mangusta-80-white", "canados-86", "lagoon-380"]),
    ("Marbella Marina vs Puerto Banus Departures", "the two main departure points compared", ["azimut-39", "astondoa-40"]),
    ("A Photographer's Guide to Boat Photoshoots", "golden hour shoots with the La Concha backdrop", ["maiora-26m", "mangusta-80-white"]),
    ("Weekend Boat Hire in Marbella", "making the most of two days on the water", ["azimut-39", "lagoon-380", "pershing-46"]),
    ("Sailing the Costa del Sol", "slow, wind-powered exploration", ["lagoon-380", "dubhe"]),
]

# ── state (avoid repeating topics) ─────────────────────────────────────────────
def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"used": []}

def save_state(s):
    STATE.write_text(json.dumps(s, indent=2))

def pick_topic():
    s = load_state()
    cutoff = (datetime.date.today() - datetime.timedelta(days=18)).isoformat()
    recent = {u["title"] for u in s.get("used", []) if u["date"] >= cutoff}
    avail = [t for t in TOPICS if t[0] not in recent] or TOPICS
    # deterministic per-day choice without random (random is unavailable in some harnesses)
    idx = int(datetime.date.today().strftime("%Y%m%d")) % len(avail)
    return avail[idx]

def mark_used(title):
    s = load_state()
    s.setdefault("used", []).append({"title": title, "date": datetime.date.today().isoformat()})
    save_state(s)

# ── DeepSeek body generation ───────────────────────────────────────────────────
def deepseek_body(title, angle, boat_names):
    import requests
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY not set in .env")
    system = (
        "You are an SEO copywriter for Boat Rental in Marbella, a boat charter service in "
        "Marbella / Puerto Banus, Spain. British English; concrete, honest, no fabricated reviews. "
        "Every charter includes a licensed skipper, fuel, drinks, snacks and insurance. "
        "Output ONLY clean HTML body markup: an intro <p>, then 2-3 <h2> sections with <p>/<ul>, "
        "no <h1>, no <html>/<head>/<body>, no markdown fences, ~400-550 words. Do not output an "
        "image or a list of boats — those are added separately. End with a short call to action "
        f"to book at {SITE.replace('https://','')} or WhatsApp +358 400 406194.")
    user = (f"Write the blog post body.\nTITLE: {title}\nANGLE: {angle}\n"
            f"You may mention these boats by name where relevant: {', '.join(boat_names)}.\n"
            "Return HTML body only.")
    r = requests.post("https://api.deepseek.com/chat/completions",
        json={"model": "deepseek-chat",
              "messages": [{"role": "system", "content": system},
                           {"role": "user", "content": user}],
              "max_tokens": 1600, "temperature": 0.7},
        headers={"Authorization": f"Bearer {key}"}, timeout=120)
    r.raise_for_status()
    body = r.json()["choices"][0]["message"]["content"].strip()
    import re
    body = re.sub(r"^```(?:html)?\s*|\s*```$", "", body, flags=re.MULTILINE).strip()
    return body

# ── assemble full post HTML ────────────────────────────────────────────────────
def boat_card(slug):
    b = BOATS_BY_SLUG[slug]
    name = html.escape(b["name"]); url = f"{SITE}/boats/{slug}/"
    tag = html.escape(b.get("tagline") or b.get("summary", "")[:140])
    img = f"{SITE}/img/boats/{slug}/hero-600.jpg"
    return ('<div style="margin:18px 0;">'
            f'<a href="{url}"><img src="{img}" alt="{name} charter Marbella" '
            'style="max-width:100%;height:auto;border-radius:8px;" /></a>'
            f'<h3><a href="{url}">{name}</a></h3>'
            f'<p>{tag} <a href="{url}">See details &amp; pricing &rarr;</a></p></div>')

def assemble(title, body_html, boat_slugs):
    hero = boat_slugs[0]
    parts = [
        f'<p><img src="{SITE}/img/boats/{hero}/hero-1200.jpg" alt="{html.escape(title)} - Puerto Banus, Marbella" '
        'style="max-width:100%;height:auto;border-radius:8px;" /></p>',
        body_html,
        "<h2>Boats for this</h2>",
    ]
    parts += [boat_card(s) for s in boat_slugs if s in BOATS_BY_SLUG]
    parts.append(f'<p>See the <a href="{SITE}/boats/">full fleet of 18 boats</a> or book at '
                 f'<a href="{SITE}">boatrentalinmarbella.com</a> or WhatsApp +358 400 406194.</p>')
    body = "".join(parts)
    return body.encode("ascii", "xmlcharrefreplace").decode("ascii")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic")
    ap.add_argument("--title")
    ap.add_argument("--boats", help="comma-separated boat slugs")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    if a.list:
        s = load_state()
        print("Recent used:", [u["title"] for u in s.get("used", [])[-8:]])
        for t in TOPICS:
            print(" -", t[0], "->", ",".join(t[2]))
        return

    if a.topic or a.title:
        title = a.title or a.topic
        angle = a.topic or a.title
        slugs = [s.strip() for s in (a.boats or "").split(",") if s.strip()] or ["azimut-39"]
    else:
        title, angle, slugs = pick_topic()

    boat_names = [BOATS_BY_SLUG[s]["name"] for s in slugs if s in BOATS_BY_SLUG]
    print(f"Topic: {title}\nBoats: {', '.join(boat_names)}")
    body = deepseek_body(title, angle, boat_names)
    full = assemble(title, body, slugs)

    pathlib.Path("/tmp/blog_today.html").write_text(full)
    pathlib.Path("/tmp/blog_today.json").write_text(json.dumps(full))
    pathlib.Path("/tmp/blog_today_title.txt").write_text(title)
    try:
        subprocess.run(["pbcopy"], input=full.encode(), check=True)
        copied = "copied to clipboard"
    except Exception:
        copied = "clipboard copy failed"
    print(f"TITLE: {title}")
    print(f"ascii={full.isascii()} len={len(full)} imgs={full.count('<img')} boat-links={full.count('/boats/')} ({copied})")
    mark_used(title)

if __name__ == "__main__":
    main()
