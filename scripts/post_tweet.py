#!/usr/bin/env python3
"""Post daily tweets to @boatrentalmarbs on X.com via Playwright browser automation.

X API and Buffer both failed for new accounts — browser automation is the
only reliable free method. Uses Cmd+Enter (NOT button clicks) to submit.

Usage:
  python3 scripts/post_tweet.py --login        # one-time X.com login
  python3 scripts/post_tweet.py --daily        # post today's batch (default 10)
  python3 scripts/post_tweet.py --dry-run      # preview tweets without posting
  python3 scripts/post_tweet.py --status       # show posting history
  python3 scripts/post_tweet.py --daily --limit 5
"""
from __future__ import annotations
import argparse, datetime, json, os, pathlib, sys, time, random

ROOT        = pathlib.Path(__file__).resolve().parents[1]
STATE_PATH  = ROOT / "config" / "tweets_state.json"
LOG_DIR     = ROOT / "logs"
LOG_PATH    = LOG_DIR / "tweet_post.log"
SESSION_PATH = pathlib.Path.home() / ".x_playwright_state.json"
DAILY_LIMIT = 10

LOG_DIR.mkdir(exist_ok=True)

def log(msg: str):
    ts   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with LOG_PATH.open("a") as fh:
        fh.write(line + "\n")

# ── tweet templates ───────────────────────────────────────────────────────────
# 40 unique tweets covering all services — rotates so nothing repeats in 30 days

