#!/usr/bin/env python3
"""Generate sitemap.xml from keyword_map.json."""
import json, pathlib, datetime, subprocess
ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config" / "keyword_map.json").read_text())
SITE = CONFIG["site"]
TODAY = datetime.date.today().isoformat()

def _git_lastmod():
    """Repo-relative path → date of its most recent commit (YYYY-MM-DD).

    Single `git log` pass over site/ — the first commit a file appears in
    (log is newest-first) is its last modification. Avoids one subprocess
    per URL, which would be slow for 500+ pages.
    """
    dates = {}
    try:
        out = subprocess.run(
            ["git", "log", "--format=%x00%cs", "--name-only", "--", "site"],
            cwd=ROOT, capture_output=True, text=True, timeout=120, check=True,
        ).stdout
        current = None
        for line in out.splitlines():
            if line.startswith("\x00"):
                current = line[1:].strip()
            elif line and current:
                dates.setdefault(line, current)
    except Exception:
        pass  # not a git checkout / git unavailable → mtime fallback below
    return dates

GIT_DATES = _git_lastmod()

def lastmod(slug):
    rel = f"site/{slug + '/' if slug else ''}index.html"
    if rel in GIT_DATES:
        return GIT_DATES[rel]
    p = ROOT / rel
    if p.exists():  # uncommitted page → file mtime
        return datetime.date.fromtimestamp(p.stat().st_mtime).isoformat()
    return TODAY

def url(slug, prio, freq):
    loc = f"{SITE['base_url']}/{slug + '/' if slug else ''}"
    return f"  <url><loc>{loc}</loc><lastmod>{lastmod(slug)}</lastmod><changefreq>{freq}</changefreq><priority>{prio}</priority></url>"

lines = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
         url("", "1.0", "weekly")]
# Duplicate-intent dupes canonicalize to a cluster canonical — exclude their
# keys from the sitemap (spokes here, blog below) so only canonicals get crawl budget.
_canon_map_path = ROOT / "config" / "blog_canonical_map.json"
NON_CANONICAL = (set(json.loads(_canon_map_path.read_text())["map"])
                 if _canon_map_path.exists() else set())
for s in CONFIG["spokes"]:
    if s["slug"] in NON_CANONICAL:
        continue
    lines.append(url(s["slug"], "0.9", "weekly"))
lines.append(url("boats", "0.95", "weekly"))  # fleet index (high-intent)
import json as _json
boats_cfg = _json.loads((pathlib.Path(__file__).resolve().parents[1] / "config" / "boats.json").read_text())
for b in boats_cfg["boats"]:
    # Higher priority for our 3 confirmed-price boats, slightly lower for on-request fleet
    prio = "0.8" if b.get("pricing_status") == "on_request" else "0.9"
    lines.append(url(f"boats/{b['slug']}", prio, "weekly"))
lines.append(url("blog", "0.8", "weekly"))  # blog index
lines.append(url("experiences", "0.9", "weekly"))  # experiences hub
for exp_slug in [
    "experiences/family-boat-days-marbella","experiences/photoshoot-yacht-marbella","experiences/bachelor-hen-parties-marbella",
    "experiences/wedding-yacht-marbella","experiences/corporate-yacht-marbella","experiences/honeymoon-yacht-marbella",
    "experiences/snorkeling-tour-marbella","experiences/birthday-yacht-marbella","experiences/proposal-yacht-marbella",
    "experiences/anniversary-yacht-marbella",
]:
    lines.append(url(exp_slug, "0.85", "weekly"))
# Duplicate-intent blog dupes canonicalize to a cluster canonical
# (config/blog_canonical_map.json keys) — keep them out of the sitemap so only
# the canonicals get crawl budget. Pages stay live; they are just not listed.
_canon_map_path = ROOT / "config" / "blog_canonical_map.json"
NON_CANONICAL = (set(json.loads(_canon_map_path.read_text())["map"])
                 if _canon_map_path.exists() else set())
