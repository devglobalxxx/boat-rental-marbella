#!/usr/bin/env python3
"""One-off: send the two guest-post pitch emails (Boatbloggings + Nautic Magazine).

Reads RESEND_API_KEY from the repo .env. Sends from the same identity as the
existing outreach engine (scripts/scraper/outreach.py). Safe to re-run only if
you actually want the pitches sent again — there is no dedup ledger here.
"""
import json, pathlib, urllib.request, urllib.error

ROOT = pathlib.Path(__file__).resolve().parents[1]
key = None
for line in (ROOT / ".env").read_text().splitlines():
    if line.startswith("RESEND_API_KEY="):
        key = line.split("=", 1)[1].strip()
if not key:
    raise SystemExit("RESEND_API_KEY not found in .env")

FROM = "Andra Kiirkivi <info@boathire24.com>"
REPLY_TO = "info@boathire24.com"

pitches = [
    {
        "to": ["guestblogger@boatbloggings.com"],
        "subject": "Guest post proposal — transparent Marbella charter pricing breakdown",
        "text": """Hi team,

I run Boat Rental Marbella (https://boatrentalinmarbella.com), a Puerto Banus-based charter operator with a fleet ranging from day boats to a 29m Mefasa 90. I'd like to contribute a piece for your guest blogger program:

"What a Yacht Charter in Marbella Actually Costs in 2026" — a transparent, boat-class-by-boat-class price breakdown (from EUR 749/2h on a 40ft flybridge to EUR 4,719/4h on an 80ft with a jet ski included), what's typically bundled (skipper, fuel, drinks, insurance, IVA) versus billed separately, and how Marbella pricing compares to Ibiza and Cannes.

Happy to write to your house style and length, and I can supply original fleet photography. Let me know if this fits the fortnightly slot.

Best regards,
Andra Kiirkivi
Boat Rental Marbella
https://boatrentalinmarbella.com""",
    },
    {
        "to": ["write@nauticmag.com"],
        "subject": "Guest author application — Marbella charter market",
        "text": """Hello,

I operate Boat Rental Marbella (https://boatrentalinmarbella.com) out of Puerto Banus. I'd like to apply as a guest author with a piece on Puerto Banus as a charter departure point — comparing it with Marbella Marina and Sotogrande for different trip types (sunset cruises vs. full-day Gibraltar runs vs. group charters), grounded in real fleet specs and pricing rather than generic marketing copy.

I can also supply original photography from our fleet (Sunseeker, Princess, Mangusta, Pershing among others). Open to your topic suggestions if there's a gap in your nautical lifestyle coverage you'd rather fill.

Best regards,
Andra Kiirkivi
Boat Rental Marbella
https://boatrentalinmarbella.com""",
    },
]

for p in pitches:
    body = json.dumps({
        "from": FROM,
        "to": p["to"],
        "reply_to": REPLY_TO,
        "subject": p["subject"],
        "text": p["text"],
    }).encode()
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as r:
            resp = json.load(r)
            print(f"SENT to {p['to'][0]}: id={resp.get('id')}")
    except urllib.error.HTTPError as e:
        print(f"FAILED to {p['to'][0]}: {e.code} {e.read().decode()[:300]}")