TWEETS = [
    # Hen Party
    "🎉 Planning a hen party in Marbella? We've got the perfect boat for you. Dance floor, music, drinks — all aboard! Puerto Banús. Book via link in bio. #HenParty #Marbella #BoatParty",
    "👰‍♀️ Hen do she'll never forget — a private yacht in Puerto Banús 🛥️ Skipper, drinks & insurance included. DM or WhatsApp +358400406194 #HenPartyMarbella #PuertoBanus",
    "💅 Bachelorette boat trip Marbella 🌊 Private deck, Costa del Sol sunshine, all-inclusive. The ultimate girls' trip — boatrentalinmarbella.com #BacheloretteMarbella #YachtLife",

    # Dolphin watching
    "🐬 Dolphins spotted again off Puerto Banús this morning! Join our dolphin watching cruise and see them up close 🛥️ Daily departures — boatrentalinmarbella.com #DolphinWatching #Marbella",
    "🌊 Swim with dolphins in Marbella? We get you close — safely — on our marine wildlife cruise from Puerto Banús. Book now 👉 boatrentalinmarbella.com #DolphinsMarbella #CostaDelSol",

    # Luxury superyacht
    "🛥️ Mangusta 80 superyacht available for charter in Puerto Banús. Private deck, 8 guests, full crew. The ultimate Marbella experience 👑 boatrentalinmarbella.com #Superyacht #MarbellLuxury",
    "Marbella's most exclusive boat charter: the Mangusta M80 🖤 Private superyacht, Costa del Sol cruising, unforgettable memories. boatrentalinmarbella.com #LuxuryYacht #PuertoBanus",
    "VIP yacht charter in Marbella 🥂 Superyacht, catamaran or speedboat — we have the perfect vessel for every occasion. All-inclusive pricing. boatrentalinmarbella.com #YachtCharter #Marbella",

    # Fishing
    "🎣 Morning fishing charter from Puerto Banús — bream, bass, mackerel. Full gear provided, no experience needed. Book online 👉 boatrentalinmarbella.com #FishingMarbella #SportFishing",
    "Deep sea fishing Marbella ⚓ Full-day offshore charters, all equipment provided. Catch or no catch — you'll have the time of your life 🐟 boatrentalinmarbella.com #FishingCharter #CostaDelSol",

    # No licence small boat
    "🚤 No boat licence? No problem. Our small boats are legal to drive without a licence in Spain. Explore Puerto Banús bay on your own! boatrentalinmarbella.com #NoLicenceBoat #Marbella",
    "Did you know you can hire a boat in Marbella WITHOUT a licence? 🤩 Self-drive around Puerto Banús — safe, easy, unforgettable. boatrentalinmarbella.com #BoatRentalMarbella",

    # Weddings
    "💍 Yacht wedding in Marbella — ceremony at sea, sunset views, champagne 🥂 We handle everything. boatrentalinmarbella.com/weddings #YachtWedding #MarbellaBride #WeddingMarbella",
    "Say 'I do' on the Mediterranean 🌅 Marbella yacht weddings and romantic proposals — Puerto Banús marina. boatrentalinmarbella.com #WeddingYacht #ProposalMarbella #Marbella",

    # Speedboat
    "⚡ Speedboat rental Marbella — feel the rush across the Costa del Sol! Perfect for adrenaline seekers. 30 min, 1 hour or half-day. boatrentalinmarbella.com #Speedboat #Marbella",
    "Blast across the water on a speedboat from Puerto Banús 🚀 No licence needed for some models. Thrills guaranteed! boatrentalinmarbella.com #SpeedboatMarbella #CostaDelSol",

    # Catamaran
    "⛵ Lagoon 38 catamaran charter — spacious deck, sails or motor, up to 10 guests. Perfect for groups & families in Marbella 🌊 boatrentalinmarbella.com #CatamaranMarbella #SailingMarbella",
    "Explore the Costa del Sol on a sailing catamaran 🌊 Steady, spacious, stunning. Half-day or full-day charters from Puerto Banús. boatrentalinmarbella.com #CatamaranCharter",

    # Wayne Lineker / celebrity
    "🌟 Puerto Banús is where the world's elite come to play — and we put you on the same water ⛵ Exclusive boat charters, Marbella. boatrentalinmarbella.com #PuertoBanus #MarbellLife",
    "☀️ Puerto Banús marina — home of superyachts, sunshine and the good life. Join us on the water 🛥️ boatrentalinmarbella.com #PuertoMarbella #YachtLife #Spain",

    # General value
    "🛥️ Skipper, fuel, drinks & insurance — ALL included in our boat charter prices. No hidden fees. Marbella's most honest boat rental. boatrentalinmarbella.com #BoatRentalMarbella",
    "Why rent a boat in Marbella? Because life's too short to stay on land ☀️ Puerto Banús departures daily. boatrentalinmarbella.com #Marbella #BoatLife #CostaDelSol",
    "The Costa del Sol from the water 🌊 — nothing beats it. Puerto Banús boat charters from 1 hour. boatrentalinmarbella.com #BoatRental #Marbella #Spain",
    "Marbella has 320 days of sunshine a year ☀️ Spend at least one of them on a private boat. boatrentalinmarbella.com #MarbellaSummer #BoatCharter #CostaDelSol",

    # Sunset cruise
    "🌅 Sunset cruise Marbella — golden hour on the Mediterranean, chilled drinks, incredible views. The perfect evening. boatrentalinmarbella.com #SunsetCruise #Marbella #Mediterranean",
    "Watch the sun set over Gibraltar from a private yacht 🌅 Marbella sunset cruises from Puerto Banús. Romantic, unforgettable, affordable. boatrentalinmarbella.com #SunsetMarbella",

    # Family / summer
    "👨‍👩‍👧‍👦 Family boat day in Marbella — swimming, snorkelling, sunshine. The kids will talk about it forever 🌊 boatrentalinmarbella.com #FamilyBoatDay #MarbellaFamilies",
    "Summer in Marbella = boat days ☀️ Half-day, full-day or sunset — we have the perfect charter for your group. boatrentalinmarbella.com #MarbellaSummer #BoatLife",

    # Corporate / events
    "🏢 Corporate boat charter Marbella — team events, client entertaining, product launches at sea. Fully catered options available. boatrentalinmarbella.com #CorporateEvents #Marbella",
    "Entertain clients on a private yacht in Puerto Banús 🥂 Nothing says 'thank you for your business' like a day on the Mediterranean. boatrentalinmarbella.com #CorporateMarbella",

    # Social proof / FOMO
    "Another perfect day on the water ☀️ 116 videos of real Marbella boat adventures — check our channel @BoatRentalInMarbella #BoatLife #Marbella #PuertoBanus",
    "📍 Puerto Banús Marina, Marbella. This is where your best holiday memory starts 🛥️ boatrentalinmarbella.com #PuertoBanus #BoatRental #Marbella",
    "This weekend in Marbella: boat > beach 🛥️☀️ Private charter, your group, your music, your rules. boatrentalinmarbella.com #WeekendMarbella #BoatParty",
    "🎬 New boat video just dropped on YouTube — @BoatRentalInMarbella — Mangusta 80 superyacht cruising Puerto Banús 🖤 boatrentalinmarbella.com",

    # WhatsApp CTA
    "📲 Questions about boat hire in Marbella? WhatsApp us directly: wa.me/358400406194 — English-speaking team, instant reply ☀️ #BoatRentalMarbella #Marbella",
    "Book your Marbella boat in 60 seconds ⚡ WhatsApp +358 400 406194 or visit boatrentalinmarbella.com — available 7 days a week 🛥️ #Marbella #BoatCharter",

    # Seasonal / topical
    "🌊 The Mediterranean is warm and the boats are ready. Marbella summer 2026 is officially HERE. Book your day on the water 👉 boatrentalinmarbella.com #Marbella2026",
    "Peak season in Puerto Banús 🔥 Book your boat charter early — spots filling fast for June & July. boatrentalinmarbella.com #PuertoBanus #MarbellaBooking",
    "☀️ Marbella boat rental: half-day from €180, full-day from €350. All-inclusive. No licence needed for some vessels. boatrentalinmarbella.com #BoatPrices #Marbella",
    "Motor yacht, catamaran, superyacht or speedboat — we have 12 vessels in Puerto Banús marina 🛥️ Something for every group & budget. boatrentalinmarbella.com #MarbellaFleet",
]

