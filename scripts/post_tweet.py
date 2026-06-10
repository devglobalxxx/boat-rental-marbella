#!/usr/bin/env python3
"""Post daily tweets with Drive media to X accounts via Playwright.

Supports @BoatRentalMarbs and @BoatHire24.
Each tweet gets a real boat photo from Google Drive attached.
Uses Cmd+Enter (NOT button clicks) to submit — button clicks fail silently.

Usage:
  python3 scripts/post_tweet.py --account boatrentalmarbs --login
  python3 scripts/post_tweet.py --account boatrentalmarbs --daily
  python3 scripts/post_tweet.py --account boatrentalmarbs --daily --limit 5
  python3 scripts/post_tweet.py --account boatrentalmarbs --dry-run
  python3 scripts/post_tweet.py --account boatrentalmarbs --status
  (replace boatrentalmarbs with boathire24 for the second account)
"""
from __future__ import annotations
import argparse, datetime, io, json, os, pathlib, random, sys, time

ROOT    = pathlib.Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"
TMP_DIR = ROOT / "tmp-social"
LOG_DIR.mkdir(exist_ok=True)
TMP_DIR.mkdir(exist_ok=True)

# ── Google Drive config ───────────────────────────────────────────────────────
DRIVE_FOLDER_ID = "1qEQPlq6084s7eaq2wqTtoTjN5t2yvFlS"
TOKEN_PATH      = pathlib.Path.home() / ".social_post_token_v2.json"
GOOGLE_SCOPES   = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/blogger",
]
MEDIA_MAX_BYTES = 5 * 1024 * 1024  # 5 MB — X image limit
_MIME_EXT = {
    "image/jpeg": ".jpg", "image/jpg": ".jpg",
    "image/png": ".png",  "image/webp": ".webp",
}

# ── per-account config ────────────────────────────────────────────────────────
ACCOUNTS = {
    "boatrentalmarbs": {
        "handle":       "@BoatRentalMarbs",
        "session_path": pathlib.Path.home() / ".x_boatrentalmarbs_session.json",
        "state_path":   ROOT / "config" / "tweets_state_boatrentalmarbs.json",
        "log_path":     LOG_DIR / "tweet_post_boatrentalmarbs.log",
        "profile_dir":  pathlib.Path.home() / ".x_boatrentalmarbs_profile",
        "login_url_check": "boatrentalmarbs",
    },
    "boathire24": {
        "handle":       "@BoatHire24",
        "session_path": pathlib.Path.home() / ".x_boathire24_session.json",
        "state_path":   ROOT / "config" / "tweets_state_boathire24.json",
        "log_path":     LOG_DIR / "tweet_post_boathire24.log",
        "profile_dir":  pathlib.Path.home() / ".x_boathire24_profile",
        "login_url_check": "boathire24",
    },
}

# ── tweet templates ───────────────────────────────────────────────────────────

_WA   = "wa.me/358400406194"
_SITE = "boatrentalinmarbella.com"
_BH   = "boathire24.com"

