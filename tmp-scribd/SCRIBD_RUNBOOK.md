# Scribd Upload Runbook

Publish all 30 PDFs in `tmp-scribd/pdfs/` to Scribd (account **info@boathire24.com**),
each with the SEO title + description from `tmp-scribd/scribd_manifest.json`, all
linking back to boathire24.com. **Run this in a SUPERVISED Claude Code session.**

## Why it must be supervised
`file_upload` (Claude-in-Chrome) only accepts files from a folder the user has
**connected**. Connecting one needs the `request_directory` approval dialog, which
**Auto / Unsupervised mode disables**. In a supervised session the dialog appears
and you approve it once. Everything else already works (tested live):
Chrome is connected, logged into Scribd, and the upload page + file input are reachable.

## To start (what the user does)
1. Turn OFF Auto Mode so approval prompts appear (this is the only thing blocking us).
2. In this project, say: **"Run the Scribd runbook — upload everything to Scribd."**

## What I (Claude) then do
1. `request_directory("/Users/master/boat-rental-marbella/tmp-scribd/pdfs")` → you click Approve (once).
2. Get the queue: `python3 scripts/scribd_state.py next 30` (priority order; already-published are skipped).
3. For EACH document `{id, pdf, title, description, category_hint, doc_type}`:
   a. `navigate` Chrome → `https://www.scribd.com/upload-document`
   b. `find` the file input → `file_upload` the `pdf` path
   c. wait for the page to process the file
   d. set **Title** = manifest `title`
   e. set **Description** = manifest `description`
   f. set **Category** per `category_hint` (Travel / Sports & Recreation / Business)
   g. set visibility **Public**, click **Publish / Done**
   h. capture the published URL
   i. `python3 scripts/scribd_state.py mark <id> <url>`
4. `python3 scripts/scribd_state.py status` → confirm 30/30 published.

## Assets (all ready, no rebuild needed)
- PDFs: `tmp-scribd/pdfs/*.pdf` (30: 18 boat spec sheets, 7 Marbella guides, 5 research papers)
- Metadata: `tmp-scribd/scribd_manifest.json` (id, pdf path, title, description, category_hint, doc_type)
- State/queue: `scripts/scribd_state.py` (`next N` | `mark <id> <url>` | `status`)

## Notes
- I will pause before the first Publish to show you one filled-in upload, then continue the batch on your OK.
- If Scribd ever shows a CAPTCHA, I cannot solve it — you click it, then I continue.
- Publishing is irreversible-ish (public docs); the manifest descriptions are reviewed
  and contain only boathire24.com links, no false claims.