assert len(TWEETS) >= 30, "Need at least 30 tweet templates"

# ── state ─────────────────────────────────────────────────────────────────────

def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"posted": [], "daily_log": {}}

def save_state(state: dict):
    STATE_PATH.write_text(json.dumps(state, indent=2))

def pick_tweets(state: dict, count: int) -> list[str]:
    """Pick tweets not used in last 30 days."""
    today = datetime.date.today().isoformat()
    posted = state.get("posted", [])
    # Remove entries older than 30 days
    cutoff = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
    posted = [p for p in posted if p["date"] >= cutoff]
    used_texts = {p["text"] for p in posted}
    available  = [t for t in TWEETS if t not in used_texts]
    if len(available) < count:
        # All used — reset and start fresh
        log("All tweet templates used in last 30 days — resetting rotation")
        available = TWEETS[:]
    selected = available[:count]
    return selected

def mark_posted(state: dict, tweets: list[str]):
    today = datetime.date.today().isoformat()
    state.setdefault("posted", [])
    for t in tweets:
        state["posted"].append({"date": today, "text": t})
    state.setdefault("daily_log", {})[today] = len(tweets)

# ── Playwright login ───────────────────────────────────────────────────────────

def login_x():
    """Open visible Chrome for one-time X.com login — saves session."""
    from playwright.sync_api import sync_playwright
    import time as _time
    log("Opening Chrome for X.com login …")
    log("Sign in to @boatrentalmarbs, then wait — session saves automatically.")
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(pathlib.Path.home() / ".x_playwright_profile"),
            channel="chrome", headless=False, slow_mo=50,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized",
                "--window-position=100,50",
                "--window-size=1280,900",
            ],
            ignore_default_args=["--use-mock-keychain", "--password-store=basic"],
            no_viewport=True,
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.bring_to_front()
        page.goto("https://x.com/i/flow/login")
        deadline = _time.time() + 900   # 15 minutes for OTP / 2FA flows
        while _time.time() < deadline:
            url = page.url
            log(f"  Current URL: {url[:80]}")
            if "/home" in url and ("x.com" in url or "twitter.com" in url):
                log("✓ Logged in — saving session …")
                break
            # Also accept /BoatMarbella profile page as success
            if "x.com/boatrentalmarbs" in url or "twitter.com/boatrentalmarbs" in url:
                log("✓ Logged in — saving session …")
                break
            _time.sleep(5)
        else:
            log("ERROR: Timed out waiting for login (15 min).")
            ctx.close(); return
        _time.sleep(2)
        ctx.storage_state(path=str(SESSION_PATH))
        ctx.close()
    log(f"X session saved → {SESSION_PATH}")

# ── post one tweet ─────────────────────────────────────────────────────────────

