#!/usr/bin/env python3
"""Deterministic internal-link injector for the jet-ski / water-sports cluster.

The site's build_link_graph only linkifies anchor phrases already in prose, so
new pages can end up orphaned. This appends a "Related: jet ski & water sports"
block (before </main>) to:
  - each jet/water-sports page  -> cross-links the cluster
  - relevant hub/spoke pages    -> gives every jet page >=4 inbound links
guaranteeing no orphans. Idempotent (re-running replaces the block).
"""
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = ROOT / "site"

JET = [
    ("jet-ski-marbella", "Jet Ski Marbella"),
    ("jet-ski-puerto-banus", "Jet Ski Puerto Banús"),
    ("jet-ski-hire-marbella", "Jet Ski Hire Marbella"),
    ("jet-ski-rental-puerto-banus", "Jet Ski Rental Puerto Banús"),
    ("jet-ski-rental-estepona", "Jet Ski Rental Estepona"),
    ("jet-ski-rental-fuengirola", "Jet Ski Rental Fuengirola"),
    ("jet-ski-rental-benalmadena", "Jet Ski Rental Benalmádena"),
    ("jet-ski-tours-marbella", "Jet Ski Tours Marbella"),
    ("jet-ski-safari-puerto-banus", "Jet Ski Safari Puerto Banús"),
    ("jet-ski-rental-costa-del-sol", "Jet Ski Rental Costa del Sol"),
    ("flyboard-marbella", "Flyboard Marbella"),
    ("water-sports-marbella", "Water Sports Marbella"),
    ("jet-ski-rental-nerja", "Jet Ski Rental Nerja"),
    ("jet-ski-rental-malaga", "Jet Ski Rental Málaga"),
]
# Hub/spoke pages that should also point at the jet cluster (inbound coverage).
HUBS = ["", "boat-rental-puerto-banus", "experiences", "boat-party-marbella",
        "sunset-cruise-marbella", "fishing-boat-rental-marbella",
        "yacht-charter-marbella", "boat-rental-no-license-marbella"]

BLOCK = re.compile(r"\n?<!--JETLINKS-->.*?<!--/JETLINKS-->", re.S)


def block_for(self_slug: str, n: int = 6) -> str:
    items = [(s, a) for s, a in JET if s != self_slug][:n] if self_slug in dict(JET) \
        else [(s, a) for s, a in JET][:n]
    # rotate by hash so different pages surface different cluster members
    h = sum(ord(c) for c in self_slug)
    pool = [(s, a) for s, a in JET if s != self_slug]
    sel = [pool[(h + i) % len(pool)] for i in range(min(n, len(pool)))]
    seen, picks = set(), []
    for s, a in sel:
        if s not in seen:
            seen.add(s); picks.append((s, a))
    lis = "".join(f'<li><a href="/{s}/">{a}</a></li>' for s, a in picks)
    return (f'\n<!--JETLINKS-->\n<section class="related-cluster" style="max-width:760px;margin:32px auto;padding:0 20px">'
            f'<h2>Jet ski &amp; water sports on the Costa del Sol</h2><ul>{lis}</ul></section>\n<!--/JETLINKS-->')


def apply_to(slug: str, self_slug: str):
    path = SITE / slug / "index.html" if slug else SITE / "index.html"
    if not path.exists():
        return False
    html = path.read_text()
    html = BLOCK.sub("", html)
    if "</main>" not in html:
        return False
    html = html.replace("</main>", block_for(self_slug) + "\n</main>", 1)
    path.write_text(html)
    return True


def main():
    done = 0
    for s, _ in JET:
        if apply_to(s, s):
            done += 1
    for h in HUBS:
        if apply_to(h, h or "home"):
            done += 1
    print(f"jet-ski link block injected into {done} pages")


if __name__ == "__main__":
    main()
