"""Sync outreach status into the 'Outreach' tab of the master leads sheet."""
from __future__ import annotations
from . import store, sheets, followup

HEADER = ["domain","email","company","city","country","lang","sent_at",
          "replied","reply_class","reply_snippet","followup_sent_at","subject"]

def main():
    con = store.connect(); followup.ensure_schema(con)
    rows = con.execute("""SELECT o.domain,o.email,l.company,l.city,l.country,o.lang,o.sent_at,
        o.replied,o.reply_class,o.reply_snippet,o.followup_sent_at,o.subject
        FROM outreach o LEFT JOIN leads l ON l.domain=o.domain
        WHERE o.status='sent' ORDER BY o.replied DESC, o.sent_at DESC""").fetchall()
    out = [HEADER]
    for r in rows:
        d,e,co,ci,cn,lang,sent,rep,kl,sn,fu,subj = r
        out.append([d or "",e or "",co or "",ci or "",cn or "",lang or "",sent or "",
                    "yes" if rep else "",kl or "",(sn or "")[:200],fu or "",subj or ""])
    sid = sheets.ensure_sheet(); svc = sheets.service()
    meta = svc.spreadsheets().get(spreadsheetId=sid).execute()
    tabs = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}
    if "Outreach" not in tabs:
        svc.spreadsheets().batchUpdate(spreadsheetId=sid, body={"requests":[{"addSheet":{"properties":{"title":"Outreach"}}}]}).execute()
        meta = svc.spreadsheets().get(spreadsheetId=sid).execute()
        tabs = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}
    sheet_id = tabs["Outreach"]
    svc.spreadsheets().values().clear(spreadsheetId=sid, range="Outreach!A:Z").execute()
    svc.spreadsheets().values().update(spreadsheetId=sid, range="Outreach!A1",
        valueInputOption="RAW", body={"values": out}).execute()
    # header format + conditional colors
    def rgb(r,g,b): return {"red":r/255,"green":g/255,"blue":b/255}
    n=len(out); nc=len(HEADER); rng={"sheetId":sheet_id,"startRowIndex":1,"endRowIndex":n,"startColumnIndex":0,"endColumnIndex":nc}
    def rule(formula,color): return {"addConditionalFormatRule":{"rule":{"ranges":[rng],"booleanRule":{"condition":{"type":"CUSTOM_FORMULA","values":[{"userEnteredValue":formula}]},"format":{"backgroundColor":color}}},"index":0}}
    reqs=[
      {"repeatCell":{"range":{"sheetId":sheet_id,"startRowIndex":0,"endRowIndex":1,"startColumnIndex":0,"endColumnIndex":nc},
        "cell":{"userEnteredFormat":{"backgroundColor":rgb(7,16,30),"textFormat":{"foregroundColor":rgb(201,168,78),"bold":True,"fontSize":11}}},
        "fields":"userEnteredFormat(backgroundColor,textFormat)"}},
      {"updateSheetProperties":{"properties":{"sheetId":sheet_id,"gridProperties":{"frozenRowCount":1,"frozenColumnCount":2}},"fields":"gridProperties.frozenRowCount,gridProperties.frozenColumnCount"}},
      rule('=$I2="interested"', rgb(198,239,206)),
      rule('=$I2="stop"', rgb(255,199,206)),
      rule('=$I2="reply"', rgb(255,235,156)),
      rule('=OR($I2="ooo",$I2="bounce")', rgb(230,230,230)),
      rule('=AND($H2="",$K2<>"")', rgb(204,224,245)),
    ]
    try: svc.spreadsheets().batchUpdate(spreadsheetId=sid, body={"requests":reqs}).execute()
    except Exception: pass
    print(f"Wrote {n-1} rows to Outreach tab.")
    print(f"Sheet: {sheets.url()}#gid={sheet_id}")

if __name__ == "__main__":
    main()