TWEETS_BOATRENTALMARBS = [
    f"🎉 Planning a hen party in Marbella? Private yacht, Puerto Banús, drinks all day. Book via link in bio. #HenParty #Marbella #BoatParty",
    f"👰 Hen do she'll never forget — private yacht, Puerto Banús 🛥️ Skipper, drinks & insurance included. DM or WhatsApp +358400406194 #HenPartyMarbella",
    f"💅 Bachelorette boat trip Marbella 🌊 Private deck, Costa del Sol sunshine, all-inclusive. The ultimate girls' trip — {_SITE} #BacheloretteMarbella",
    f"🐬 Dolphins spotted off Puerto Banús this morning! Join our dolphin watching cruise — daily departures. {_SITE} #DolphinWatching #Marbella",
    f"🌊 Swim with dolphins in Marbella? We get you close — safely. Marine wildlife cruise from Puerto Banús. {_SITE} #DolphinsMarbella",
    f"🛥️ Mangusta 80 superyacht — 24m of Italian power, full crew, from €4,719/4hrs. Puerto Banús. {_SITE} #Superyacht #Marbella",
    f"Marbella's most exclusive boat: the Mangusta 80 🖤 Private superyacht, Costa del Sol cruising. {_SITE} #LuxuryYacht #PuertoBanus",
    f"VIP yacht charter in Marbella 🥂 Superyacht, catamaran or speedboat — all-inclusive pricing. {_SITE} #YachtCharter #Marbella",
    f"🎣 Morning fishing from Puerto Banús — bream, bass, mackerel. Full gear provided. {_SITE} #FishingMarbella #SportFishing",
    f"Deep sea fishing Marbella ⚓ Full-day offshore charters, all equipment provided. {_SITE} #FishingCharter #CostaDelSol",
    f"🚤 No boat licence? No problem. Self-drive boats legal without a licence in Spain. Explore Puerto Banús bay! {_SITE} #NoLicenceBoat",
    f"Did you know you can hire a boat in Marbella WITHOUT a licence? 🤩 Self-drive around Puerto Banús. {_SITE} #BoatRentalMarbella",
    f"💍 Yacht wedding in Marbella — ceremony at sea, sunset views, champagne 🥂 {_SITE} #YachtWedding #WeddingMarbella",
    f"Say 'I do' on the Mediterranean 🌅 Marbella yacht weddings and romantic proposals at Puerto Banús. {_SITE} #ProposalMarbella",
    f"⚡ Speedboat rental Marbella — feel the rush across the Costa del Sol! 30 min to half-day. {_SITE} #Speedboat #Marbella",
    f"Blast across the water on a speedboat from Puerto Banús 🚀 No licence needed for some models. {_SITE} #SpeedboatMarbella",
    f"⛵ Lagoon 38 catamaran — spacious deck, up to 10 guests. Perfect for groups & families. {_SITE} #CatamaranMarbella",
    f"Explore the Costa del Sol on a catamaran 🌊 Steady, spacious, stunning. Half or full-day charters. {_SITE} #CatamaranCharter",
    f"🌟 Puerto Banús — where the world's elite come to play. Join us on the water. {_SITE} #PuertoBanus #YachtLife",
    f"🛥️ Skipper, fuel, drinks & insurance — ALL included. No hidden fees. Marbella's most honest boat rental. {_SITE}",
    f"Why rent a boat in Marbella? Because life's too short to stay on land ☀️ Puerto Banús departures daily. {_SITE}",
    f"The Costa del Sol from the water 🌊 — nothing beats it. Boat charters from 1 hour. {_SITE} #Marbella",
    f"Marbella has 320 days of sunshine a year ☀️ Spend at least one on a private boat. {_SITE} #MarbellaSummer",
    f"🌅 Sunset cruise Marbella — golden hour on the Mediterranean, chilled drinks, incredible views. {_SITE} #SunsetCruise",
    f"Watch the sun set over Gibraltar from a private yacht 🌅 Romantic, unforgettable, affordable. {_SITE} #SunsetMarbella",
    f"👨‍👩‍👧‍👦 Family boat day — swimming, snorkelling, sunshine. The kids will talk about it forever 🌊 {_SITE} #FamilyBoatDay",
    f"Summer in Marbella = boat days ☀️ Half-day, full-day or sunset charters. {_SITE} #MarbellaSummer #BoatLife",
    f"🏢 Corporate boat charter — team events, client entertaining, product launches at sea. {_SITE} #CorporateEvents",
    f"Entertain clients on a private yacht 🥂 Nothing says 'thank you' like a day on the Mediterranean. {_SITE}",
    f"📍 Puerto Banús Marina, Marbella. This is where your best holiday memory starts 🛥️ {_SITE} #PuertoBanus",
    f"This weekend in Marbella: boat > beach 🛥️☀️ Private charter, your group, your music, your rules. {_SITE}",
    f"📲 Book your Marbella boat in 60 seconds ⚡ WhatsApp: {_WA} — available 7 days. #Marbella #BoatCharter",
    f"🌊 The Mediterranean is warm and the boats are ready. Marbella summer 2026. Book: {_SITE} #Marbella2026",
    f"Peak season in Puerto Banús 🔥 Spots filling fast for June & July. Book early: {_SITE} #PuertoBanus",
    f"Motor yacht, catamaran, superyacht or speedboat — 12 vessels in Puerto Banús 🛥️ {_SITE} #MarbellaFleet",
    f"🥂 Hen party goals: private yacht, champagne on deck, dolphin sighting. We deliver all four. {_SITE} #HenParty",
    f"🎂 Birthday on a yacht = the birthday they'll never forget. Private charter, your music. {_SITE} #BirthdayYacht",
    f"💑 Anniversary dinner on the water — private chef, champagne, sunset. {_SITE} #RomanticYacht #Marbella",
    f"🏆 Team-building in Marbella? Private yacht with catering & water sports beats any conference room. {_SITE}",
    f"☀️ Marbella boat rental from €180 half-day, €350 full-day. All-inclusive. {_SITE} #BoatPrices #Marbella",
]

