#!/usr/bin/env python3
"""Add Andra's boathire24 Marbella boats that are missing from boatrentalinmarbella.

Reads .tmp/missing10.json (pulled from the boathire24 partner API), downloads &
resizes each boat's photos into the site's local srcset variants, and appends a
config/boats.json entry + a real-price tier for each. Idempotent: skips any slug
already present.

  python3 scripts/import_andra_boats.py
"""
from __future__ import annotations
import json, pathlib, re, io, urllib.request
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = json.loads((ROOT / ".tmp" / "missing10.json").read_text())
CFG_PATH = ROOT / "config" / "boats.json"
CFG = json.loads(CFG_PATH.read_text())
IMG_ROOT = ROOT / "site" / "img" / "boats"
UA = {"User-Agent": "Mozilla/5.0 (compatible; BoatRentalMarbella/1.0)"}

HERO_W = [600, 900, 1200, 1600]
GAL_W = [600, 900, 1200]

def slugify(name: str) -> str:
    s = name.lower().replace("—", " ").replace("(brp)", "")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return re.sub(r"-+", "-", s)

def fetch(url: str) -> bytes:
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read()

def save_variants(img: Image.Image, folder: pathlib.Path, base: str, widths: list[int]) -> list[list]:
    folder.mkdir(parents=True, exist_ok=True)
    if img.mode != "RGB":
        img = img.convert("RGB")
    out = []
    for w in widths:
        if img.width >= w:
            h = round(img.height * w / img.width)
            v = img.resize((w, h), Image.LANCZOS)
        else:
            v = img  # don't upscale
        p = folder / f"{base}-{w}.jpg"
        v.save(p, "JPEG", quality=82, optimize=True, progressive=True)
        out.append([f"/img/boats/{folder.name}/{base}-{w}.jpg", w])
    return out

# Premium-sounding features to surface as highlights, in priority order.
PRIORITY = ["Jacuzzi", "Beach club", "Sunken beach-club stern", "Flybridge", "Tender / dinghy",
            "En-suite cabins", "Swim platform & ladder", "Inflatable sea toys", "Paddleboard (SUP)",
            "Bluetooth sound system", "Air conditioning", "Sun pads", "Bimini / shade"]

def highlights_for(b: dict) -> list[str]:
    feats = b.get("features") or []
    picked = [f for f in PRIORITY if f in feats][:5]
    hl = []
    cabins = b.get("cabins")
    if cabins:
        hl.append(f"{cabins} en-suite cabins for overnight charter")
    for f in picked:
        if f == "Sunken beach-club stern": hl.append("Sunken beach-club stern for swim-platform days")
        elif f == "Jacuzzi": hl.append("Deck jacuzzi for sunset soaks")
        elif f == "Beach club": hl.append("Full beach club at the stern")
        elif f == "Flybridge": hl.append("Flybridge with bar and sunbeds")
        elif f == "Tender / dinghy": hl.append("Tender for beach-club drop-offs")
        elif f == "En-suite cabins": continue
        else: hl.append(f)
    hl.append(f"Departs Puerto Banús with a licensed skipper, fuel & drinks included")
    # de-dupe preserving order, cap 6
    seen, res = set(), []
    for h in hl:
        if h.lower() not in seen:
            seen.add(h.lower()); res.append(h)
    return res[:6]

def summary_for(b: dict) -> str:
    d = (b.get("description") or "").strip()
    d = d.replace("—", " — ")
    if "Marbella" not in d and "Costa del Sol" not in d:
        d += " Based in Puerto Banús, Marbella, with a licensed skipper on every charter."
    return d[:600]

existing = {x["slug"] for x in CFG["boats"]}
added = []
for b in SRC:
    slug = slugify(b["name"])
    if slug in existing:
        print("skip (exists):", slug); continue
    is_jet = b.get("type") == "jet_ski"
    folder = IMG_ROOT / slug
    imgs = b.get("images") or []

    hero_srcset, gallery_local = [], []
    if imgs:
        try:
            hero_img = Image.open(io.BytesIO(fetch(imgs[0])))
            hero_srcset = save_variants(hero_img, folder, "hero", HERO_W)
        except Exception as e:
            print("  hero fail", slug, e)
        for i, url in enumerate(imgs[1:], start=2):
            try:
                gi = Image.open(io.BytesIO(fetch(url)))
                ss = save_variants(gi, folder, f"g{i}", GAL_W)
                gallery_local.append({"src": ss[1][0] if len(ss) > 1 else ss[0][0],
                                       "srcset": ss, "alt": f"{b['name']} — Marbella charter"})
            except Exception as e:
                print("  gallery fail", slug, i, e)

    # real boathire24 price grid → tier
    tier_key = f"tier_{slug.replace('-', '_')}"
    prices = {f"{p['duration_hours']}h": int(p["price"]) for p in sorted(b.get("pricing", []), key=lambda p: p["duration_hours"])}
    CFG["hourly_price_tiers"][tier_key] = {
        "label": f"{b['name']} — {b.get('length_m')}m {'jet ski' if is_jet else 'motor yacht'}",
        "min_hours": b.get("min_hours") or 2,
        "prices": prices, "currency": "EUR",
    }

    entry = {
        "slug": slug, "name": b["name"],
        "tagline": b.get("tagline") or f"{b['name']} charter · Puerto Banús, Marbella",
        "model_year": b.get("model_year"),
        "builder": b.get("builder") or "",
        "type": "Jet ski" if is_jet else "Motor yacht",
        "length_m": b.get("length_m"),
        "capacity_pax": b.get("capacity") or 1,
        "departure_port": "Puerto Banús",
        "tier": tier_key,
        "summary": summary_for(b),
        "highlights": highlights_for(b),
    }
    if hero_srcset:
        entry["hero_local"] = hero_srcset[-1][0]
        entry["hero_local_srcset"] = hero_srcset
        entry["hero_local_alt"] = f"{b['name']} {'jet ski' if is_jet else 'motor yacht'} charter off Marbella, Puerto Banús"
    if gallery_local:
        entry["gallery_local"] = gallery_local

    CFG["boats"].append(entry)
    added.append(slug)
    print("added:", slug, f"({len(hero_srcset and [1] or [])} hero, {len(gallery_local)} gallery, prices {prices})")

CFG_PATH.write_text(json.dumps(CFG, indent=2, ensure_ascii=False))
print(f"\nDone. Added {len(added)}: {', '.join(added)}")
