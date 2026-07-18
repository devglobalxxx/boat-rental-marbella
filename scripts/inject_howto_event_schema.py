#!/usr/bin/env python3
"""Strip previously injected HowTo/Event JSON-LD blocks (cleanup-only).

The HowTo injection was retired because Google dropped HowTo rich results in
2023. The Event injection was retired because it marked up third-party events
(Starlite, F1 GP, ferias) with the operator as organizer plus charter Offers —
manual-action-grade structured data.

The old script wrapped everything in one marker pair per page, so this pass
only removes those marker-wrapped blocks; visible blog content is untouched.
Kept in the deploy chain so committed HTML gets (and stays) clean. Idempotent.
"""
from __future__ import annotations
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "site"

BEGIN = "<!-- ai-howto-event:begin -->"
END = "<!-- ai-howto-event:end -->"
PAT = re.compile(re.escape(BEGIN) + r"[\s\S]*?" + re.escape(END) + r"\n?")

def main():
    n = 0
    for p in SITE_DIR.rglob("index.html"):
        s = p.read_text()
        if BEGIN not in s:
            continue
        p.write_text(PAT.sub("", s))
        n += 1
    print(f"inject_howto_event_schema: stripped HowTo/Event blocks from {n} page(s)")

if __name__ == "__main__":
    main()