TWEETS_BOATHIRE24 = [
    f"🛥️ Boat hire Marbella — the best way to spend a day on the Costa del Sol. All-inclusive packages. {_BH} #BoatHire #Marbella",
    f"⚓ Charter a private yacht in Puerto Banús 🌊 Skipper, fuel & drinks included. No hidden costs. {_BH} #YachtHire #Marbella",
    f"🐬 Dolphin watching cruise from Marbella — see wild dolphins on a private boat. Daily departures. {_BH} #DolphinWatching",
    f"🌅 Sunset yacht hire Marbella — golden hour on the Med, champagne, incredible views. Book now. {_BH} #SunsetCruise #Marbella",
    f"🎉 Hen party boat hire Marbella 👰 Private deck, music, drinks, Costa del Sol sunshine. {_BH} #HenParty #BoatHire",
    f"💍 Planning a proposal? Hire a private yacht at sunset in Marbella — we'll make it perfect. {_BH} #Proposal #Marbella",
    f"🎣 Fishing boat hire Puerto Banús — bream, bass, tuna in season. All tackle provided. {_BH} #FishingCharter #CostaDelSol",
    f"⛵ Catamaran hire Marbella — stable, spacious, stunning. Perfect for groups up to 10. {_BH} #CatamaranHire #Sailing",
    f"🚤 Small boat hire without a licence — explore Puerto Banús bay yourself! From 1 hour. {_BH} #NoLicenceBoat",
    f"🛥️ Mangusta 80 superyacht hire — 24 metres of luxury, full crew, Puerto Banús. {_BH} #SuperyachtHire #LuxuryYacht",
    f"Speedboat hire Marbella ⚡ Feel the rush across the Costa del Sol. 30 min to half-day options. {_BH} #SpeedboatHire",
    f"💼 Corporate boat hire Marbella — team events, client days, launches at sea. Fully catered. {_BH} #CorporateBoat",
    f"👨‍👩‍👧‍👦 Family boat hire Marbella — swimming, snorkelling, sunshine. Kids love it. {_BH} #FamilyBoatHire #CostaDelSol",
    f"💒 Yacht wedding Marbella — hire a private boat for your ceremony at sea 🥂 {_BH} #YachtWedding #WeddingMarbella",
    f"🌊 The Costa del Sol from the water — nothing beats it. Boat hire from 1 hour. {_BH} #BoatHireMarbella",
    f"☀️ 320 sunny days a year in Marbella. Hire a boat for at least one of them. {_BH} #Marbella #SummerBoat",
    f"📍 Puerto Banús marina — where your perfect boat day begins 🛥️ Book: {_BH} #PuertoBanus #BoatHire24",
    f"🥂 Private yacht hire for birthdays, anniversaries, proposals — we handle everything. {_BH} #PrivateYacht #Marbella",
    f"All-inclusive boat hire in Marbella 🛥️ Skipper, fuel, drinks & snacks — one price, no surprises. {_BH}",
    f"🐬 Morning dolphin cruise Marbella — best wildlife sighting rate on the Costa del Sol. {_BH} #Dolphins #BoatHire",
    f"Half-day boat hire from €180 · Full-day from €350 · Superyacht from €4,719 🛥️ {_BH} #BoatHirePrices #Marbella",
    f"⛵ Lagoon 38 catamaran — the steadiest, most spacious boat hire on the Costa del Sol. {_BH} #Catamaran #Marbella",
    f"🎊 Stag do, hen party, birthday, anniversary — hire a private yacht and do it properly. {_BH} #BoatHireMarbella",
    f"🌟 Puerto Banús is where superyachts come to play — hire one for the day. {_BH} #PuertoBanus #LuxuryBoat",
    f"🏖️ Secret coves only reachable by boat — your private beach for the day off Marbella. {_BH} #SecretBeach #BoatHire",
    f"🌅 Watch the sun set over Gibraltar from a hired yacht 🛥️ Marbella's best evening experience. {_BH} #SunsetMarbella",
    f"Corporate yacht day Marbella 🥂 Entertain clients on the Mediterranean — nothing comes close. {_BH} #CorporateEvent",
    f"Peak summer 2026 🔥 Boat hire spots in Puerto Banús filling fast. Book early: {_BH} #Marbella #SummerBooking",
    f"🚢 Full crew, drinks, fuel, insurance — all included in every BoatHire24 package. No hidden extras. {_BH}",
    f"📲 Book your Marbella boat hire in minutes — WhatsApp {_WA} or visit {_BH} ☀️ #BoatHire24 #Marbella",
    f"🎣 Deep sea fishing hire — tuna, swordfish, big game off the Costa del Sol. {_BH} #DeepSeaFishing #Marbella",
    f"Motor yacht, catamaran, superyacht or speedboat — the full fleet is at {_BH} 🛥️ #MarbellaFleet",
    f"🌊 Morning swim stop, afternoon dolphins, evening sunset — one full-day boat hire. {_BH} #MarbellaBoatDay",
    f"Summer in Marbella = boat days ☀️ Half or full-day hire from Puerto Banús. {_BH} #SummerMarbella #BoatLife",
    f"🏆 Team-building on a yacht beats any conference room. Private catered charter from Puerto Banús. {_BH}",
    f"Own a boat in Marbella? List it on BoatHire24 and earn while you're not using it. {_BH} #BoatOwner #PassiveIncome",
    f"🛥️ Boat owners — turn your vessel into revenue. Easy listing, vetted charterers, full insurance. {_BH} #ListYourBoat",
    f"Got a boat sitting in Puerto Banús? It could be earning €500–€2,000/day. List on {_BH} #BoatRental #BoatOwner",
    f"BoatHire24 connects private boat owners with quality charterers across the Costa del Sol. {_BH} #BoatHire24",
    f"No licence? No problem 🤩 Self-drive boat hire in Marbella — safe, easy, legal. From 1 hour. {_BH} #NoLicence",
]