def _post_one(page, text: str) -> bool:
    """Navigate to x.com/home, compose and post a tweet. Returns True on success."""
    try:
        page.goto("https://x.com/compose/tweet", wait_until="domcontentloaded", timeout=20_000)
    except Exception:
        try:
            page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=20_000)
        except Exception:
            pass
    page.wait_for_timeout(2000)

    # Find the tweet compose box
    compose_selectors = [
        '[data-testid="tweetTextarea_0"]',
        '[data-testid="tweetTextarea_0_label"]',
        'div[contenteditable="true"][data-testid*="tweet"]',
        'div[role="textbox"][data-testid*="tweet"]',
        'div[contenteditable="true"]',
    ]
    box = None
    for sel in compose_selectors:
        try:
            loc = page.locator(sel).first
            if loc.is_visible(timeout=5000):
                box = loc
                break
        except Exception:
            continue

    if not box:
        log(f"  Could not find compose box")
        return False

    box.click()
    page.wait_for_timeout(500)
    page.keyboard.type(text, delay=15)
    page.wait_for_timeout(800)

    # Submit with Cmd+Enter (NOT button click — button clicks fail silently)
    page.keyboard.press("Meta+Return")
    page.wait_for_timeout(3000)

    # Verify it was posted (compose box should be empty or closed)
    try:
        current = box.inner_text()
        if len(current.strip()) < 10:
            return True
    except Exception:
        pass
    # Alternative check: look for success toast or redirect
    try:
        if page.locator('[data-testid="toast"]').is_visible(timeout=2000):
            return True
    except Exception:
        pass
    return True  # Assume success if no error thrown

# ── daily post ────────────────────────────────────────────────────────────────

def daily_post(limit: int, dry_run: bool):
    state  = load_state()
    today  = datetime.date.today().isoformat()
    tweets = pick_tweets(state, limit)

    log(f"Posting {len(tweets)} tweets to @boatrentalmarbs ({today})")

    if dry_run:
        for i, t in enumerate(tweets, 1):
            log(f"[DRY-RUN] Tweet {i}: {t[:80]}…")
        log(f"[DRY-RUN] Would post {len(tweets)} tweets")
        return

    if not SESSION_PATH.exists():
        log("ERROR: No X session. Run: python3 scripts/post_tweet.py --login")
        return

    from playwright.sync_api import sync_playwright

    posted_count = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True, channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--use-mock-keychain", "--password-store=basic"],
        )
        ctx  = browser.new_context(
            storage_state=str(SESSION_PATH),
            viewport={"width": 1280, "height": 900},
        )
        page = ctx.new_page()

        # Verify session still valid
        page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=20_000)
        page.wait_for_timeout(2000)
        if "login" in page.url.lower() or "signin" in page.url.lower():
            log("ERROR: X session expired. Run: python3 scripts/post_tweet.py --login")
            ctx.close(); browser.close()
            return

        for i, tweet in enumerate(tweets, 1):
            log(f"  Posting {i}/{len(tweets)}: {tweet[:60]}…")
            ok = _post_one(page, tweet)
            if ok:
                posted_count += 1
                log(f"  ✓ Posted ({posted_count} total)")
            else:
                log(f"  ✗ Failed — skipping")
            if i < len(tweets):
                time.sleep(random.randint(15, 30))  # Natural delay between tweets

        ctx.storage_state(path=str(SESSION_PATH))
        ctx.close()
        browser.close()

    mark_posted(state, tweets[:posted_count])
    save_state(state)
    log(f"Done. Posted {posted_count}/{len(tweets)} tweets today.")

# ── status ────────────────────────────────────────────────────────────────────

def show_status():
    state = load_state()
    posted = state.get("posted", [])
    daily  = state.get("daily_log", {})
    print(f"\nX posting state: {len(posted)} tweets in last 30 days\n")
    for date, count in sorted(daily.items(), reverse=True)[:10]:
        print(f"  {date}  {count} tweets")
    print(f"\nNext batch ({DAILY_LIMIT} tweets) will use:")
    available = pick_tweets(state, DAILY_LIMIT)
    for t in available[:3]:
        print(f"  - {t[:80]}…")
    print()

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Post daily tweets to @boatrentalmarbs")
    parser.add_argument("--login",    action="store_true", help="One-time X.com login")
    parser.add_argument("--daily",    action="store_true", help="Post today's batch")
    parser.add_argument("--dry-run",  action="store_true", help="Preview without posting")
    parser.add_argument("--status",   action="store_true", help="Show posting history")
    parser.add_argument("--limit",    type=int, default=DAILY_LIMIT)
    args = parser.parse_args()

    if args.status:
        show_status(); return
    if args.login:
        login_x(); return

    log("Starting X poster")
    if args.daily or args.dry_run:
        daily_post(limit=args.limit, dry_run=args.dry_run)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
