#!/usr/bin/env python3
"""Scribd daily-drip state machine.

Single source of truth for the Scribd publishing queue. Reads the manifest
(tmp-scribd/scribd_manifest.json, rebuilt by scribd_manifest.py) and tracks
which documents have been published in config/scribd_published.json.

Each day we publish 2-3 *unique* documents, leading with boat spec sheets
(one distinct boat each) and interleaving the occasional research paper /
guide so the feed stays varied.

Commands:
  python3 scripts/scribd_state.py next [N]        # next N unpublished (default 3)
  python3 scripts/scribd_state.py mark <id> <url> # record a publish
  python3 scripts/scribd_state.py status          # progress summary
"""
import json
import pathlib
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "tmp-scribd" / "scribd_manifest.json"
STATE = ROOT / "config" / "scribd_published.json"

# Publish order: lead with the marquee boats (one unique boat per doc), drop a
# research paper / guide in every few days so the profile is not all spec sheets.
# Any manifest id not listed here is appended at the end (spec sheets first).
ORDER = [
    "spec-mangusta-80",          # 24m flagship, the headline boat
    "spec-ferretti-94",          # 29m, largest
    "research-fleet",            # case study referencing the whole fleet
    "spec-canados-86",
    "spec-pershing-46",
    "guide-best-anchorages-marbella",
    "spec-azimut-58",
    "spec-maiora-26m",
    "research-pricing",
    "spec-astondoa-40",
    "spec-fairline-targa-12m",
    "guide-full-day-itinerary-marbella",
    "spec-azimut-39",
    "spec-k80",
    "research-anchorages",
    "spec-lagoon-380",
    "spec-bandido",
    "guide-dolphin-watching-marbella",
    "spec-mangusta-80-white",
    "spec-red-tide-fishing-boat",
    "research-seasonality",
    "spec-mangusta-80-grey",
    "spec-dubhe",
    "guide-best-snorkel-spots-marbella",
    "spec-mariah-sx21",
    "spec-speedboat",
    "research-regulation",
    "guide-best-beaches-by-boat-marbella",
    "guide-best-month-to-rent-a-boat-in-marbella",
    "guide-how-much-does-it-cost-to-rent-a-boat-in-marbella",
    "guide-gibraltar-day-trip-by-boat",
    "guide-marbella-restaurants-by-boat",
    "guide-catamaran-vs-motor-yacht-marbella-families",
]


def load_manifest() -> dict:
    with open(MANIFEST) as f:
        return {d["id"]: d for d in json.load(f)}


def load_state() -> dict:
    if STATE.exists():
        with open(STATE) as f:
            return json.load(f)
    return {"published": {}}


def save_state(state: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE, "w") as f:
        json.dump(state, f, indent=1, ensure_ascii=False)


def ordered_ids(man: dict) -> list:
    seen = set()
    out = []
    for i in ORDER:
        if i in man and i not in seen:
            out.append(i)
            seen.add(i)
    # append any manifest docs not in ORDER (spec sheets first, then the rest)
    rest = [i for i in man if i not in seen]
    rest.sort(key=lambda i: (0 if man[i]["doc_type"] == "spec" else 1, i))
    return out + rest


def cmd_next(n: int) -> None:
    man = load_manifest()
    state = load_state()
    done = set(state["published"])
    queue = [i for i in ordered_ids(man) if i not in done]
    batch = queue[:n]
    if not batch:
        print("QUEUE EMPTY - every document has been published.")
        return
    out = [man[i] for i in batch]
    print(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"\n# {len(batch)} to publish, {len(queue) - len(batch)} remaining after this batch",
          file=sys.stderr)


def cmd_mark(doc_id: str, url: str) -> None:
    state = load_state()
    state["published"][doc_id] = {
        "url": url,
        "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    save_state(state)
    print(f"marked {doc_id} -> {url} ({len(state['published'])} published total)")


def cmd_status() -> None:
    man = load_manifest()
    state = load_state()
    done = state["published"]
    queue = [i for i in ordered_ids(man) if i not in done]
    print(f"Published: {len(done)} / {len(man)}   Remaining: {len(queue)}")
    if done:
        print("\nPublished:")
        for i, meta in done.items():
            print(f"  {i:45} {meta.get('url','')}")
    print("\nNext up:")
    for i in queue[:6]:
        print(f"  {i:45} {man[i]['title']}")


def main() -> None:
    args = sys.argv[1:]
    if not args:
        cmd_status()
        return
    cmd = args[0]
    if cmd == "next":
        cmd_next(int(args[1]) if len(args) > 1 else 3)
    elif cmd == "mark":
        cmd_mark(args[1], args[2])
    elif cmd == "status":
        cmd_status()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