assert len(TWEETS_BOATRENTALMARBS) >= 30, "Need ≥30 templates for boatrentalmarbs"
assert len(TWEETS_BOATHIRE24)      >= 30, "Need ≥30 templates for boathire24"

ACCOUNT_TWEETS = {
    "boatrentalmarbs": TWEETS_BOATRENTALMARBS,
    "boathire24":      TWEETS_BOATHIRE24,
}

# ── logging ───────────────────────────────────────────────────────────────────

_current_log: pathlib.Path | None = None

def set_log(path: pathlib.Path):
    global _current_log
    _current_log = path

def log(msg: str):
    ts   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    if _current_log:
        with _current_log.open("a") as fh:
            fh.write(line + "\n")

# ── env ───────────────────────────────────────────────────────────────────────

def load_env():
    for p in [ROOT / ".env", pathlib.Path.home() / ".env"]:
        if p.exists():
            for line in p.read_text().splitlines():
                if "=" in line and not line.startswith("#"):
                    k, _, v = line.partition("=")
                    k = k.strip()
                    if k and k not in os.environ:
                        os.environ[k] = v.strip().strip('"').strip("'")

load_env()

# ── tweet state ───────────────────────────────────────────────────────────────

def load_state(state_path: pathlib.Path) -> dict:
    if state_path.exists():
        return json.loads(state_path.read_text())
    return {"posted": [], "daily_log": {}}

