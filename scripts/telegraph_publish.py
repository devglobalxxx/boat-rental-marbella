#!/usr/bin/env python3
"""Publish N articles/day to Telegra.ph that link back to boatrentalinmarbella.com.

Each article:
  - is a fresh Marbella / boats topic (LLM-generated title, deduped vs ledger)
  - 900-1300 words, real local detail
  - carries the hub backlink + 3-4 deep-page backlinks with VARIED natural anchors
  - opens with one of our own (publicly-hosted) boat photos
  - is published to telegra.ph under the Boat Rental Marbella author (author_url → site)

Backend: DeepSeek primary (works under launchd, $0-ish), claude CLI fallback.
Telegraph API needs no key; the account access_token is created once and cached.

Usage:
    python3 scripts/telegraph_publish.py            # publish N (default 3)
    python3 scripts/telegraph_publish.py --n 1      # one (for testing)
    python3 scripts/telegraph_publish.py --dry-run  # generate, don't publish
"""
from __future__ import annotations
import argparse, json, os, pathlib, re, subprocess, sys, datetime, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "config" / "telegraph_link_targets.json").read_text())
TOKEN_FILE = ROOT / ".telegraph_token"
LEDGER = ROOT / "logs" / "telegraph_published.json"
LOG_DIR = ROOT / "logs"; LOG_DIR.mkdir(exist_ok=True)
LOG_PATH = LOG_DIR / "telegraph_publish.log"
AUTHOR = "Boat Rental Marbella"
HUB = CFG["hub"]["url"]

