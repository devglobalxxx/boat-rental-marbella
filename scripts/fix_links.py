#!/usr/bin/env python3
"""Repair broken internal links in rendered HTML AND content/*.json sources.

LLM-generated copy invents URL shapes (/boat/X/, /fleet/, /yachts/X/,
/boats/<name>-marbella/). This maps every internal href to a real page:
  1. exact-match against the rendered page set
  2. pattern rewrites (boat→boats, fleet→boats, yachts→boats, strip suffixes)
  3. topic fallbacks (pricing→cost guide, marinas→puerto banus page)
  4. last resort → closest hub (/boats/, /blog/, /)

Run late in deploy (after all builders). Prints a summary; exits 0 always —
the *gate* for new breakage is the separate check in deploy.sh.
"""
from __future__ import annotations
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
CONTENT = ROOT / "content"

def valid_paths():
    v = set()
    for f in SITE.rglob("index.html"):
        rel = f.relative_to(SITE).parent
        v.add("/" if str(rel) == "." else f"/{rel}/")
    return v

VALID = valid_paths()
BOAT_SLUGS = sorted({p.split("/")[2] for p in VALID if p.startswith("/boats/") and p.count("/") == 3})

STATIC_MAP = {
    "/fleet/": "/boats/",
    "/pricing/": "/blog/how-much-does-it-cost-to-rent-a-boat-in-marbella/",
    "/legal/": "/terms/",
    "/ /": "/",
    "/boat-hire-marbella/": "/",
    "/marinas/puerto-banus/": "/boat-rental-puerto-banus/",
    "/locations/puerto-banus-marbella/": "/boat-rental-puerto-banus/",
    "/areas/golden-mile/": "/boat-rental-puerto-banus/",
    "/destinations/cala-del-faro/": "/experiences/calas-marbella-tour/",
    "/experiences/sunset-cruise-marbella/": "/sunset-cruise-marbella/",
    "/experiences/cabopino-half-day/": "/experiences/calas-marbella-tour/",
}

SUFFIXES = ["-fufi", "-flybridge", "-marbella", "-only-catamaran-marbella",
            "-only-catamaran", "-nina", "-grey", "-white"]

def match_boat(slug: str) -> str | None:
    """Fuzzy-match an invented boat slug to a real one."""
    if slug in BOAT_SLUGS:
        return slug
    s = slug
    changed = True
    while changed:
        changed = False
        for suf in SUFFIXES:
            if s.endswith(suf) and s[: -len(suf)] in BOAT_SLUGS:
                return s[: -len(suf)]
            if s.endswith(suf):
                s2 = s[: -len(suf)]
                if s2 != s:
                    s = s2
                    changed = True
    if s in BOAT_SLUGS:
        return s
    # prefix match (azimut-58-flybridge → azimut-58)
    for b in BOAT_SLUGS:
        if s.startswith(b) or b.startswith(s):
            return b
    return None

def resolve(href: str) -> str | None:
    """Return corrected href, or None if already valid / external."""
    if not href.startswith("/") or href.startswith("//"):
        return None
    h = href if href.endswith("/") else href + "/"
    if h in VALID:
        return None
    if h in STATIC_MAP:
        return STATIC_MAP[h]
    parts = [p for p in h.strip("/").split("/") if p]
    # /boat/X/, /yachts/X/, /fleet/X/ → /boats/X/
    if len(parts) == 2 and parts[0] in ("boat", "yachts", "fleet", "boats"):
        m = match_boat(parts[1])
        if m:
            return f"/boats/{m}/"
        return "/boats/"
    # bare boat-name at root, e.g. /azimut-58-flybridge/ or /mangusta-80-marbella/
    if len(parts) == 1:
        m = match_boat(parts[0])
        if m:
            return f"/boats/{m}/"
    # broken blog link → blog hub
    if parts and parts[0] == "blog":
        return "/blog/"
    if parts and parts[0] == "experiences":
        return "/experiences/"
    return "/"

def fix_html(path: pathlib.Path) -> int:
    s = path.read_text(errors="ignore")
    n = 0
    def sub(m):
        nonlocal n
        fixed = resolve(m.group(1))
        if fixed:
            n += 1
            return f'href="{fixed}"'
        return m.group(0)
    new = re.sub(r'href="(/[^"#?]*)"', sub, s)
    if n:
        path.write_text(new)
    return n

def fix_content(path: pathlib.Path) -> int:
    s = path.read_text(errors="ignore")
    n = 0
    def sub(m):
        nonlocal n
        fixed = resolve(m.group(1))
        if fixed:
            n += 1
            return f'href=\\"{fixed}\\"' if '\\"' in m.group(0) else f'href="{fixed}"'
        return m.group(0)
    new = re.sub(r'href=\\?"(/[^"\\#?]*)\\?"', sub, s)
    # markdown links too
    def sub_md(m):
        nonlocal n
        fixed = resolve(m.group(2))
        if fixed:
            n += 1
            return f"[{m.group(1)}]({fixed})"
        return m.group(0)
    new = re.sub(r"\[([^\]]+)\]\((/[^)#?]*)\)", sub_md, new)
    if n:
        path.write_text(new)
    return n

def main():
    html_fixed = sum(fix_html(f) for f in SITE.rglob("index.html"))
    json_fixed = sum(fix_content(f) for f in CONTENT.glob("*.json"))
    print(f"fix_links: {html_fixed} hrefs repaired in HTML, {json_fixed} in content JSON")

if __name__ == "__main__":
    main()
