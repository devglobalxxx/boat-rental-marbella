#!/usr/bin/env python3
"""Emit /api/pages.json — a single-fetch index of every page on the site for
Custom GPT Actions / RAG agents. Each entry has url, title, description, kind,
locale, and a short body excerpt. Designed for sub-200 KB total so a Custom
GPT can fetch it inside one tool call.
"""
from __future__ import annotations
import json, pathlib, re, html as htmllib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = json.loads((ROOT / "config" / "keyword_map.json").read_text())["site"]
SITE_DIR = ROOT / "site"
BASE = SITE["base_url"].rstrip("/")

def strip_html(s: str) -> str:
    s = re.sub(r"<script\b[^>]*>.*?</script>", "", s, flags=re.DOTALL | re.IGNORECASE)
    s = re.sub(r"<style\b[^>]*>.*?</style>", "", s, flags=re.DOTALL | re.IGNORECASE)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", htmllib.unescape(s)).strip()

def meta(html_str: str, name: str) -> str | None:
    m = re.search(rf'<meta\s+name="{name}"\s+content="([^"]*)"', html_str)
    return m.group(1) if m else None

def title(html_str: str) -> str | None:
    m = re.search(r"<title>([^<]+)</title>", html_str)
    return m.group(1).strip() if m else None

def first_para(html_str: str) -> str:
    m = re.search(r'<article[^>]*>(.*?)</article>', html_str, re.DOTALL)
    if not m:
        return ""
    para = re.search(r'<p>(.*?)</p>', m.group(1), re.DOTALL)
    return strip_html(para.group(1))[:400] if para else ""

def sitemap_urls() -> set[str]:
    """URLs from sitemap.xml — the same manifest search engines get. Keeps the
    pages.json count consistent with sitemap.xml and llms-full*.txt."""
    sm = SITE_DIR / "sitemap.xml"
    if not sm.exists():
        return set()
    return set(re.findall(r"<loc>([^<]+)</loc>", sm.read_text()))

def kind_for(slug: str) -> str:
    if not slug: return "hub"
    if slug.startswith("blog/"): return "blog"
    if slug.startswith("boats/"): return "boat"
    if slug.startswith("experiences/"): return "experience"
    if slug.startswith("de/"): return "de"
    if slug.startswith("es/"): return "es"
    if slug == "uk": return "uk"
    if slug in ("reviews", "about", "contact", "cancellation-policy", "cookies", "privacy", "terms"):
        return "trust"
    return "spoke"

def locale_for(slug: str) -> str:
    if slug.startswith("de/"): return "de"
    if slug.startswith("es/"): return "es"
    if slug == "uk" or slug.startswith("uk/"): return "en-GB"
    return "en"

def main():
    manifest = sitemap_urls()
    pages = []
    for f in sorted(SITE_DIR.rglob("index.html")):
        rel = f.relative_to(SITE_DIR).parent
        slug = "" if str(rel) == "." else str(rel)
        url = f"{BASE}/" if not slug else f"{BASE}/{slug}/"
        if manifest and url not in manifest:
            continue  # noindexed (e.g. /ig/) or orphan pages stay out
        s = f.read_text(errors="ignore")
        pages.append({
            "url": url,
            "title": (title(s) or slug)[:140],
            "description": (meta(s, "description") or "")[:300],
            "kind": kind_for(slug),
            "locale": locale_for(slug),
            "excerpt": first_para(s)[:280],
        })

    index = {
        "@context": f"{BASE}/api/pages.json",
        "source": BASE,
        "count": len(pages),
        "kinds": sorted(set(p["kind"] for p in pages)),
        "locales": sorted(set(p["locale"] for p in pages)),
        "usage": (
            "Single-fetch index of every sitemap-listed page for AI agents / Custom GPT Actions. "
            "For a page's full text, fetch its URL directly, or grep the canonical URL in the "
            "full-text dumps: /llms-full-core.txt (hub + transactional + trust + locales), "
            "/llms-full-boats.txt, /llms-full-experiences.txt, /llms-full-blog.txt (chunked into "
            "-2, -3… parts). Highest-value pages only: /llms-full.txt. Site index: /llms.txt. "
            "All prices are in EUR and include 21% Spanish IVA. Always link to source URL when citing."
        ),
        "pages": pages,
    }
    out = SITE_DIR / "api"
    out.mkdir(parents=True, exist_ok=True)
    (out / "pages.json").write_text(json.dumps(index, ensure_ascii=False, indent=2))
    size_kb = (out / "pages.json").stat().st_size // 1024
    print(f"  ✓ /api/pages.json ({len(pages)} pages, {size_kb} KB)")

if __name__ == "__main__":
    main()
