#!/usr/bin/env python3
"""High-volume unique-content link drops to free publishing platforms.

Platforms (adapters):
  - telegraph   → api.telegra.ph (pages also live on graph.org). Anonymous, rotates accounts.
  - rentry      → rentry.co anonymous CSRF API (markdown).
  (justpaste.it removed — only graph.org + rentry.co.)

Each post:
  - UNIQUE topic from a large combinatorial space (subject × angle × modifier), LLM-written fresh.
  - 350-650 words (short-form, natural for these hosts).
  - 2-4 contextual backlinks with VARIED anchors, spread across ALL 282 site pages
    (pulled live from sitemap.xml) — not just the homepage.
  - deduped vs a per-platform ledger.

Backend: DeepSeek primary ($0-ish, works under launchd), claude CLI fallback.

Usage:
  python3 scripts/linkdrop_publish.py --platform rentry --n 50
  python3 scripts/linkdrop_publish.py --platform telegraph --n 50 --throttle 8
  python3 scripts/linkdrop_publish.py --platform all --n 50      # all enabled platforms
  python3 scripts/linkdrop_publish.py --platform rentry --n 1 --dry-run
"""
from __future__ import annotations
import argparse, json, os, pathlib, re, subprocess, sys, time, datetime, random, html as htmllib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
LOG_DIR = ROOT / "logs"; LOG_DIR.mkdir(exist_ok=True)
LOG_PATH = LOG_DIR / "linkdrop.log"
HUB = "https://boatrentalinmarbella.com"
AUTHOR = "Boat Rental Marbella"

