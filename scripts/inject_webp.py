#!/usr/bin/env python3
"""WebP everywhere (SEO audit 2026-07, batch M7).

1. Generates a .webp sibling (quality 82, Pillow) for every site/img/**/*.jpg
   that lacks one — skipped when the webp would be larger than the jpg.
2. Injects <source type="image/webp"> into every <picture> whose jpg srcset has
   webp siblings (hero pictures — original behaviour), AND wraps every bare
   local-jpg <img> (galleries, blog inline images) in a <picture> with a webp
   source. Idempotent: pictures that already carry a webp source are skipped,
   and wrapped imgs aren't re-wrapped.
"""
from __future__ import annotations
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
IMG_DIR = SITE / "img"

IMG_RE = re.compile(r"<img\b[^>]*>")
SRC_RE = re.compile(r'\bsrc="([^"]+)"')
SRCSET_RE = re.compile(r'\bsrcset="([^"]+)"')
SIZES_RE = re.compile(r'\bsizes="([^"]+)"')


# ---------- webp generation ----------
def generate_webps() -> tuple[int, int]:
    from PIL import Image
    made = skipped = 0
    for jpg in IMG_DIR.rglob("*.jpg"):
        webp = jpg.with_suffix(".webp")
        if webp.exists():
            continue
        try:
            with Image.open(jpg) as im:
                im.save(webp, "WEBP", quality=82, method=4)
            if webp.stat().st_size >= jpg.stat().st_size:
                webp.unlink()  # no win — keep serving the jpg
                skipped += 1
            else:
                made += 1
        except Exception as e:  # noqa: BLE001
            print(f"  webp failed for {jpg.relative_to(ROOT)}: {e}")
            if webp.exists():
                webp.unlink()
    return made, skipped


# ---------- srcset helpers ----------
def _webp_url(url: str) -> str | None:
    """Local .jpg url -> webp sibling url if it exists on disk, else None."""
    if url.startswith("http") or not url.endswith(".jpg"):
        return None
    rel = url.lstrip("/").rsplit(".", 1)[0] + ".webp"
    return "/" + rel if (SITE / rel).exists() else None


def webp_srcset(jpg_srcset: str) -> str | None:
    entries = []
    for part in jpg_srcset.split(","):
        part = part.strip()
        if not part:
            continue
        bits = part.split()
        w = _webp_url(bits[0])
        if not w:
            return None
        entries.append(w + (" " + bits[1] if len(bits) > 1 else ""))
    return ", ".join(entries) if entries else None


def _source_for(img_tag: str) -> str | None:
    """Build the <source type=image/webp> tag for an <img>, or None."""
    m = SRCSET_RE.search(img_tag)
    if m:
        ws = webp_srcset(m.group(1))
        if not ws:
            return None
        sm = SIZES_RE.search(img_tag)
        sizes = f' sizes="{sm.group(1)}"' if sm else ""
        return f'<source type="image/webp" srcset="{ws}"{sizes}>'
    m = SRC_RE.search(img_tag)
    if m:
        w = _webp_url(m.group(1))
        return f'<source type="image/webp" srcset="{w}">' if w else None
    return None


# ---------- html injection ----------
def _inside_picture(s: str, pos: int) -> bool:
    open_p = s.rfind("<picture", 0, pos)
    close_p = s.rfind("</picture>", 0, pos)
    return open_p > close_p


def process(path: pathlib.Path) -> bool:
    s = path.read_text(errors="ignore")
    out, last, changed = [], 0, False
    for m in IMG_RE.finditer(s):
        img = m.group(0)
        src = _source_for(img)
        if not src:
            continue
        if _inside_picture(s, m.start()):
            # picture already exists — add the webp source right after <picture...>
            # unless this picture already has one.
            open_p = s.rfind("<picture", 0, m.start())
            seg = s[open_p:m.start()]
            if '<source type="image/webp"' in seg:
                continue
            tag_end = s.index(">", open_p) + 1
            out.append(s[last:tag_end])
            out.append(src)
            out.append(s[tag_end:m.end()])
        else:
            out.append(s[last:m.start()])
            out.append(f"<picture>{src}{img}</picture>")
        last = m.end()
        changed = True
    if not changed:
        return False
    out.append(s[last:])
    path.write_text("".join(out))
    return True


def main():
    made, skipped = generate_webps()
    print(f"inject_webp: generated {made} webp files ({skipped} skipped, no size win)")
    n = sum(1 for f in SITE.rglob("index.html") if process(f))
    print(f"inject_webp: webp <source> added on {n} pages")


if __name__ == "__main__":
    main()