def log(msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with LOG_PATH.open("a") as f:
        f.write(line + "\n")

# ---------- env ----------
def load_env():
    if os.environ.get("DEEPSEEK_API_KEY"):
        return
    for p in [ROOT / ".env", ROOT.parent.parent / ".env", pathlib.Path.home() / "aiangels-blog" / ".env"]:
        if p.exists():
            for line in p.read_text().splitlines():
                if line.startswith("DEEPSEEK_API_KEY="):
                    os.environ["DEEPSEEK_API_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")
                    return
load_env()

# ---------- generation backend ----------
def _call_deepseek(system: str, user: str) -> str:
    import requests as _req
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY not set")
    resp = _req.post(
        "https://api.deepseek.com/chat/completions",
        json={"model": "deepseek-chat",
              "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
              "max_tokens": 8000, "temperature": 0.8},
        headers={"Authorization": f"Bearer {key}"}, timeout=180,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()

def _call_cli(system: str, user: str, timeout_s: int = 600) -> str:
    proc = subprocess.run(["claude", "-p", system + "\n\n---\n\n" + user, "--output-format", "text"],
                          capture_output=True, text=True, timeout=timeout_s)
    if proc.returncode != 0:
        raise RuntimeError(f"claude CLI exit {proc.returncode}: {proc.stderr[-200:]}")
    return proc.stdout.strip()

def generate(system: str, user: str) -> str:
    if os.environ.get("DEEPSEEK_API_KEY", "").strip():
        try:
            return _call_deepseek(system, user)
        except Exception as e:
            log(f"  DeepSeek failed ({type(e).__name__}: {str(e)[:120]}), falling back to claude CLI")
    return _call_cli(system, user)

# ---------- telegraph ----------
def telegraph_token() -> str:
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    import requests as _req
    r = _req.post("https://api.telegra.ph/createAccount", data={
        "short_name": "BoatRentalMarbella",
        "author_name": AUTHOR,
        "author_url": HUB,
    }).json()
    if not r.get("ok"):
        raise RuntimeError(f"createAccount failed: {r}")
    tok = r["result"]["access_token"]
    TOKEN_FILE.write_text(tok)
    log(f"created Telegraph account, token cached")
    return tok

def publish(token: str, title: str, content_nodes: list) -> str:
    import requests as _req
    r = _req.post("https://api.telegra.ph/createPage", data={
        "access_token": token,
        "title": title[:256],
        "author_name": AUTHOR,
        "author_url": HUB,
        "content": json.dumps(content_nodes),
        "return_content": "false",
    }, timeout=60).json()
    if not r.get("ok"):
        raise RuntimeError(f"createPage failed: {r}")
    return r["result"]["url"]

# ---------- ledger ----------
def load_ledger() -> dict:
    if LEDGER.exists():
        return json.loads(LEDGER.read_text())
    return {"published": []}

def save_ledger(d: dict):
    LEDGER.write_text(json.dumps(d, ensure_ascii=False, indent=2))

# ---------- topic + article generation ----------
def pick_links(seed: int, n: int = 4) -> list:
    """Hub always + (n-1) varied deep targets, deterministic-ish by seed."""
    import random
    rnd = random.Random(seed)
    targets = rnd.sample(CFG["targets"], min(n - 1, len(CFG["targets"])))
    out = [{"url": HUB, "anchor": rnd.choice(CFG["hub"]["anchors"])}]
    for t in targets:
        out.append({"url": t["url"], "anchor": rnd.choice(t["anchors"])})
    return out

def gen_topics(n: int, avoid: list[str]) -> list[str]:
    sys_p = ("You are an editor planning blog topics about chartering boats and visiting Marbella, "
             "Puerto Banús and the Costa del Sol (Spain). Topics must be genuinely useful to travellers "
             "and varied: boat-types, itineraries, seasons, events, neighbourhoods, food/marina guides, "
             "specific boats, family/party/romance angles. No clickbait.")
    user_p = (f"Give {n} fresh article titles (each 6-12 words, specific, no numbering). "
              f"AVOID anything close to these already-used titles:\n{json.dumps(avoid[-120:])}\n\n"
              f"Return one title per line, nothing else.")
    raw = generate(sys_p, user_p)
    titles = [re.sub(r'^[\d\.\-\)\s"]+', '', l).strip().strip('"') for l in raw.splitlines() if l.strip()]
    return [t for t in titles if 12 < len(t) < 130][:n]

def gen_article_nodes(title: str, links: list, hero: str) -> list:
    link_lines = "\n".join(f'    - {l["url"]}  (anchor: "{l["anchor"]}")' for l in links)
    sys_p = (
        "You are a travel/charter writer for Boat Rental Marbella, an independent boat-charter operator "
        "in Puerto Banús. Write accurate, locally-specific, genuinely useful articles. Real place names "
        "(Puerto Banús, Marbella Marina, Cabopino, Estepona, Sotogrande, La Concha, Río Verde, Golden Mile), "
        "real prices in EUR (from €749/2h skippered, €230/2h licence-free Dubhe, Mangusta 80 €4,719/4h). "
        "Every charter includes skipper, fuel, drinks, snacks and 21% IVA. Never invent reviews."
    )
    user_p = (
        f"Write a 900-1300 word article titled: \"{title}\".\n\n"
        f"Insert these backlinks NATURALLY in the prose (each exactly once, as inline links, never as a list):\n{link_lines}\n\n"
        f"Structure: a 2-sentence intro paragraph, then 4-6 H3 sections, then a short closing paragraph "
        f"with a call to message us on WhatsApp to book.\n\n"
        f"OUTPUT: a JSON array of Telegraph DOM nodes ONLY (no markdown fences, no commentary). Node formats:\n"
        f'  image (use FIRST): {{"tag":"img","attrs":{{"src":"{hero}"}}}}\n'
        f'  heading: {{"tag":"h3","children":["Section title"]}}\n'
        f'  paragraph: {{"tag":"p","children":["plain text ",{{"tag":"a","attrs":{{"href":"URL"}},"children":["anchor"]}}," more text"]}}\n'
        f'  bold: {{"tag":"b","children":["text"]}}  list: {{"tag":"ul","children":[{{"tag":"li","children":["item"]}}]}}\n'
        f"Start with the img node. Use the EXACT href URLs and anchor texts given above. Output the JSON array only."
    )
    nodes = None
    for attempt in range(3):
        raw = generate(sys_p, user_p)
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
        s, e = raw.find("["), raw.rfind("]")
        if s < 0 or e <= s:
            log(f"  attempt {attempt+1}: no JSON array, retrying")
            continue
        blob = raw[s:e + 1]
        try:
            nodes = json.loads(blob)
            break
        except json.JSONDecodeError:
            # Lenient repair: drop trailing commas, collapse stray newlines inside strings
            repaired = re.sub(r",\s*([\]}])", r"\1", blob)
            try:
                nodes = json.loads(repaired)
                log(f"  attempt {attempt+1}: parsed after repair")
                break
            except json.JSONDecodeError:
                log(f"  attempt {attempt+1}: JSON parse failed, retrying")
                continue
    if nodes is None:
        raise RuntimeError("article JSON unparseable after 3 attempts")
    # Guarantee hero image first
    if not (nodes and isinstance(nodes[0], dict) and nodes[0].get("tag") == "img"):
        nodes.insert(0, {"tag": "img", "attrs": {"src": hero}})
    # Guarantee hub link present (append a closing CTA paragraph if the model dropped it)
    flat = json.dumps(nodes)
    if HUB not in flat:
        nodes.append({"tag": "p", "children": [
            "Ready to get on the water? ",
            {"tag": "a", "attrs": {"href": HUB}, "children": ["Book your boat in Marbella"]},
            " — WhatsApp reply in under 5 minutes."]})
    return nodes

def count_backlinks(nodes: list) -> int:
    return json.dumps(nodes).count("boatrentalinmarbella.com")

# ---------- indexnow (nudge crawl of the new telegraph URLs) ----------
def ping_google(urls: list):
    # Telegraph pages aren't on our host, so IndexNow can't sign them. Instead ping
    # Google + Bing "ping" endpoints are deprecated; rely on Telegraph's own crawlability.
    # We simply record the URLs; backlinks get discovered when Google recrawls telegra.ph.
    pass

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    led = load_ledger()
    used_titles = [p["title"] for p in led["published"]]
    log(f"=== Telegraph run: target {args.n} article(s) · {len(used_titles)} previously published ===")

    try:
        topics = gen_topics(args.n + 2, used_titles)  # over-generate, drop dupes
    except Exception as e:
        log(f"topic generation failed: {e}")
        return 1
    topics = [t for t in topics if t not in used_titles][:args.n]
    if not topics:
        log("no fresh topics produced — aborting")
        return 1

    token = None if args.dry_run else telegraph_token()
    import random
    day_seed = int(datetime.date.today().strftime("%Y%m%d"))
    ok = 0
    for i, title in enumerate(topics):
        log(f"[{i+1}/{len(topics)}] {title}")
        try:
            links = pick_links(day_seed + i, n=4)
            hero = random.Random(day_seed + i).choice(CFG["hero_images"])
            nodes = gen_article_nodes(title, links, hero)
            bl = count_backlinks(nodes)
            if bl < 1:
                log(f"  ✗ no backlink in article — skipping")
                continue
            if args.dry_run:
                log(f"  (dry-run) {len(nodes)} nodes, {bl} backlinks")
                ok += 1
                continue
            url = publish(token, title, nodes)
            led["published"].append({
                "title": title, "url": url, "backlinks": bl,
                "links": [l["url"] for l in links],
                "date": datetime.date.today().isoformat(),
            })
            save_ledger(led)
            log(f"  ✓ published {url} ({bl} backlinks)")
            ok += 1
        except Exception as e:
            log(f"  ✗ FAILED: {type(e).__name__}: {str(e)[:200]}")

    log(f"=== Done: {ok}/{len(topics)} published. Ledger total: {len(led['published'])} ===\n")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
