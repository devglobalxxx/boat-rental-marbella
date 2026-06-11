#!/usr/bin/env python3
"""Rebuild hreflang clusters from a single source of truth so every page in a
cluster carries the identical, fully-reciprocal alternate set (Google discards
non-reciprocal hreflang entirely).

Clusters:
  - homepage cluster: every locale hub that exists on disk
  - spoke clusters: EN spoke ↔ ES/DE translations where they exist

Pages outside any cluster get their hreflang block removed (a lone hreflang
is worse than none).
"""
from __future__ import annotations
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
BASE = "https://boatrentalinmarbella.com"

# locale → path (homepage cluster) — only included if the page exists
HOME_CLUSTER = {
    "en": "/",
    "en-GB": "/uk/",
    "es": "/es/",
    "de": "/de/",
    "fr": "/fr/",
    "nl": "/nl/",
    "no": "/no/",
    "pl": "/pl/",
    "ru": "/ru/",
    "sv": "/sv/",
    "ar": "/ar/",
}

SPOKE_CLUSTERS = [
    {"en": "/yacht-charter-marbella/", "es": "/es/alquiler-de-yates-marbella/", "de": "/de/yachtcharter-marbella/"},
    {"en": "/boat-rental-puerto-banus/", "es": "/es/alquiler-barcos-puerto-banus/", "de": "/de/bootsverleih-puerto-banus/"},
    {"en": "/boat-rental-no-license-marbella/", "es": "/es/alquiler-barcos-sin-licencia-marbella/", "de": "/de/bootsverleih-ohne-fuehrerschein-marbella/"},
]

HREFLANG_RE = re.compile(r'<link rel="alternate" hreflang="[^"]*" href="[^"]*">\s*')

def exists(path: str) -> bool:
    rel = path.strip("/")
    p = (SITE / rel / "index.html") if rel else (SITE / "index.html")
    return p.exists()

def block_for(cluster: dict) -> str:
    live = {lang: path for lang, path in cluster.items() if exists(path)}
    if len(live) < 2:
        return ""
    lines = [f'<link rel="alternate" hreflang="{lang}" href="{BASE}{path}">' for lang, path in live.items()]
    xdef = live.get("en") or next(iter(live.values()))
    lines.append(f'<link rel="alternate" hreflang="x-default" href="{BASE}{xdef}">')
    return "\n".join(lines)

def apply(path_str: str, block: str) -> bool:
    rel = path_str.strip("/")
    p = (SITE / rel / "index.html") if rel else (SITE / "index.html")
    if not p.exists():
        return False
    s = p.read_text(errors="ignore")
    stripped = HREFLANG_RE.sub("", s)
    if block:
        # insert after canonical link
        new = re.sub(r'(<link rel="canonical"[^>]*>)', r"\1\n" + block, stripped, count=1)
        if new == stripped:  # no canonical? insert before </head>
            new = stripped.replace("</head>", block + "\n</head>", 1)
    else:
        new = stripped
    if new != s:
        p.write_text(new)
        return True
    return False

def main():
    clusters = [HOME_CLUSTER] + SPOKE_CLUSTERS
    in_cluster = set()
    touched = 0
    for cluster in clusters:
        block = block_for(cluster)
        for lang, path in cluster.items():
            if exists(path):
                in_cluster.add(path)
                if apply(path, block):
                    touched += 1
    # Strip orphan hreflang from all other pages
    stripped = 0
    for f in SITE.rglob("index.html"):
        rel = f.relative_to(SITE).parent
        path = "/" if str(rel) == "." else f"/{rel}/"
        if path in in_cluster:
            continue
        s = f.read_text(errors="ignore")
        if 'rel="alternate" hreflang' in s:
            new = HREFLANG_RE.sub("", s)
            if new != s:
                f.write_text(new)
                stripped += 1
    print(f"inject_hreflang: {touched} cluster pages rebuilt, {stripped} orphan hreflang blocks stripped")

if __name__ == "__main__":
    main()
