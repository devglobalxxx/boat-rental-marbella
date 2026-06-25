#!/usr/bin/env python3
"""Harvest real, verified image URLs from boathire24.com into an image pool.

Scrapes each boat page (and a sample of location pages) for the Supabase
boat-image CDN URLs (decoding Next.js /_next/image?url= wrappers), plus the
og:image and any Pexels images. Writes config/boathire24_images.json which the
backlink generator rotates into articles so every post has relevant, on-brand
imagery that also reinforces boathire24.com's own image-search footprint.

Usage:
  python3 scripts/harvest_boat_images.py            # harvest everything
  python3 scripts/harvest_boat_images.py --boats    # boats only (fast)
"""
import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
URLS = json.loads((ROOT / "config" / "boathire24_landing_urls.json").read_text())
OUT = ROOT / "config" / "boathire24_images.json"
UA = {"User-Agent": "Mozilla/5.0 (compatible; BoatHire24Bot/1.0)"}


def _get(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore")


def _decode_imgs(html):
    """Return de-duped, decoded image URLs found on a page (supabase + pexels)."""
    found = []
    for raw in re.findall(r'/_next/image\?url=([^&"\']+)', html):
        u = urllib.parse.unquote(raw).split("?")[0]
        if "supabase" in u and "boat-images" in u:
            found.append(u)
    # direct (non-wrapped) image tags
    for u in re.findall(r'<img[^>]+src=["\']([^"\']+)', html):
        if u.startswith("http") and ("supabase" in u or "pexels" in u):
            found.append(u.split("?")[0] if "supabase" in u else u.replace("&amp;", "&"))
    # og:image
    for u in re.findall(r'og:image["\'][^>]*content=["\']([^"\']+)', html):
        if u.startswith("http"):
            found.append(u.replace("&amp;", "&"))
    seen, out = set(), []
    for u in found:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def _verify(url):
    try:
        req = urllib.request.Request(url, method="HEAD", headers=UA)
        r = urllib.request.urlopen(req, timeout=15)
        ct = r.headers.get("content-type", "")
        return r.status == 200 and ct.startswith("image")
    except Exception:
        return False


def _title(html):
    m = re.search(r"<title[^>]*>([^<]+)</title>", html)
    return (m.group(1).split("|")[0].strip() if m else "").strip()


def harvest_boats():
    boats = {}
    total = len(URLS["boats"])
    for i, url in enumerate(URLS["boats"], 1):
        slug = url.rstrip("/").split("/")[-1]
        try:
            html = _get(url)
            imgs = [u for u in _decode_imgs(html) if "boat-images" in u]
            imgs = [u for u in imgs if _verify(u)]
            if imgs:
                boats[slug] = {"name": _title(html) or slug.replace("-", " ").title(),
                               "url": url, "images": imgs}
                print(f"[{i}/{total}] {slug}: {len(imgs)} imgs")
            else:
                print(f"[{i}/{total}] {slug}: no verified imgs", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"[{i}/{total}] {slug}: ERR {str(e)[:50]}", file=sys.stderr)
    return boats


def harvest_generic(sample=60):
    """Grab generic sea/marina images from a sample of location pages (Pexels)."""
    generic = []
    seen = set()
    locs = URLS["locations"]
    step = max(1, len(locs) // sample)
    for url in locs[::step][:sample]:
        try:
            html = _get(url)
            for u in _decode_imgs(html):
                if "pexels" in u and u not in seen:
                    seen.add(u)
                    generic.append(u)
        except Exception:
            continue
    # verify a capped subset
    generic = [u for u in generic if _verify(u)][:40]
    print(f"generic pool: {len(generic)} pexels imgs")
    return generic


def main():
    boats_only = "--boats" in sys.argv
    data = json.loads(OUT.read_text()) if OUT.exists() else {"boats": {}, "generic": []}
    print("== harvesting boat images ==")
    data["boats"] = harvest_boats()
    if not boats_only:
        print("== harvesting generic images ==")
        data["generic"] = harvest_generic()
    img_count = sum(len(b["images"]) for b in data["boats"].values()) + len(data["generic"])
    OUT.write_text(json.dumps(data, indent=1, ensure_ascii=False))
    print(f"\nWROTE {OUT}: {len(data['boats'])} boats, "
          f"{len(data['generic'])} generic, {img_count} images total")


if __name__ == "__main__":
    main()