_excluded = 0
for b in CONFIG["blog"]:
    if b["slug"] in NON_CANONICAL:
        _excluded += 1
        continue
    lines.append(url(b["slug"], "0.7", "monthly"))
if _excluded:
    print(f"sitemap: excluded {_excluded} non-canonical blog dupes (blog_canonical_map.json)")
# Spanish (ES) priority pages
for es_slug, prio in [("es", "0.95"), ("es/alquiler-de-yates-marbella", "0.9"),
                      ("es/alquiler-barcos-puerto-banus", "0.9"),
                      ("es/alquiler-barcos-sin-licencia-marbella", "0.9")]:
    lines.append(url(es_slug, prio, "weekly"))
# German (DE) priority pages
for de_slug, prio in [("de", "0.95"), ("de/yachtcharter-marbella", "0.9"),
                      ("de/bootsverleih-puerto-banus", "0.9"),
                      ("de/bootsverleih-ohne-fuehrerschein-marbella", "0.9"),
                      ("de/katamaran-mieten-marbella", "0.9"), ("de/angelboot-mieten-marbella", "0.85"),
                      ("de/sonnenuntergang-bootstour-marbella", "0.9"), ("de/bootsparty-marbella", "0.85"),
                      ("de/luxusyacht-mieten-marbella", "0.9"), ("de/jetski-mieten-marbella", "0.85"),
                      ("de/privat-bootscharter-marbella", "0.85"), ("de/speedboot-mieten-marbella", "0.85"),
                      ("de/segelboot-mieten-marbella", "0.85"), ("de/motoryacht-mieten-marbella", "0.9"),
                      ("de/yachtcharter-puerto-banus", "0.9"), ("de/familien-yachtcharter-marbella", "0.85"),
                      ("de/superyacht-charter-marbella", "0.85"), ("de/tagescharter-marbella", "0.85"),
                      ("de/blog/was-kostet-bootsverleih-marbella", "0.7"),
                      ("de/blog/beste-reisezeit-boot-marbella", "0.7"),
                      ("de/blog/bootsfuehrerschein-spanien", "0.7")]:
    lines.append(url(de_slug, prio, "weekly"))
# UK landing
lines.append(url("uk", "0.9", "weekly"))
# Locale homepages (built by build_languages.py)
for loc_slug in ["fr", "nl", "no", "pl", "ru", "sv", "ar"]:
    lines.append(url(loc_slug, "0.6", "weekly"))
# Human-readable site map page (built by build_sitemap_page.py)
lines.append(url("site-map", "0.4", "weekly"))
# Intentionally excluded: /ig/ (Instagram link-in-bio page, noindexed).
# /api/pages.json and llms-full*.txt use this sitemap as their page manifest,
# so /ig/ stays out of those feeds too.
# Trust + legal
for trust_slug, prio in [("reviews", "0.85"), ("about", "0.7"), ("contact", "0.7"),
                          ("cancellation-policy", "0.5"), ("cookies", "0.4")]:
    lines.append(url(trust_slug, prio, "monthly"))
# Legal pages (EN + ES)
for legal_slug in ["privacy", "terms", "es/privacidad", "es/terminos"]:
    lines.append(url(legal_slug, "0.2", "yearly"))
lines.append('</urlset>')
(ROOT / "site" / "sitemap.xml").write_text("\n".join(lines) + "\n")
print(f"sitemap.xml written ({sum(1 for l in lines if l.startswith('  <url>'))} URLs)")

# Sitemap index — points search engines at both the URL sitemap and the video sitemap.
index = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
         f'  <sitemap><loc>{SITE["base_url"]}/sitemap.xml</loc><lastmod>{TODAY}</lastmod></sitemap>',
         f'  <sitemap><loc>{SITE["base_url"]}/sitemap-video.xml</loc><lastmod>{TODAY}</lastmod></sitemap>',
         '</sitemapindex>']
(ROOT / "site" / "sitemap-index.xml").write_text("\n".join(index) + "\n")
print("sitemap-index.xml written (URL + video)")
