"""Google Sheets writer — reuses the project's Desktop OAuth client."""
from __future__ import annotations
import os, pathlib, json, sys

SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive.file"]
TOKEN_PATH = pathlib.Path.home() / ".boathire24_sheets_token.json"
STATE_FILE = pathlib.Path(__file__).resolve().parents[2] / "config" / "scraper_sheet.json"

HEADER = ["domain","company","city","country","emails","phones","contact_form_url",
          "source","first_seen","confidence","outreach_status","notes"]

def _load_dotenv():
    env_path = pathlib.Path(__file__).resolve().parents[2] / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

def get_credentials(force=False):
    _load_dotenv()
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    creds = None
    if not force and TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token and not force:
            creds.refresh(Request())
        else:
            cp = os.environ.get("GOOGLE_CREDENTIALS")
            if not cp or not pathlib.Path(cp).exists():
                sys.exit("ERROR: GOOGLE_CREDENTIALS not set/missing in .env")
            flow = InstalledAppFlow.from_client_secrets_file(cp, SCOPES)
            creds = flow.run_local_server(port=8766, prompt="consent")
        TOKEN_PATH.write_text(creds.to_json())
    return creds

def service():
    from googleapiclient.discovery import build
    return build("sheets", "v4", credentials=get_credentials(), cache_discovery=False)

def _state():
    if STATE_FILE.exists(): return json.loads(STATE_FILE.read_text())
    return {}

def _save_state(s):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(s, indent=2))

def ensure_sheet(title="BoatHire24 Leads"):
    s = _state()
    if s.get("spreadsheet_id"): return s["spreadsheet_id"]
    svc = service()
    res = svc.spreadsheets().create(
        body={"properties": {"title": title}, "sheets": [{"properties": {"title": "Leads"}}]},
        fields="spreadsheetId").execute()
    sid = res["spreadsheetId"]
    svc.spreadsheets().values().update(spreadsheetId=sid, range="Leads!A1",
        valueInputOption="RAW", body={"values": [HEADER]}).execute()
    s["spreadsheet_id"] = sid; _save_state(s)
    return sid

def append_rows(rows):
    if not rows: return 0
    sid = ensure_sheet(); svc = service()
    svc.spreadsheets().values().append(spreadsheetId=sid, range="Leads!A1",
        valueInputOption="RAW", insertDataOption="INSERT_ROWS", body={"values": rows}).execute()
    return len(rows)

def url():
    sid = _state().get("spreadsheet_id")
    return f"https://docs.google.com/spreadsheets/d/{sid}" if sid else None

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "url"
    if cmd == "auth": get_credentials(force=True); print("ok", TOKEN_PATH)
    elif cmd == "create": print(ensure_sheet())
    else: print(url())
