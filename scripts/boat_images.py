#!/usr/bin/env python3
"""Image pool + picker for BoatHire24 backlink articles.

Loads config/boathire24_images.json (built by harvest_boat_images.py) and picks
relevant, verified boat photos for an article. Location-aware: a Marbella article
prefers a boat photographed in Marbella, falling back to any boat, then generic
sea/marina shots. Produces SEO-ready alt text + a short caption for each image.

Import and use:
    from boat_images import pick_images
    imgs = pick_images("Marbella", n=2, seed=7)
    # -> [{"url":..., "alt":..., "caption":..., "boat":..., "boat_url":...}, ...]
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
POOL = ROOT / "config" / "boathire24_images.json"


def _clean(s: str) -> str:
    """Strip em/en dashes and collapse whitespace (house style: no em-dashes)."""
    s = s.replace("—", " ").replace("–", " ").replace("—", " ").replace("–", " ")
    s = re.sub(r"\s+", " ", s).strip(" -·,")
    return s.strip()


def _parse(name: str):
    """From 'Azimut 58 — White — Motor yacht in Marbella' derive
    (boat_label, boat_type, location)."""
    raw = name
    loc = None
    m = re.search(r"\bin\s+([A-Za-z][A-Za-z \-']+)$", raw)
    if m:
        loc = _clean(m.group(1))
        raw = raw[:m.start()].strip(" -—–·")
    btype = None
    for t in ("Luxury yacht", "Motor yacht", "Sailing yacht", "Catamaran",
              "Speedboat", "Jet ski", "Yacht", "Sailboat", "Boat"):
        if re.search(t, name, re.I):
            btype = t.lower()
            break
    label = _clean(raw.split("—")[0].split("·")[0])
    return label or "boat", (btype or "boat"), (loc or "")


def _load():
    if not POOL.exists():
        return {"boats": {}, "generic": []}
    return json.loads(POOL.read_text())


# Build a flat, ordered list of image records once at import.
def _records():
    data = _load()
    recs = []
    for slug, b in data["boats"].items():
        label, btype, loc = _parse(b.get("name", slug))
        for i, url in enumerate(b["images"]):
            recs.append({
                "url": url, "boat": label, "boat_type": btype,
                "boat_url": b.get("url", ""), "loc": loc, "slug": slug, "idx": i,
            })
    generic = [{"url": u, "boat": "", "boat_type": "boat", "boat_url": "",
                "loc": "", "slug": "generic", "idx": i}
               for i, u in enumerate(data.get("generic", []))]
    # Round-robin by image index so the flat fallback order alternates BOATS
    # (boatA#0, boatB#0, boatC#0, ... then #1s). Without this, one boat's 6 photos
    # sit consecutively and dominate the rotation for cities with no local boat.
    recs.sort(key=lambda r: (r["idx"], r["slug"]))
    return recs, generic


_RECS, _GENERIC = _records()


def _alt_caption(rec, location):
    """SEO-friendly alt text + human caption.

    location = the article's target city. We only claim a city when it is TRUE:
    a boat is described as being "in {city}" solely when the boat's real harvested
    location matches the article's city (or it is a generic shot). Otherwise we use
    neutral, accurate phrasing so we never assert a false location (protects E-E-A-T).
    """
    boat = rec["boat"]
    btype = rec["boat_type"]
    boat_loc = rec.get("loc", "")
    matches = bool(location) and boat_loc.lower() == location.lower()
    where = location if (matches or not boat) else ""
    if boat and where:
        alt = f"{boat} {btype} available to rent in {where} with BoatHire24"
        cap = f"{boat}: a {btype} you can charter in {where}."
    elif boat:
        alt = f"{boat} {btype} available for charter on BoatHire24"
        cap = f"{boat}, a {btype} you can charter through BoatHire24."
    elif where:
        alt = f"Boat rental and yacht charter in {where} with BoatHire24"
        cap = f"On the water in {where}."
    else:
        alt = "Boat rental and yacht charter with BoatHire24"
        cap = "A day on the water with BoatHire24."
    return _clean(alt), _clean(cap)


def pick_images(location: str, n: int = 2, seed: int = 0, prefer_type: str = None):
    """Pick n relevant images for an article targeting `location`.

    Order of preference: boats of `prefer_type` shot in `location`, then any boat
    in `location`, then boats of `prefer_type` anywhere, then any boat (rotated by
    seed so consecutive articles do not reuse the same photo), then generic shots.
    """
    location = _clean(location or "")
    loc_key = location.lower()
    pt = (prefer_type or "").lower().strip()

    def _is_type(r):
        return pt and pt in r["boat_type"].lower()

    in_loc = [r for r in _RECS if r["loc"].lower() == loc_key] if loc_key else []
    # Build a preference-ordered pool without duplicates.
    tiers = []
    if pt:
        tiers.append([r for r in in_loc if _is_type(r)])      # type + location
    tiers.append(in_loc)                                       # location
    if pt:
        tiers.append([r for r in _RECS if _is_type(r)])       # type anywhere
    tiers.append(_RECS)                                        # anything
    pool, seen_ids = [], set()
    for tier in tiers:
        for r in tier:
            rid = (r["slug"], r["idx"])
            if rid not in seen_ids:
                seen_ids.add(rid)
                pool.append(r)
    if not pool:
        pool = _GENERIC or _RECS
    total = len(pool)
    # Rotate the START within the relevant head (type+location / location block, or
    # the first ~12 records when the location has no boats) so consecutive articles
    # vary the photo WITHOUT falling out of the relevant tier.
    head = len([r for r in pool if r in in_loc]) if in_loc else min(total, 12)
    head = max(head, 1)
    start = seed % head
    seq = pool[start:] + pool[:start]
    out, used_boats = [], set()
    for rec in seq:
        if len(out) >= n:
            break
        if rec["slug"] in used_boats and len(out) > 0:
            continue
        used_boats.add(rec["slug"])
        alt, cap = _alt_caption(rec, location)
        out.append({"url": rec["url"], "alt": alt, "caption": cap,
                    "boat": rec["boat"], "boat_url": rec["boat_url"]})
    return out


def figure_html(img: dict) -> str:
    """Render a picked image as a telegraph/LiveJournal-safe <figure> block."""
    return (f'<figure><img src="{img["url"]}" alt="{img["alt"]}"/>'
            f'<figcaption>{img["caption"]}</figcaption></figure>')


if __name__ == "__main__":
    import sys
    loc = sys.argv[1] if len(sys.argv) > 1 else "Marbella"
    print(f"pool: {len(_RECS)} boat images, {len(_GENERIC)} generic")
    for im in pick_images(loc, n=3, seed=2):
        print(json.dumps(im, ensure_ascii=False, indent=1))
