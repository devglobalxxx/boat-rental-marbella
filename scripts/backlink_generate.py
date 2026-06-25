#!/usr/bin/env python3
"""Runtime generator for BoatHire24 backlink articles (blueprint-driven).

Produces fresh, UNIQUE, SEO + LLM-optimised articles into a channel's backlog.
Each article follows the synthesised blueprint in config/backlink_seo_spec.json:
direct-answer opener, question headings with extractable answers, At-a-glance and
FAQ blocks, 1-2 relevant boat images, and 2-4 links to DIFFERENT boathire24.com
pages with varied, archetype-mapped anchor text. The per-article plan (location,
links, anchors, images) comes from backlink_plan.py so every channel obeys the
same rules; the LLM only writes prose.

Requires a key in config/llm_key.json (gitignored):
  {"deepseek_api_key": "sk-..."}     # or env DEEPSEEK_API_KEY

Usage:
  python3 scripts/backlink_generate.py <channel> <count> [start_index]
  python3 scripts/backlink_generate.py check <file.json>     # validate one article
  channels: telegraph | graph_org | livejournal | rentry
"""
import json
import os
import pathlib
import re
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import backlink_plan as BP  # noqa: E402
from boat_images import figure_html  # noqa: E402

SPEC = json.loads((ROOT / "config" / "backlink_seo_spec.json").read_text())
TEMPLATE = SPEC["deepseek_prompt_template"]
URLS = json.loads((ROOT / "config" / "boathire24_landing_urls.json").read_text())
ALL_URLS = set(sum((URLS[k] for k in ("locations", "blog", "boats", "core", "home")), []))
USED = ROOT / "config" / "backlink_topics_used.json"
USED_IMG = ROOT / "config" / "backlink_images_used.json"
KEYFILE = ROOT / "config" / "llm_key.json"
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"


# ----------------------------------------------------------------------------- key
def _env_key(name="DEEPSEEK_API_KEY"):
    """Read a key from the environment or the project .env (same source the repo's
    other DeepSeek automation uses), so auto-refill works without a separate file."""
    if os.environ.get(name):
        return os.environ[name]
    envf = ROOT / ".env"
    if envf.exists():
        for line in envf.read_text().splitlines():
            line = line.strip()
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _key():
    if KEYFILE.exists():
        k = json.loads(KEYFILE.read_text()).get("deepseek_api_key")
        if k:
            return k
    k = _env_key()
    if not k:
        sys.exit(f"No DeepSeek key. Create {KEYFILE} with "
                 '{"deepseek_api_key":"sk-..."} (gitignored), set DEEPSEEK_API_KEY, '
                 "or add DEEPSEEK_API_KEY=... to .env.")
    return k


# --------------------------------------------------------------------------- prompt
def build_prompt(a: dict) -> str:
    links = {l["role"]: l for l in a["links"]}
    primary = links.get("primary", a["links"][0])
    secondary = links.get("secondary") or (a["links"][1] if len(a["links"]) > 1 else primary)
    home = links.get("home")
    fourth = links.get("resource") or links.get("sibling")
    imgs = a["images"]
    image_count = len(imgs)

    home_url = home["url"] if home else ""
    home_anchor = home["anchor"] if home else ""
    extra = ""
    if fourth:
        extra = (f"4. EXTRA ({fourth['role']}): {fourth['url']}  | anchor: {fourth['anchor']} "
                 f"(place in {fourth['place']}); include only if link_count >= 4.")

    sub = {
        "location": a["location"], "angle": a["angle"], "currency": a["currency"],
        "sea": "the actual sea, lake or river at this destination (name it correctly)",
        "entities": "real marinas, ports, harbours, bays, islands and nearby towns that you are "
                    "confident genuinely exist at this destination (do not invent names)",
        "year": str(a["year"]), "link_count": str(a["link_count"]),
        "primary_url": primary["url"], "primary_anchor": primary["anchor"],
        "secondary_url": secondary["url"], "secondary_anchor": secondary["anchor"],
        "home_or_host_url": home_url or "https://boathire24.com",
        "extra_link_line": extra,
        "boat_name": a.get("boat_name") or "the listed boat",
        "image_count": str(image_count),
        "image_url": imgs[0]["url"] if imgs else "",
        "image_alt": imgs[0]["alt"] if imgs else "",
        "image_url_2": imgs[1]["url"] if image_count > 1 else "",
        "image_alt_2": imgs[1]["alt"] if image_count > 1 else "",
    }
    out = TEMPLATE
    for k, v in sub.items():
        out = out.replace("{" + k + "}", v)
    # Add the explicit anchor assignments + title hint so the model cannot drift.
    anchor_lines = "\n".join(
        f"   - {l['role'].upper()} -> {l['url']} | anchor: \"{l['anchor']}\" ({l['archetype']}); place in {l['place']}"
        for l in a["links"])
    out += (f"\n\nEXPLICIT LINK PLAN for THIS article (use these EXACT urls + anchors, "
            f"one per section, never two links adjacent):\n{anchor_lines}\n"
            f"Base the TITLE on: \"{a['title_hint']}\" (refine to 50-65 chars, keep the place "
            f"in the first words, add one differentiator). Write {a['link_count']} links total.")
    return out


