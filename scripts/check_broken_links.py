#!/usr/bin/env python3
"""Scan the built site for internal <a href> and <img src> targets that don't
resolve to an actual file. Read-only report — run after a full build.

Usage: python3 scripts/check_broken_links.py [--fail]
  --fail   exit 1 if anything is broken (for wiring into deploy.sh later)
"""
from __future__ import annotations
import argparse, pathlib, re, sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = ROOT / "site"

LINK_RE = re.compile(r'href="(/[^"#?]*)"')
IMG_RE = re.compile(r'<img[^>]*src="([^"]+)"')

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fail", action="store_true")
    args = ap.parse_args()

    all_pages = set()
    for f in SITE.rglob("index.html"):
        rel = f.relative_to(SITE).parent
        all_pages.add("/" if str(rel) == "." else f"/{rel}/")

    broken_links: dict[str, list[str]] = defaultdict(list)
    broken_imgs: dict[str, list[str]] = defaultdict(list)
    for f in SITE.rglob("index.html"):
        rel = f.relative_to(SITE).parent
        src = "/" if str(rel) == "." else f"/{rel}/"
        html = f.read_text(errors="ignore")
        for m in LINK_RE.finditer(html):
            link = m.group(1)
            if link.startswith(("/api/", "/img/", "/audio/")) or "." in link.rsplit("/", 1)[-1]:
                continue
            norm = link if link.endswith("/") else link + "/"
            if norm not in all_pages:
                broken_links[norm].append(src)
        for m in IMG_RE.finditer(html):
            imgsrc = m.group(1)
            if imgsrc.startswith(("http", "data:")):
                continue
            if not (SITE / imgsrc.lstrip("/")).exists():
                broken_imgs[imgsrc].append(src)

    print(f"{len(all_pages)} known pages, {len(broken_links)} broken link targets, {len(broken_imgs)} broken image srcs\n")
    for link, sources in sorted(broken_links.items(), key=lambda x: -len(x[1])):
        print(f"  {len(sources):3d}x  {link}  (e.g. from {sources[0]})")
    for img, sources in sorted(broken_imgs.items(), key=lambda x: -len(x[1])):
        print(f"  {len(sources):3d}x  [img] {img}  (e.g. from {sources[0]})")

    if args.fail and (broken_links or broken_imgs):
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
