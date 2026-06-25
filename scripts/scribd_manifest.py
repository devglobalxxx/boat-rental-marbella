#!/usr/bin/env python3
"""Build a Scribd upload manifest from tmp-scribd content JSONs.

For each generated PDF, emit the title + description to paste into Scribd's
metadata form during upload. Descriptions carry the SEO keywords and both
site URLs (Scribd descriptions are indexed and the profile links are followed
by readers, not crawlers, so the URLs are written out in plain text).
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
TMP = ROOT / "tmp-scribd"
OUT = TMP / "scribd_manifest.json"

CATEGORY = {
    "spec": "Sports & Recreation",
    "research": "Business",
    "guide": "Travel",
}


def describe(doc_id: str, c: dict) -> dict:
    doc_type = c.get("doc_type", "guide")
    title = c.get("title", doc_id)
    subtitle = c.get("subtitle", "")
    boat_url = (c.get("links") or {}).get("boat_url")

    if doc_type == "spec":
        desc = (
            f"{title} - official specification sheet and 2026 charter rates. {subtitle} "
            "Full particulars, on-board highlights, all-inclusive pricing and departure "
            "information for this boat, chartered from Puerto Banus, Marbella with licensed "
            "skipper, fuel and drinks included. "
        )
    elif doc_type == "research":
        desc = (
            f"{title}. {subtitle} "
            "Original research by BoatHire24 using real fleet, pricing and operational data "
            "from the Costa del Sol day-charter market. "
        )
    else:
        desc = (
            f"{title}. {subtitle} "
            "A practical, skipper-written guide for boat charter guests in Marbella and the "
            "Costa del Sol, published by BoatHire24. "
        )

    desc += "Book online at boatrentalinmarbella.com. Boat owners list free at boathire24.com."
    if boat_url:
        desc += f" Boat page: {boat_url}"

    return {
        "id": doc_id,
        "pdf": str(TMP / "pdfs" / f"{doc_id}.pdf"),
        "title": title if len(title) <= 100 else title[:97] + "...",
        "description": desc,
        "category_hint": CATEGORY[doc_type],
        "doc_type": doc_type,
    }


def main() -> None:
    items = []
    for cj in sorted((TMP / "content").glob("*.json")):
        doc_id = cj.stem
        pdf = TMP / "pdfs" / f"{doc_id}.pdf"
        if not pdf.exists():
            continue
        with open(cj) as f:
            items.append(describe(doc_id, json.load(f)))
    with open(OUT, "w") as f:
        json.dump(items, f, indent=1, ensure_ascii=False)
    print(f"{len(items)} docs -> {OUT}")
    for it in items:
        print(f"  [{it['doc_type']:8}] {it['title']}")


if __name__ == "__main__":
    main()