def save_state(state: dict, state_path: pathlib.Path):
    state_path.write_text(json.dumps(state, indent=2))

def pick_tweets(state: dict, templates: list[str], count: int) -> list[str]:
    """Pick tweets not used in last 30 days, in order."""
    cutoff    = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
    posted    = [p for p in state.get("posted", []) if p["date"] >= cutoff]
    used      = {p["text"] for p in posted}
    available = [t for t in templates if t not in used]
    if len(available) < count:
        log("All templates used in 30 days — resetting rotation")
        available = templates[:]
    return available[:count]

def mark_posted(state: dict, tweets: list[str]):
    today = datetime.date.today().isoformat()
    state.setdefault("posted", [])
    for t in tweets:
        state["posted"].append({"date": today, "text": t})
    state.setdefault("daily_log", {})[today] = len(tweets)

# ── Google Drive media ────────────────────────────────────────────────────────

def _get_drive():
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        if not TOKEN_PATH.exists():
            log("Drive: no token — skipping media")
            return None
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), GOOGLE_SCOPES)
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                log("Drive: credentials invalid — skipping media")
                return None
        return build("drive", "v3", credentials=creds, cache_discovery=False)
    except Exception as e:
        log(f"Drive init error: {e}")
        return None

def _list_images(drive, folder_id: str, depth: int = 0) -> list[dict]:
    results, page_token = [], None
    while True:
        resp = drive.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="nextPageToken, files(id, name, mimeType, size)",
            pageSize=200, pageToken=page_token,
        ).execute()
        for f in resp.get("files", []):
            mime = f.get("mimeType", "")
            if mime in _MIME_EXT and int(f.get("size", 0)) <= MEDIA_MAX_BYTES:
                results.append(f)
            elif mime == "application/vnd.google-apps.folder" and depth < 2:
                results.extend(_list_images(drive, f["id"], depth + 1))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return results

def fetch_media_pool(count: int, seed_suffix: str = "") -> list[pathlib.Path]:
    """Download `count` unique Drive images. Returns local paths (may be < count)."""
    drive = _get_drive()
    if not drive:
        return []
    try:
        log("Drive: listing images…")
        imgs = _list_images(drive, DRIVE_FOLDER_ID)
        if not imgs:
            log("Drive: no images found")
            return []
        log(f"Drive: {len(imgs)} eligible images")

        rng = random.Random(datetime.date.today().isoformat() + seed_suffix)
        rng.shuffle(imgs)
        chosen = imgs[:count]

        paths: list[pathlib.Path] = []
        for img in chosen:
            ext  = _MIME_EXT[img["mimeType"]]
            dest = TMP_DIR / f"tweet_{img['id']}{ext}"
            if dest.exists():
                paths.append(dest); continue
            size = int(img.get("size", 0))
            log(f"  Downloading {img['name']} ({size // 1024} KB)…")
            try:
                from googleapiclient.http import MediaIoBaseDownload
                req = drive.files().get_media(fileId=img["id"])
                buf = io.BytesIO()
                dl = MediaIoBaseDownload(buf, req, chunksize=4 * 1024 * 1024)
                done = False
                while not done:
                    _, done = dl.next_chunk()
                dest.write_bytes(buf.getvalue())
                paths.append(dest)
            except Exception as e:
                log(f"  Download error ({img['id']}): {e}")

        log(f"Drive: {len(paths)}/{count} images ready")
        return paths
    except Exception as e:
        log(f"Drive pool error: {e}")
        return []