# ----------------------------------------------------------------------- deepseek
def deepseek(key, prompt):
    body = json.dumps({
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are an expert British travel and boating writer. "
             "You write original, genuinely useful, accurate articles and output STRICT JSON only."},
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 1.0,
        "max_tokens": 3200,
    }).encode()
    req = urllib.request.Request(DEEPSEEK_URL, data=body, headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    res = json.load(urllib.request.urlopen(req, timeout=180))
    return res["choices"][0]["message"]["content"]


# ----------------------------------------------------------------- post-process
EMDASH = re.compile(r"\s*[—–‒]\s*")
BANNED_BLOCK = re.compile(r"<(script|style|table|thead|tbody|tfoot)[^>]*>.*?</\1>", re.I | re.S)


def sanitize(html: str) -> str:
    """Enforce house style + the telegraph tag subset."""
    html = BANNED_BLOCK.sub(" ", html)
    # remap headings outside the subset
    html = re.sub(r"<(/?)h[12]\b", r"<\1h3", html, flags=re.I)
    html = re.sub(r"<(/?)h[56]\b", r"<\1h4", html, flags=re.I)
    # unwrap div/span/table-cell tags (keep inner text)
    html = re.sub(r"</?(div|span|table|thead|tbody|tfoot|tr|td|th)\b[^>]*>", " ", html, flags=re.I)
    # house style: no em/en dashes, no exclamation marks
    html = EMDASH.sub(", ", html)
    html = html.replace("!", ".")
    html = re.sub(r"\.{2,}", ".", html)
    return re.sub(r"[ \t]{2,}", " ", html).strip()


def fix_images(html: str, a: dict) -> str:
    """Force the figure src/alt to our exact picked images (the model may alter URLs);
    inject missing figures; drop extras. Keeps the model's caption when present."""
    imgs = a["images"]
    figs = re.findall(r"<figure>.*?</figure>", html, flags=re.S)

    def build(i, caption=None):
        im = imgs[i]
        cap = caption or im["caption"]
        cap = EMDASH.sub(", ", cap).replace("!", ".").strip()
        return (f'<figure><img src="{im["url"]}" alt="{im["alt"]}"/>'
                f'<figcaption>{cap}</figcaption></figure>')

    # Rewrite each existing figure in document order to our URL/alt, keep its caption.
    for i, fig in enumerate(figs):
        capm = re.search(r"<figcaption>(.*?)</figcaption>", fig, flags=re.S)
        caption = capm.group(1).strip() if capm else None
        replacement = build(i, caption) if i < len(imgs) else ""
        html = html.replace(fig, replacement, 1)

    # Too few figures: inject after the first </p>, and (for 2) before the cost section.
    present = len(re.findall(r"<figure>", html))
    need = len(imgs)
    if present < need:
        for i in range(present, need):
            block = build(i)
            if i == 0:
                html = re.sub(r"(</p>)", r"\1\n" + block, html, count=1)
            else:
                # before a cost/price/how-much heading if we can find one, else append
                m = re.search(r"<h3>[^<]*(cost|price|how much)[^<]*</h3>", html, flags=re.I)
                if m:
                    html = html[:m.start()] + block + "\n" + html[m.start():]
                else:
                    html = re.sub(r"(</p>)", r"\1\n" + block, html, count=1)
    return html


# Fallback sentence per ANCHOR ARCHETYPE so the injected text fits the anchor wording.
_LINK_SENTENCE = {
    "exact": " You can {a} for your chosen dates.",
    "geo": " You can {a} for your chosen dates.",
    "partial": " You can {a} in a few minutes.",
    "product": " One option worth a look is {a}.",
    "branded": " You can also see more on {a}.",
    "naked": " You can also see more at {a}.",
    "owner": " If you own a boat, you can {a} and earn from spare days.",
    "topic": " For more detail, {a} is a useful read.",
    "resource": " To see how booking works, visit {a}.",
}


def inject_links(html: str, a: dict) -> str:
    """Guarantee the planned links exist. DeepSeek sometimes omits links despite the
    plan; inject any missing one into a distinct body paragraph (not the opener, not
    the FAQ) with a natural trailing sentence, spaced across paragraphs."""
    present = set(re.findall(r'href="([^"]+)"', html))
    missing = [l for l in a["links"] if l["url"] not in present]
    if not missing:
        return html
    faq = re.search(r"<h3[^>]*>\s*Questions about", html, re.I)
    faq_pos = faq.start() if faq else len(html)
    paras = list(re.finditer(r"<p>.*?</p>", html, re.S))
    cand = [m for i, m in enumerate(paras)
            if i > 0 and m.start() < faq_pos and "<a " not in m.group(0)]
    if not cand:
        cand = [m for i, m in enumerate(paras) if i > 0] or paras
    used = set()
    n = len(missing)
    for k, l in enumerate(missing):
        if not cand:
            break
        ci = min((k * len(cand)) // max(1, n), len(cand) - 1)
        while ci in used and ci < len(cand) - 1:
            ci += 1
        used.add(ci)
        anchor = f'<a href="{l["url"]}">{l["anchor"]}</a>'
        sentence = _LINK_SENTENCE.get(l.get("archetype"),
                                      " You can find this {a} on BoatHire24.").format(a=anchor)
        old = cand[ci].group(0)
        new = old[:-4] + sentence + "</p>"
        html = html.replace(old, new, 1)
    return html


# ------------------------------------------------------------------- validation
def validate(art: dict) -> list:
    """Return a list of problems (empty = passes). Programmatic subset of the
    blueprint quality_checklist."""
    p = []
    html = art.get("html", "")
    title = art.get("title", "")
    text = re.sub(r"<[^>]+>", " ", html)
    words = len(text.split())
    if not (650 <= words <= 1000):
        p.append(f"word count {words} not in 650-1000")
    h3 = len(re.findall(r"<h3\b", html, re.I))
    if not (4 <= h3 <= 8):
        p.append(f"h3 count {h3} not in 4-8")
    questions = len(re.findall(r"<h3\b[^>]*>[^<]*\?", html, re.I))
    if questions < 2:
        p.append(f"only {questions} question headings (need >=2)")
    if "<ul" not in html.lower():
        p.append("no <ul>")
    if "<ol" not in html.lower():
        p.append("no <ol>")
    if len(re.findall(r"<blockquote", html, re.I)) < 1:
        p.append("no <blockquote>")
    # links
    hrefs = re.findall(r'href="(https?://boathire24\.com[^"]*)"', html)
    n = len(hrefs)
    if not (2 <= n <= 4):
        p.append(f"link count {n} not in 2-4")
    if len(set(hrefs)) != n:
        p.append("duplicate link URLs")
    for h in hrefs:
        if h.rstrip("/") not in {u.rstrip("/") for u in ALL_URLS}:
            p.append(f"link not in landing set: {h}")
    # adjacency: no two <a> in one <li>
    for li in re.findall(r"<li\b[^>]*>.*?</li>", html, re.S):
        if li.count("<a ") > 1:
            p.append("two links in one <li>")
            break
    # style
    if "!" in text:
        p.append("exclamation mark present")
    if re.search(r"[—–‒]", html):
        p.append("em/en dash present")
    for bad in ("<h1", "<h2", "<table", "<div", "<span", "<script"):
        if bad in html.lower():
            p.append(f"banned tag {bad}")
    # title
    if not (40 <= len(title) <= 75):
        p.append(f"title length {len(title)} not in 40-75")
    if "!" in title or re.search(r"[—–‒]", title):
        p.append("title has ! or dash")
    # images
    figs = len(re.findall(r"<figure>", html))
    if not (1 <= figs <= 2):
        p.append(f"figure count {figs} not in 1-2")
    if re.search(r'<img(?![^>]*\bsrc=)', html):
        p.append("img without src")
    return p


# ------------------------------------------------------------------------- state
def _load(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def _save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, ensure_ascii=False))


# ---------------------------------------------------------------------- generate
def generate(channel, count, start_index=0):
    key = _key()
    outdir = ROOT / "content" / channel
    outdir.mkdir(parents=True, exist_ok=True)
    used = _load(USED, {})
    seen = set(used.get(channel, []))
    used_img = _load(USED_IMG, {})
    img_seen = set(used_img.get(channel, []))

    # Walk planned assignments, skipping ones whose topic we've already done.
    made = 0
    idx = start_index
    guard = 0
    while made < count and guard < count * 8:
        guard += 1
        a = BP.plan_one(channel, idx)
        idx += 1
        if not BP.is_real_location(a["location_url"]):
            continue   # skip generic non-geo pages (e.g. /boat-rental) as primaries
        if a["topic_key"] in seen:
            continue
        prompt = build_prompt(a)
        try:
            raw = deepseek(key, prompt)
            art = json.loads(raw)
        except Exception as e:  # noqa: BLE001
            print(f"  gen error idx={a['idx']}: {str(e)[:80]}", file=sys.stderr)
            time.sleep(2)
            continue
        art["html"] = inject_links(fix_images(sanitize(art.get("html", "")), a), a)
        art["title"] = EMDASH.sub(", ", art.get("title", "")).replace("!", ".").strip()
        problems = validate(art)
        if problems:
            print(f"  reject idx={a['idx']} {a['location']}: {problems[:3]}", file=sys.stderr)
            continue
        # enrich + persist
        art.update({
            "author_name": "BoatHire24", "author_url": "https://boathire24.com",
            "topic": a["angle"], "tags": "boat rental, yacht charter, travel",
            "location": a["location"], "primary_url": a["location_url"],
        })
        stamp = f"{int(time.time())}{made:02d}"
        slug = re.sub(r"[^a-z0-9]+", "-", a["angle"].lower()).strip("-")[:48]
        fn = outdir / f"gen-{stamp}-{slug}.json"
        fn.write_text(json.dumps(art, indent=1, ensure_ascii=False))
        seen.add(a["topic_key"])
        for im in a["images"]:
            img_seen.add(im["url"])
        made += 1
        print(f"  OK {fn.name}  ({a['location']}, {a['link_count']} links, {len(a['images'])} imgs)")

    used[channel] = sorted(seen)
    _save(USED, used)
    used_img[channel] = sorted(img_seen)
    _save(USED_IMG, used_img)
    print(f"{channel}: generated {made}/{count} into {outdir}")


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(1)
    if a[0] == "check":
        art = json.loads(pathlib.Path(a[1]).read_text())
        probs = validate(art)
        print("PASS" if not probs else "FAIL: " + "; ".join(probs))
        sys.exit(0 if not probs else 1)
    if a[0] == "fix":
        # Deterministic house-style cleanup of an existing article file, then report.
        path = pathlib.Path(a[1])
        art = json.loads(path.read_text())
        art["html"] = sanitize(art.get("html", ""))
        art["title"] = EMDASH.sub(", ", art.get("title", "")).replace("!", ".").strip()
        path.write_text(json.dumps(art, indent=1, ensure_ascii=False))
        probs = validate(art)
        print("PASS" if not probs else "FAIL: " + "; ".join(probs))
        sys.exit(0 if not probs else 1)
    channel = a[0]
    count = int(a[1]) if len(a) > 1 else 10
    start = int(a[2]) if len(a) > 2 else 0
    generate(channel, count, start)


if __name__ == "__main__":
    main()
