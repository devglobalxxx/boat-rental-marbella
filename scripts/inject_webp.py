#!/usr/bin/env python3
"""Add <source type="image/webp"> to every hero <picture> whose jpg srcset has
.webp siblings on disk. Hero is the LCP element — WebP here cuts ~30-40% off
the largest transfer. Idempotent.
"""
from __future__ import annotations
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = ROOT / "site"

PIC_RE = re.compile(r'(<picture class="hero-img-wrap">)(\s*)(<img[^>]*srcset="([^"]+)"[^>]*>)', re.DOTALL)

def webp_srcset(jpg_srcset: str) -> str | None:
    entries = []
    for part in jpg_srcset.split(","):
        part = part.strip()
        if not part:
            continue
        bits = part.split()
        url = bits[0]
        if not url.endswith(".jpg") or url.startswith("http"):
            return None
        webp_rel = url.lstrip("/").rsplit(".", 1)[0] + ".webp"
        if not (SITE / webp_rel).exists():
            return None
        entries.append("/" + webp_rel + (" " + bits[1] if len(bits) > 1 else ""))
    return ", ".join(entries) if entries else None

def process(path: pathlib.Path) -> bool:
    s = path.read_text(errors="ignore")
    if '<source type="image/webp"' in s:
        return False
    changed = False
    def sub(m):
        nonlocal changed
        ws = webp_srcset(m.group(4))
        if not ws:
            return m.group(0)
        changed = True
        return m.group(1) + m.group(2) + f'<source type="image/webp" srcset="{ws}" sizes="100vw">' + m.group(2) + m.group(3)
    new = PIC_RE.sub(sub, s)
    if changed:
        path.write_text(new)
    return changed

def main():
    n = sum(1 for f in SITE.rglob("index.html") if process(f))
    print(f"inject_webp: hero <source webp> added on {n} pages")

if __name__ == "__main__":
    main()