# ── Playwright login ───────────────────────────────────────────────────────────

def login_x(account: str):
    cfg = ACCOUNTS[account]
    from playwright.sync_api import sync_playwright

    log(f"Opening Chrome for {cfg['handle']} login…")
    log("Sign in, then wait — session saves automatically.")
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(cfg["profile_dir"]),
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
        deadline = time.time() + 900   # 15 min for 2FA
        while time.time() < deadline:
            url = page.url
            log(f"  URL: {url[:80]}")
            check = cfg["login_url_check"].lower()
            if "/home" in url or check in url.lower():
                log("✓ Logged in — saving session…")
                break
            time.sleep(5)
        else:
            log("ERROR: Timed out waiting for login (15 min).")
            ctx.close(); return
        time.sleep(2)
        ctx.storage_state(path=str(cfg["session_path"]))
        ctx.close()
    log(f"Session saved → {cfg['session_path']}")

# ── post one tweet ─────────────────────────────────────────────────────────────

_COMPOSE_SELECTORS = [
    '[data-testid="tweetTextarea_0"]',
    'div[contenteditable="true"][data-testid*="tweet"]',
    'div[role="textbox"][data-testid*="tweet"]',
    'div[contenteditable="true"]',
]

def _attach_media(page, media_path: pathlib.Path) -> bool:
    """Set a local file on X's hidden file input. Returns True if attached."""
    try:
        # Use the primaryColumn-scoped input to avoid strict-mode violations
        # (X renders a second fileInput outside the compose column)
        inp = page.locator('[data-testid="primaryColumn"] input[data-testid="fileInput"]')
        if inp.count() == 0:
            inp = page.locator('input[data-testid="fileInput"]').first
        if inp.count() == 0:
            inp = page.locator('input[type="file"]').first
        inp.set_input_files(str(media_path))
        page.wait_for_timeout(4000)   # wait for upload progress
        log(f"  📎 {media_path.name}")
        return True
    except Exception as e:
        log(f"  Media attach failed: {e}")
        return False

def _post_one(page, text: str, media_path: pathlib.Path | None = None) -> bool:
    try:
        try:
            page.goto("https://x.com/compose/tweet",
                      wait_until="domcontentloaded", timeout=20_000)
        except Exception:
            try:
                page.goto("https://x.com/home",
                          wait_until="domcontentloaded", timeout=20_000)
            except Exception:
                pass
        page.wait_for_timeout(2000)

        # Attach media before typing (upload runs while we type)
        if media_path and media_path.exists():
            _attach_media(page, media_path)

        # Find compose box
        box = None
        for sel in _COMPOSE_SELECTORS:
            try:
                loc = page.locator(sel).first
                if loc.is_visible(timeout=5000):
                    box = loc; break
            except Exception:
                continue
        if not box:
            log("  Could not find compose box")
            return False

        box.click()
        page.wait_for_timeout(500)
        page.keyboard.type(text, delay=15)
        page.wait_for_timeout(800)

        # Extra wait if media is still uploading
        if media_path:
            page.wait_for_timeout(2000)

        # Submit with Cmd+Enter — button click fires no network request
        # Playwright uses "Enter" not "Return" for the Enter key
        page.keyboard.press("Meta+Enter")
        page.wait_for_timeout(3500)

        # Fallback: click button if compose still open
        if "compose" in page.url:
            btn = page.locator('[data-testid="tweetButton"]')
            if btn.count() > 0:
                btn.click()
                page.wait_for_timeout(3000)

        return True
    except Exception as e:
        log(f"  ERROR: {e}")
        return False

# ── daily post ────────────────────────────────────────────────────────────────