def log(msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with LOG_PATH.open("a") as f:
        f.write(line + "\n")

# ---------- env ----------
def load_env():
    want = ("DEEPSEEK_API_KEY",)
    for p in [ROOT / ".env", ROOT.parent.parent / ".env", pathlib.Path.home() / "aiangels-blog" / ".env"]:
        if p.exists():
            for line in p.read_text().splitlines():
                for k in want:
                    if line.startswith(k + "=") and not os.environ.get(k):
                        os.environ[k] = line.split("=", 1)[1].strip().strip('"').strip("'")
load_env()

# ---------- generation backend ----------
def _deepseek(system, user, max_tokens=2000):
    import requests as _req
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY not set")
    r = _req.post("https://api.deepseek.com/chat/completions",
                  json={"model": "deepseek-chat",
                        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                        "max_tokens": max_tokens, "temperature": 0.9},
                  headers={"Authorization": f"Bearer {key}"}, timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()

def _cli(system, user, timeout_s=300):
    p = subprocess.run(["claude", "-p", system + "\n\n---\n\n" + user, "--output-format", "text"],
                       capture_output=True, text=True, timeout=timeout_s)
    if p.returncode != 0:
        raise RuntimeError(f"claude CLI exit {p.returncode}")
    return p.stdout.strip()

def generate(system, user, max_tokens=2000):
    # Retry DeepSeek on transient network errors before the (launchd-broken) CLI fallback.
    if os.environ.get("DEEPSEEK_API_KEY", "").strip():
        for attempt in range(4):
            try:
                return _deepseek(system, user, max_tokens)
            except Exception as e:
                log(f"  DeepSeek attempt {attempt+1}/4 failed ({str(e)[:80]})")
                time.sleep(3 * (attempt + 1))
        log("  DeepSeek exhausted, trying CLI")
    return _cli(system, user)

# ---------- link targets (from live sitemap) ----------
def slug_to_anchors(url: str) -> list[str]:
    path = url.replace(HUB, "").strip("/")
    if not path:
        return ["boat rental in Marbella", "Boat Rental Marbella", "charter a boat in Marbella"]
    last = path.split("/")[-1]
    words = last.replace("-", " ")
    # a couple of natural variants
    base = re.sub(r"\bmarbella\b", "Marbella", words, flags=re.I)
    base = re.sub(r"\bpuerto banus\b", "Puerto Banús", base, flags=re.I)
    variants = [base]
    if "marbella" not in last:
        variants.append(base + " in Marbella")
    if path.startswith("boats/"):
        variants = [f"the {base}", f"{base} charter", f"{base} in Puerto Banús"]
    if path.startswith("blog/"):
        variants = [f"our guide to {base}", base, f"read about {base}"]
    return [v.strip() for v in variants if v.strip()]

def load_targets() -> list[dict]:
    sm = (SITE / "sitemap.xml").read_text()
    urls = re.findall(r"<loc>([^<]+)</loc>", sm)
    skip = ("/privacy", "/terms", "/cookies", "/cancellation", "/site-map",
            "/es/", "/de/", "/fr/", "/nl/", "/no/", "/pl/", "/ru/", "/sv/", "/ar/", "/uk/")
    targets = []
    for u in urls:
        if any(s in u for s in skip):
            continue
        targets.append({"url": u, "anchors": slug_to_anchors(u)})
    return targets

TARGETS = load_targets()
HUB_ANCHORS = ["boat rental in Marbella", "Boat Rental Marbella", "book a boat in Marbella",
               "charter a boat in Marbella", "Marbella boat charter"]
HERO_IMAGES = [
    f"{HUB}/img/boats/mangusta-80/hero-1600.jpg", f"{HUB}/img/boats/azimut-39/hero-1600.jpg",
    f"{HUB}/img/boats/astondoa-40/hero-1600.jpg", f"{HUB}/img/boats/astondoa-40/sunset-1600.jpg",
    f"{HUB}/img/dolphins/dolphins-jumping-1600.jpg", f"{HUB}/img/hen-party/hen-party-group-puerto-banus-1600.jpg",
]

# ---------- combinatorial topic space ----------
SUBJECTS = ["a yacht charter", "a catamaran charter", "a sunset cruise", "a fishing trip",
            "a jet ski rental", "a licence-free boat day", "a luxury yacht", "a boat party",
            "a family boat day", "a private charter", "the Astondoa 40", "the Azimut 39",
            "the Mangusta 80", "a hen-party boat day", "a proposal cruise", "a Puerto Banús charter"]
ANGLES = ["a first-timer's guide to", "what to expect on", "how much it costs to book",
          "the best season for", "5 things nobody tells you about", "a half-day itinerary for",
          "why couples love", "the ultimate group guide to", "what's included in",
          "how to plan", "a local's tips for", "the perfect day plan for", "comparing options for"]
MODIFIERS = ["in Marbella", "from Puerto Banús", "on the Costa del Sol", "near Estepona",
             "out to Cabopino", "around Sotogrande", "this summer", "in shoulder season",
             "for groups", "for couples", "for families", "for a special occasion"]

def topic_seed(rng) -> str:
    return f"{rng.choice(ANGLES)} {rng.choice(SUBJECTS)} {rng.choice(MODIFIERS)}"

# ---------- per-post content ----------
def pick_links(rng, n=3) -> list[dict]:
    out = [{"url": HUB + "/", "anchor": rng.choice(HUB_ANCHORS)}]
    for t in rng.sample(TARGETS, min(n - 1, len(TARGETS))):
        if t["url"].rstrip("/") == HUB:
            continue
        out.append({"url": t["url"], "anchor": rng.choice(t["anchors"])})
    return out[:n]

SYS = ("You write short, accurate, genuinely useful posts about chartering boats and visiting "
       "Marbella, Puerto Banús and the Costa del Sol (Spain). Real place names and real prices: "
       "from €749/2h skippered, €230/2h Dubhe 8m day boat, Mangusta 80 €4,719/4h; every charter "
       "includes skipper, fuel, drinks, snacks, 21% IVA. Never invent reviews or fake statistics.")

def gen_title(rng, avoid: set) -> str:
    for _ in range(6):
        seed = topic_seed(rng)
        raw = generate(SYS, f"Write ONE specific, natural blog-post title (6-12 words) for: \"{seed}\". "
                            f"Title only, no quotes, no numbering.", max_tokens=60)
        title = raw.splitlines()[0].strip().strip('"').strip()
        title = re.sub(r'^\d+[\.\)]\s*', '', title)
        if 12 < len(title) < 120 and title not in avoid:
            return title
    return None

def gen_markdown(title: str, links: list[dict]) -> str:
    link_lines = "\n".join(f'    - {l["url"]}  (anchor: "{l["anchor"]}")' for l in links)
    user = (f"Write a 350-650 word markdown post titled \"{title}\".\n\n"
            f"Insert these links NATURALLY in the prose as inline markdown links, each exactly once:\n{link_lines}\n\n"
            f"Structure: a 1-2 sentence intro, 2-3 short sections with ## headings, a closing line inviting "
            f"a WhatsApp booking. Output MARKDOWN ONLY — no front-matter, no code fences.")
    md = generate(SYS, user, max_tokens=1600)
    md = re.sub(r"^```(?:markdown)?\s*|\s*```$", "", md, flags=re.MULTILINE).strip()
    # guarantee hub link
    if HUB not in md:
        md += f"\n\nReady to book? [{random.choice(HUB_ANCHORS)}]({HUB}/) — WhatsApp reply in under 5 minutes."
    return md

def md_to_telegraph_nodes(title: str, md: str, hero: str) -> list:
    """Minimal markdown→Telegraph node converter (h2, p, links, lists)."""
    nodes = [{"tag": "img", "attrs": {"src": hero}}]
    def inline(text):
        # split markdown links into a/children
        parts, last = [], 0
        for m in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text):
            if m.start() > last:
                parts.append(text[last:m.start()])
            parts.append({"tag": "a", "attrs": {"href": m.group(2)}, "children": [m.group(1)]})
            last = m.end()
        if last < len(text):
            parts.append(text[last:])
        # strip leftover ** bold markers
        return [p if isinstance(p, dict) else p.replace("**", "") for p in parts] or [text]
    for block in re.split(r"\n\s*\n", md):
        block = block.strip()
        if not block:
            continue
        if block.startswith("## "):
            nodes.append({"tag": "h3", "children": inline(block[3:].strip())})
        elif block.startswith("# "):
            nodes.append({"tag": "h4", "children": inline(block[2:].strip())})
        elif re.match(r"^[-*] ", block):
            items = [{"tag": "li", "children": inline(re.sub(r"^[-*]\s+", "", l))}
                     for l in block.splitlines() if l.strip()]
            nodes.append({"tag": "ul", "children": items})
        else:
            nodes.append({"tag": "p", "children": inline(block)})
    return nodes

# ============================================================
# PLATFORM ADAPTERS
# ============================================================
def _ledger_path(platform): return LOG_DIR / f"linkdrop_{platform}.json"
def load_ledger(platform):
    p = _ledger_path(platform)
    return json.loads(p.read_text()) if p.exists() else {"published": []}
def save_ledger(platform, d): _ledger_path(platform).write_text(json.dumps(d, ensure_ascii=False, indent=2))

# --- Telegraph (graph.org) ---
_TG_TOKENS = ROOT / ".telegraph_tokens.json"
def _tg_accounts(n_needed=3) -> list[str]:
    import requests as _req
    toks = json.loads(_TG_TOKENS.read_text()) if _TG_TOKENS.exists() else []
    while len(toks) < n_needed:
        r = _req.post("https://api.telegra.ph/createAccount",
                      data={"short_name": f"BRM{len(toks)+1}", "author_name": AUTHOR, "author_url": HUB + "/"}).json()
        if not r.get("ok"):
            break
        toks.append(r["result"]["access_token"])
    _TG_TOKENS.write_text(json.dumps(toks))
    return toks

def post_telegraph(title, md, links, rng) -> str:
    import requests as _req
    toks = _tg_accounts(3)
    tok = rng.choice(toks)
    hero = rng.choice(HERO_IMAGES)
    nodes = md_to_telegraph_nodes(title, md, hero)
    r = _req.post("https://api.telegra.ph/createPage",
                  data={"access_token": tok, "title": title[:256], "author_name": AUTHOR,
                        "author_url": HUB + "/", "content": json.dumps(nodes), "return_content": "false"},
                  timeout=60).json()
    if not r.get("ok"):
        raise RuntimeError(f"telegraph: {r}")
    return r["result"]["url"]

# --- rentry.co ---
_RENTRY_CSRF = {"token": None, "cookies": None}
def _rentry_csrf():
    import requests as _req
    s = _req.Session()
    r = s.get("https://rentry.co/", timeout=30)
    m = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', r.text)
    if not m:
        m = re.search(r"csrftoken=([^;]+)", r.headers.get("set-cookie", ""))
    return s, (m.group(1) if m else None)

def post_rentry(title, md, links, rng) -> str:
    import requests as _req
    s, csrf = _rentry_csrf()
    body = f"# {title}\n\n{md}"
    r = s.post("https://rentry.co/api/new",
               headers={"Referer": "https://rentry.co"},
               data={"csrfmiddlewaretoken": csrf, "text": body, "url": "", "edit_code": ""},
               timeout=60).json()
    if str(r.get("status")) != "200":
        raise RuntimeError(f"rentry: {r}")
    return r["url"]

# Active platforms: graph.org/telegra.ph + rentry.co only.
ADAPTERS = {"telegraph": post_telegraph, "rentry": post_rentry}

# ============================================================
def run_platform(platform: str, n: int, throttle: float, dry: bool) -> int:
    if platform not in ADAPTERS:
        log(f"unknown platform {platform}"); return 0
    led = load_ledger(platform)
    used = {p["title"] for p in led["published"]}
    today = datetime.date.today().isoformat()
    today_count = sum(1 for p in led["published"] if p.get("date") == today)
    if today_count >= n:
        log(f"[{platform}] already {today_count}/{n} today — done"); return 0
    target = n - today_count
    log(f"=== [{platform}] target {target} (today {today_count}/{n}) · {len(used)} all-time ===")
    rng = random.Random()
    ok = 0
    for i in range(target):
        try:
            title = gen_title(rng, used)
            if not title:
                log(f"  [{i+1}] no fresh title — skip"); continue
            used.add(title)
            links = pick_links(rng, n=rng.choice([2, 3, 3, 4]))
            md = gen_markdown(title, links)
            if HUB not in md:
                log(f"  [{i+1}] no backlink — skip"); continue
            if dry:
                log(f"  [{i+1}] (dry) {title} · {len(links)} links · {len(md.split())}w"); ok += 1; continue
            url = ADAPTERS[platform](title, md, links, rng)
            led["published"].append({"title": title, "url": url, "date": today,
                                     "links": [l["url"] for l in links]})
            save_ledger(platform, led)
            log(f"  [{i+1}/{target}] ✓ {url}")
            ok += 1
            if throttle:
                time.sleep(throttle)
        except Exception as e:
            log(f"  [{i+1}] ✗ {type(e).__name__}: {str(e)[:160]}")
            time.sleep(2)
    log(f"=== [{platform}] done: {ok}/{target} ===")
    return ok

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--platform", default="all", help="telegraph | rentry | all")
    ap.add_argument("--n", type=int, default=15, help="target posts per platform per day")
    ap.add_argument("--throttle", type=float, default=9.0, help="seconds between posts")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    plats = list(ADAPTERS) if args.platform == "all" else [args.platform]
    total = 0
    for p in plats:
        total += run_platform(p, args.n, args.throttle, args.dry_run)
    log(f"ALL DONE: {total} posts across {len(plats)} platform(s)\n")
    return 0 if total or args.dry_run else 1

if __name__ == "__main__":
    sys.exit(main())
