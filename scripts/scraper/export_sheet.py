#!/usr/bin/env python3
"""Export the BoatHire24 listing-outreach campaign to CSV (+ a Google Sheet).

The CSV is always written. A Google Sheet is also created when a valid OAuth token
is already present (~/.boathire24_sheets_token.json) — this never opens a browser, so
it is safe to run head-less / from cron. If the token is missing or unrefreshable it
just prints how to enable Sheets and leaves you the CSV.

Run from project root:  python3 -m scripts.scraper.export_sheet
"""
from __future__ import annotations
import sqlite3, csv, json, pathlib, datetime

ROOT = pathlib.Path(__file__).resolve().parents[2]
DB = ROOT / "data" / "scraper" / "leads.db"
CSV_OUT = ROOT / "data" / "scraper" / "boathire24_outreach_export.csv"
STATE_FILE = ROOT / "config" / "scraper_sheet.json"

COLS = ["domain", "email", "lang", "subject", "sent_at", "status", "replied",
        "reply_class", "followup_sent_at", "interested_reply_sent_at"]
HEADER = ["Domain", "Email", "Lang", "Subject", "Initial sent", "Status",
          "Replied", "Reply type", "Follow-up sent", "Interested-reply sent"]


def fetch():
    db = sqlite3.connect(DB)
    rows = [[("" if v is None else v) for v in r]
            for r in db.execute(f"SELECT {','.join(COLS)} FROM outreach ORDER BY sent_at")]
    g = lambda s: db.execute(s).fetchone()[0]
    summ = {
        "contacted": g("SELECT COUNT(*) FROM outreach WHERE status='sent'"),
        "followed_up": g("SELECT COUNT(*) FROM outreach WHERE followup_sent_at IS NOT NULL"),
        "replied": g("SELECT COUNT(*) FROM outreach WHERE replied=1"),
        "failed": g("SELECT COUNT(*) FROM outreach WHERE status='failed'"),
    }
    db.close()
    return rows, summ


def write_csv(rows):
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(CSV_OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        w.writerows(rows)
    return CSV_OUT


def _creds_noninteractive():
    """Valid creds from the saved token, or None. Never opens a browser."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from scripts.scraper.sheets import TOKEN_PATH, SCOPES
    except Exception:
        return None
    if not TOKEN_PATH.exists():
        return None
    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json())
            return creds
        except Exception:
            return None
    return None


def to_sheet(rows, summ):
    creds = _creds_noninteractive()
    if not creds:
        return None
    from googleapiclient.discovery import build
    svc = build("sheets", "v4", credentials=creds, cache_discovery=False)
    title = "BoatHire24 Outreach " + datetime.date.today().isoformat()
    sid = svc.spreadsheets().create(
        body={"properties": {"title": title}, "sheets": [{"properties": {"title": "Outreach"}}]},
        fields="spreadsheetId").execute()["spreadsheetId"]
    values = [
        ["BoatHire24 listing outreach — exported " + datetime.date.today().isoformat()],
        [f"Contacted: {summ['contacted']}", f"Followed up: {summ['followed_up']}",
         f"Replied: {summ['replied']}", f"Failed: {summ['failed']}"],
        [],
        HEADER,
    ] + rows
    svc.spreadsheets().values().update(
        spreadsheetId=sid, range="Outreach!A1", valueInputOption="RAW",
        body={"values": values}).execute()
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps({"spreadsheet_id": sid}, indent=2))
    return f"https://docs.google.com/spreadsheets/d/{sid}"


def main():
    rows, summ = fetch()
    print(f"CSV written: {write_csv(rows)}  ({len(rows)} rows)")
    print(f"Summary: contacted={summ['contacted']} followed_up={summ['followed_up']} "
          f"replied={summ['replied']} failed={summ['failed']}")
    try:
        url = to_sheet(rows, summ)
    except Exception as e:
        url = None
        print(f"Sheet step skipped: {e}")
    if url:
        print(f"Google Sheet: {url}")
    else:
        print("No Google Sheet created (no usable OAuth token). The CSV above is ready.")
        print("Enable Sheets later with: python3 -m scripts.scraper.sheets auth")


if __name__ == "__main__":
    main()