def daily_post(account: str, limit: int, dry_run: bool):
    cfg       = ACCOUNTS[account]
    templates = ACCOUNT_TWEETS[account]
    state     = load_state(cfg["state_path"])
    today     = datetime.date.today().isoformat()
    tweets    = pick_tweets(state, templates, limit)

    log(f"Posting {len(tweets)} tweets to {cfg['handle']} ({today})")

    if dry_run:
        for i, t in enumerate(tweets, 1):
            log(f"[DRY-RUN] {i}: {t[:90]}…")
        log(f"[DRY-RUN] Would post {len(tweets)} tweets + Drive media")
        return

    if not cfg["session_path"].exists():
        log(f"ERROR: No X session for {account}.")
        log(f"Run: python3 scripts/post_tweet.py --account {account} --login")
        return

    # Download one Drive image per tweet upfront
    media_pool = fetch_media_pool(len(tweets), seed_suffix=account)
    if not media_pool:
        log("No Drive media available — posting text-only")

    from playwright.sync_api import sync_playwright

    posted_ok = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True, channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--use-mock-keychain", "--password-store=basic"],
        )
        ctx  = browser.new_context(
            storage_state=str(cfg["session_path"]),
            viewport={"width": 1280, "height": 900},
        )
        page = ctx.new_page()

        # Verify session valid
        page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=20_000)
        page.wait_for_timeout(2000)
        if "login" in page.url.lower() or "signin" in page.url.lower():
            log(f"ERROR: Session expired for {account}.")
            log(f"Run: python3 scripts/post_tweet.py --account {account} --login")
            ctx.close(); browser.close()
            return

        for i, tweet in enumerate(tweets, 1):
            media = media_pool[i - 1] if (i - 1) < len(media_pool) else None
            label = f"with {media.name}" if media else "text-only"
            log(f"  {i}/{len(tweets)} [{label}]: {tweet[:55]}…")
            if _post_one(page, tweet, media_path=media):
                posted_ok += 1
                log(f"  ✓ ({posted_ok} posted)")
            else:
                log("  ✗ Failed")
            if i < len(tweets):
                time.sleep(random.randint(15, 30))

        ctx.storage_state(path=str(cfg["session_path"]))
        ctx.close()
        browser.close()

    # Clean up temp media files
    for mp in media_pool:
        try: mp.unlink()
        except Exception: pass

    mark_posted(state, tweets[:posted_ok])
    save_state(state, cfg["state_path"])
    log(f"Done — {posted_ok}/{len(tweets)} tweets posted to {cfg['handle']}.")

# ── status ────────────────────────────────────────────────────────────────────

def show_status(account: str):
    cfg   = ACCOUNTS[account]
    state = load_state(cfg["state_path"])
    daily = state.get("daily_log", {})
    print(f"\n{cfg['handle']} — posting history:")
    if daily:
        for date, count in sorted(daily.items(), reverse=True)[:10]:
            print(f"  {date}: {count} tweets")
    else:
        print("  No posts yet.")
    session_ok = cfg["session_path"].exists()
    print(f"  Session: {'✓ exists' if session_ok else '✗ missing — run --login'}")
    print()

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Post daily tweets with Drive media to X accounts"
    )
    parser.add_argument(
        "--account", choices=list(ACCOUNTS), required=True,
        help="Which account to post to"
    )
    parser.add_argument("--login",   action="store_true", help="One-time X.com login")
    parser.add_argument("--daily",   action="store_true", help="Post today's batch")
    parser.add_argument("--dry-run", action="store_true", help="Preview without posting")
    parser.add_argument("--status",  action="store_true", help="Show posting history")
    parser.add_argument("--limit",   type=int, default=10, help="Max tweets (default 10)")
    args = parser.parse_args()

    cfg = ACCOUNTS[args.account]
    set_log(cfg["log_path"])

    if args.status:
        show_status(args.account); return
    if args.login:
        login_x(args.account); return

    log(f"Starting X poster — {cfg['handle']}")
    if args.daily or args.dry_run:
        daily_post(account=args.account, limit=args.limit, dry_run=args.dry_run)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
