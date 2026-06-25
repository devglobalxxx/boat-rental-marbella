#!/usr/bin/env python3
"""
BoatHire24 branded PDF builder — Design A: "Nautical Classic"
Deep navy + gold/brass, serif display headings, elegant rules, yacht-brochure feel.

Usage:
    python3 build_pdf.py <content.json> <out.pdf>

Builds an HTML file next to <out.pdf> (kept on disk for debugging) and renders
it to A4 PDF with Chrome headless. Stdlib only.

Content JSON schema accepted:
{
  "doc_type": "spec" | "research" | "guide",
  "title": str, "subtitle": str, "author": str, "date": str,
  "cover_image": abs path | null,
  "spec_table": [[label, value], ...] | null,
  "sections": [{"heading": str, "html": str,
                "image": abs path | null, "image_caption": str | null}],
  "callout": {"heading": str, "html": str} | null,
  "links": {"primary": str, "boat_url": str | null}
}
"""

import html
import json
import pathlib
import re
import subprocess
import sys

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

PUBLISHER_LOGO = "/Users/master/boat-rental-platform/public/brand-logo.jpg"
FLEET_LOGO = "/Users/master/boat-rental-marbella/site/img/logo-640.png"

DOC_TYPE_LABELS = {
    "spec": "Vessel Specification",
    "research": "Research Report",
    "guide": "Charter Guide",
}

SPEC_TABLE_TITLE = "Principal Particulars"


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def file_uri(path):
    """Absolute file:// URI for an image path, or None if missing."""
    if not path:
        return None
    p = pathlib.Path(path).expanduser()
    if not p.is_absolute():
        p = p.resolve()
    if not p.is_file():
        print(f"WARN: image not found, skipping: {p}", file=sys.stderr)
        return None
    return p.as_uri()


CSS = """
:root {
  --navy:      #0e2438;
  --navy-deep: #08182a;
  --gold:      #b9924b;
  --gold-dark: #8a6c33;
  --gold-light:#d4b06a;
  --gold-pale: #e8d8af;
  --ivory:     #f7f2e6;
  --paper:     #fdfbf5;
  --ink:       #22303e;
  --muted:     #5d6a76;
  --hairline:  #d9cdaf;
  --row-tint:  #f5efdf;
}
* { -webkit-print-color-adjust: exact; print-color-adjust: exact;
    box-sizing: border-box; }
@page { size: A4; margin: 0; }
html, body { margin: 0; padding: 0; }
body {
  background: var(--paper);
  color: var(--ink);
  font-family: Georgia, 'Palatino Linotype', Palatino, 'Times New Roman', serif;
  font-size: 10.5pt;
  line-height: 1.62;
}
.display { font-family: Didot, 'Didot LT STD', 'Playfair Display', Georgia,
           'Times New Roman', serif; }
.caps { font-family: Optima, 'Avenir Next', 'Gill Sans', 'Trebuchet MS',
        sans-serif; text-transform: uppercase; }

/* ---------------- Cover ---------------- */
.cover {
  position: relative;
  width: 210mm; height: 297mm;
  overflow: hidden;
  background: var(--navy-deep);
  page-break-after: always;
}
.cover-img {
  position: absolute; inset: 0;
  width: 100%; height: 100%;
  object-fit: cover;
  object-position: 24% center;  /* centres the yacht's full profile in the A4 crop */
}
.cover-veil {
  position: absolute; inset: 0;
  background:
    linear-gradient(to top, rgba(11,26,46,0.92),
                    rgba(11,26,46,0.86) 30%, transparent 55%),
    linear-gradient(180deg,
      rgba(8,24,42,0.62) 0%,
      rgba(8,24,42,0.20) 26%,
      rgba(8,24,42,0.12) 50%,
      rgba(8,24,42,0.00) 62%);
}
.cover-veil.no-img {
  background:
    radial-gradient(120mm 90mm at 50% 26%, rgba(185,146,75,0.20), transparent 70%),
    linear-gradient(180deg, #122c46 0%, #0a1d33 55%, #071426 100%);
}
.cover-top {
  position: absolute; top: 13mm; left: 16mm; right: 16mm;
  display: flex; align-items: center; justify-content: space-between;
}
.brand-lockup { display: flex; align-items: center; gap: 4.5mm; }
.logo-chip {
  background: #ffffff;
  border: 1px solid var(--gold);
  border-radius: 1.2mm;
  padding: 2mm;
  line-height: 0;
}
.logo-chip img { display: block; height: 13mm; width: 13mm;
                 object-fit: cover; border-radius: 0.7mm; }
.brand-name {
  color: var(--ivory); font-size: 13pt; letter-spacing: 0.30em;
  line-height: 1.25;
}
.brand-tag {
  color: var(--gold-pale); font-size: 6.4pt; letter-spacing: 0.26em;
  margin-top: 1mm;
}
.doc-type-flag {
  text-align: right;
  color: var(--gold-light);
  font-size: 7.5pt; letter-spacing: 0.34em;
  border-top: 0.7pt solid var(--gold);
  border-bottom: 0.7pt solid var(--gold);
  padding: 2.2mm 0 2mm 0;
}
.cover-main {
  position: absolute; left: 16mm; right: 16mm; bottom: 34mm;
}
.cover-rule {
  display: flex; align-items: center; gap: 4mm;
  margin-bottom: 5mm;
}
.cover-rule .line { flex: 0 0 22mm; height: 0; border-top: 0.8pt solid var(--gold); }
.cover-rule .word {
  color: var(--gold-light); font-size: 8pt; letter-spacing: 0.42em;
  white-space: nowrap;
  text-shadow: 0 1px 5px rgba(5,14,26,0.65);
}
.cover-title {
  color: #fdfaf2;
  font-size: 44pt; line-height: 1.05;
  font-weight: 600;
  margin: 0 0 4mm 0;
  text-shadow: 0 1px 8px rgba(5,14,26,0.55);
}
.cover-subtitle {
  color: var(--gold-pale);
  font-style: italic;
  font-size: 13pt; line-height: 1.45;
  margin: 0 0 7mm 0;
  max-width: 150mm;
  text-shadow: 0 1px 6px rgba(5,14,26,0.6);
}
.cover-meta {
  color: rgba(247,242,230,0.92);
  font-size: 7.6pt; letter-spacing: 0.22em;
}
.cover-meta .dot { color: var(--gold-light); padding: 0 2.2mm; }
.fleet-strip {
  margin-top: 8mm;
  display: flex; align-items: center; gap: 4mm;
}
.fleet-strip .logo-chip img { height: 9mm; width: auto; }
.fleet-label {
  color: rgba(247,242,230,0.85); font-size: 6.6pt; letter-spacing: 0.30em;
}

/* ------------- Repeating footer ------------- */
.runfoot {
  position: fixed; left: 0; right: 0; bottom: 0;
  height: 12mm;
  background: var(--ivory);
  border-top: 1pt solid var(--gold);
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 16mm;
  font-size: 6.8pt; letter-spacing: 0.12em;
  color: var(--navy);
}
.runfoot b { letter-spacing: 0.22em; font-weight: 600; }
.runfoot .gold { color: var(--gold-dark); }
.runfoot a { color: var(--navy); text-decoration: none; }

/* ------------- Paged content scaffold ------------- */
table.paged { width: 100%; border-collapse: collapse; }
table.paged > thead td { height: 15mm; padding: 0; }
table.paged > tfoot td { height: 17mm; padding: 0; }
table.paged > tbody > tr > td { padding: 0 18mm; }

/* ------------- Sections ------------- */
.sec { margin: 0 0 8mm 0; }
.sec-head {
  break-after: avoid-page; page-break-after: avoid;
  break-inside: avoid; page-break-inside: avoid;
  margin: 0 0 4.5mm 0;
}
.sec-kicker {
  color: var(--gold-dark); font-size: 7pt; letter-spacing: 0.38em;
  margin-bottom: 1.6mm;
}
.sec-head h2 {
  color: var(--navy);
  font-size: 18.5pt; font-weight: 400; line-height: 1.2;
  margin: 0 0 2.6mm 0;
}
.sec-head .rules { position: relative; height: 2.4mm; }
.sec-head .rules .thin {
  position: absolute; left: 0; right: 0; top: 1mm;
  border-top: 0.6pt solid var(--hairline);
}
.sec-head .rules .thick {
  position: absolute; left: 0; top: 0; width: 26mm;
  border-top: 2.2pt solid var(--gold);
}
.sec-body p { margin: 0 0 3.4mm 0; }
.sec-body p:last-child { margin-bottom: 0; }
.sec-body ol { margin: 0 0 3.4mm 0; padding-left: 5.5mm; }
.sec-body ul { margin: 0 0 3.4mm 0; padding-left: 1mm; }
.sec-body li { margin-bottom: 1.6mm; break-inside: avoid; page-break-inside: avoid;
               -webkit-column-break-inside: avoid; }
.sec-body ul.cols2 { columns: 2; column-gap: 9mm;
                     break-inside: avoid; page-break-inside: avoid; }
.sec-body ul > li {
  list-style: none;
  padding-left: 1.1em; text-indent: -1.1em;  /* hanging indent: wraps align under text */
}
.sec-body ul > li::before {
  content: "\\2726";            /* four-pointed star, brass compass point */
  display: inline-block; width: 1.44em; text-indent: 0;
  color: var(--gold); font-size: 8pt;       /* 1.44em @8pt == 1.1em @10.5pt */
}
.sec-body a { color: var(--navy); text-decoration: none;
              border-bottom: 0.6pt solid var(--gold); }
.sec-body strong { color: var(--navy); }

/* generic tables inside section html */
.sec-body table {
  width: 100%; border-collapse: collapse;
  margin: 1mm 0 4mm 0;
  break-inside: avoid; page-break-inside: avoid;
  font-size: 9.8pt;
}
.sec-body th {
  background: var(--navy); color: var(--ivory);
  font-family: Optima, 'Avenir Next', 'Gill Sans', 'Trebuchet MS', sans-serif;
  text-transform: uppercase; letter-spacing: 0.16em;
  font-size: 7.4pt; font-weight: 500;
  text-align: left; padding: 2.6mm 3.5mm;
  border-bottom: 1.4pt solid var(--gold);
}
.sec-body td {
  padding: 2.2mm 3.5mm;
  border-bottom: 0.6pt solid var(--hairline);
  color: var(--ink);
}
.sec-body td, .sec-body th { font-variant-numeric: tabular-nums; }
.sec-body td:not(:first-child),
.sec-body th:not(:first-child) { text-align: right; }
.sec-body tr:nth-child(even) td { background: var(--row-tint); }
.sec-body td:first-child { color: var(--navy); }
.sec-body tr.best td { background: rgba(212,175,55,0.12); }
.sec-body tr.best td:first-child { color: var(--navy); font-weight: 600; }
.best-tag {
  display: inline-block;
  font-family: Optima, 'Avenir Next', 'Gill Sans', 'Trebuchet MS', sans-serif;
  font-variant-caps: small-caps; text-transform: lowercase;
  font-size: 7.6pt; font-weight: 600; letter-spacing: 0.14em;
  color: var(--gold-dark);
  border: 0.6pt solid var(--gold);
  border-radius: 1mm;
  padding: 0.2mm 1.6mm;
  margin-left: 2.2mm;
  white-space: nowrap;
  vertical-align: 0.2mm;
}

/* ------------- Figures ------------- */
figure.plate {
  break-inside: avoid; page-break-inside: avoid;
  margin: 5mm 0 2mm 0;
  background: #ffffff;
  border: 0.7pt solid var(--gold-light);
  padding: 2.6mm;
}
figure.plate img {
  display: block; width: 100%; height: 78mm; object-fit: cover;
}
figure.plate figcaption {
  text-align: center;
  font-style: italic;
  font-size: 8.4pt; color: var(--muted);
  padding: 2.4mm 2mm 0.6mm 2mm;
}
figure.plate figcaption::before {
  content: "\\25C6\\00a0"; color: var(--gold); font-size: 6pt;
}

/* ------------- Spec table (2-column grid: two lbl/val pairs per row) ------------- */
.spec-block { margin: 0 0 8mm 0; }
table.spec {
  width: 100%; border-collapse: collapse;
  border-top: 1.6pt solid var(--navy);
  border-bottom: 1.6pt solid var(--navy);
}
table.spec td { padding: 1.7mm 1.5mm; border-bottom: 0.6pt solid var(--hairline);
                vertical-align: top; }
table.spec tr:last-child td { border-bottom: none; }
table.spec td.lbl {
  width: 21%;
  font-family: Optima, 'Avenir Next', 'Gill Sans', 'Trebuchet MS', sans-serif;
  text-transform: uppercase; letter-spacing: 0.16em;
  font-size: 7.2pt; color: var(--gold-dark);
  padding-top: 2.3mm;
}
table.spec td.val { width: 29%; color: var(--navy); font-size: 9.8pt; }
table.spec td.lbl:nth-child(3) {
  border-left: 0.6pt solid var(--hairline);
  padding-left: 4mm;
}
table.spec td.val:nth-child(2) { padding-right: 4mm; }

/* ------------- Callout ------------- */
.callout {
  break-inside: avoid; page-break-inside: avoid;
  margin: 8mm 0 4mm 0;
  background: var(--navy);
  border: 1pt solid var(--gold);
  outline: 0.6pt solid var(--gold);
  outline-offset: -2.2mm;
  color: var(--ivory);
  padding: 8mm 9mm 7mm 9mm;
}
.callout h3 {
  color: var(--gold-light);
  font-size: 15pt; font-weight: 400;
  margin: 0 0 3mm 0;
}
.callout p { margin: 0 0 2.8mm 0; line-height: 1.6; color: #efe7d3; }
.callout a { color: var(--gold-light); text-decoration: none; }
.callout ul { margin: 0 0 2.8mm 0; padding-left: 1mm; }
.callout ul > li { list-style: none; margin-bottom: 1.4mm;
                   padding-left: 1.1em; text-indent: -1.1em;
                   break-inside: avoid; page-break-inside: avoid; }
.callout ul > li::before {
  content: "\\2726"; display: inline-block; width: 1.44em; text-indent: 0;
  color: var(--gold-light); font-size: 8pt;
}
.callout .linksrow {
  margin-top: 4.5mm; padding-top: 3.6mm;
  border-top: 0.6pt solid rgba(212,176,106,0.55);
  font-size: 7.6pt; letter-spacing: 0.16em;
  color: var(--gold-pale);
}
.callout .linksrow span.sep { padding: 0 2.6mm; color: var(--gold); }

.endmark {
  display: flex; align-items: center; justify-content: center; gap: 3.5mm;
  margin: 7mm 0 0 0;
}
.endmark .line { width: 14mm; height: 0; border-top: 0.6pt solid var(--gold); }
.endmark svg { display: block; }
"""


def build_cover(doc, pub_logo_uri, fleet_logo_uri):
    doc_type = doc.get("doc_type", "guide")
    label = DOC_TYPE_LABELS.get(doc_type, "Document")
    cover_uri = file_uri(doc.get("cover_image"))

    img_html = ""
    veil_cls = "cover-veil no-img"
    if cover_uri:
        img_html = f'<img class="cover-img" src="{cover_uri}" alt="">'
        veil_cls = "cover-veil"

    logo_html = ""
    if pub_logo_uri:
        logo_html = (f'<span class="logo-chip"><img src="{pub_logo_uri}" '
                     f'alt="BoatHire24"></span>')

    fleet_html = ""
    if doc_type == "spec" and fleet_logo_uri:
        fleet_html = (
            '<div class="fleet-strip">'
            '<span class="fleet-label caps">From the fleet of</span>'
            f'<span class="logo-chip"><img src="{fleet_logo_uri}" '
            'alt="Boat Rental In Marbella"></span>'
            "</div>"
        )

    # The doc-type label appears exactly once (in .cover-rule); the top-right
    # flag carries the date instead, so the cover has a single document label.
    meta_bits = [b for b in (doc.get("author"),) if b]
    meta = '<span class="dot">&#9670;</span>'.join(esc(b) for b in meta_bits)
    date = doc.get("date")
    flag_html = (f'<div class="doc-type-flag caps">{esc(date)}</div>'
                 if date else "")

    return f"""
<div class="cover">
  {img_html}
  <div class="{veil_cls}"></div>
  <div class="cover-top">
    <div class="brand-lockup">
      {logo_html}
      <div>
        <div class="brand-name caps display">BoatHire24</div>
        <div class="brand-tag caps">Rent boats worldwide <span class="gold">|</span> list your boat free</div>
      </div>
    </div>
    {flag_html}
  </div>
  <div class="cover-main">
    <div class="cover-rule">
      <span class="line"></span>
      <span class="word caps">{esc(label)}</span>
    </div>
    <h1 class="cover-title display">{esc(doc.get("title"))}</h1>
    <p class="cover-subtitle display">{esc(doc.get("subtitle"))}</p>
    <div class="cover-meta caps">{meta}</div>
    {fleet_html}
  </div>
</div>"""


def build_spec_table(rows):
    """Two lbl/val pairs per table row so the spec block stays compact."""
    if not rows:
        return ""
    trs_list = []
    for i in range(0, len(rows), 2):
        pair = rows[i:i + 2]
        tds = "".join(
            f'<td class="lbl">{esc(r[0])}</td><td class="val">{esc(r[1])}</td>'
            for r in pair
        )
        if len(pair) == 1:  # odd count: pad so the grid stays aligned
            tds += '<td class="lbl"></td><td class="val"></td>'
        trs_list.append(f"<tr>{tds}</tr>")
    trs = "\n".join(trs_list)
    return f"""
<div class="spec-block sec">
  <div class="sec-head">
    <div class="sec-kicker caps">Particulars</div>
    <h2 class="display">{SPEC_TABLE_TITLE}</h2>
    <div class="rules"><span class="thick"></span><span class="thin"></span></div>
  </div>
  <table class="spec">{trs}</table>
</div>"""


_BEST_ROW_RE = re.compile(
    r'<tr>(\s*<td[^>]*>)([^<]*full[\s-]day[^<]*)(</td>)', re.IGNORECASE)


def enhance_section_html(s):
    """Highlight the 'full day' pricing row and tag it as best value."""
    if not s:
        return s
    return _BEST_ROW_RE.sub(
        r'<tr class="best">\1\2<span class="best-tag">Best value</span>\3',
        s, count=1)


def build_section(i, sec):
    fig = ""
    img_uri = file_uri(sec.get("image"))
    if img_uri:
        cap = sec.get("image_caption")
        cap_html = f"<figcaption>{esc(cap)}</figcaption>" if cap else ""
        fig = (f'<figure class="plate"><img src="{img_uri}" alt="">'
               f"{cap_html}</figure>")
    return f"""
<div class="sec">
  <div class="sec-head">
    <div class="sec-kicker caps">Section {i:02d}</div>
    <h2 class="display">{esc(sec.get("heading"))}</h2>
    <div class="rules"><span class="thick"></span><span class="thin"></span></div>
  </div>
  <div class="sec-body">{enhance_section_html(sec.get("html") or "")}</div>
  {fig}
</div>"""


def build_callout(callout, links):
    if not callout:
        return ""
    primary = (links or {}).get("primary")
    boat_url = (links or {}).get("boat_url")
    bits = []
    if primary:
        bits.append(f'<a href="{esc(primary)}">{esc(primary)}</a>')
    if boat_url:
        bits.append(f'<a href="{esc(boat_url)}">{esc(boat_url)}</a>')
    linksrow = ""
    if bits:
        joined = '<span class="sep">&#9670;</span>'.join(bits)
        linksrow = f'<div class="linksrow caps">{joined}</div>'
    return f"""
<div class="callout">
  <h3 class="display">{esc(callout.get("heading"))}</h3>
  {callout.get("html") or ""}
  {linksrow}
</div>"""


def build_footer(links):
    boat_url = (links or {}).get("boat_url")
    right = ""
    if boat_url:
        shown = boat_url.replace("https://", "").replace("http://", "").rstrip("/")
        right = f'<span class="gold caps">{esc(shown)}</span>'
    return f"""
<div class="runfoot caps">
  <span><b>boathire24.com</b> <span class="gold">&#9670;</span> rent boats worldwide
    <span class="gold">&#9670;</span> list your boat free</span>
  {right}
</div>"""


def build_html(doc):
    pub_logo_uri = file_uri(PUBLISHER_LOGO)
    fleet_logo_uri = file_uri(FLEET_LOGO)

    body_parts = [build_spec_table(doc.get("spec_table"))]
    for i, sec in enumerate(doc.get("sections") or [], start=1):
        body_parts.append(build_section(i, sec))
    body_parts.append(build_callout(doc.get("callout"), doc.get("links")))
    # Deliberate finisher: inline SVG anchor in brand gold (no font fallback).
    anchor_svg = (
        '<svg width="14" height="14" viewBox="0 0 24 24" '
        'xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
        '<path fill="#b9924b" d="M17 15l1.55 1.55c-.96 1.69-3.33 3.04-5.55 '
        '3.37V11h3V9h-3V7.82C14.16 7.4 15 6.3 15 5c0-1.65-1.35-3-3-3S9 3.35 '
        '9 5c0 1.3.84 2.4 2 2.82V9H8v2h3v8.92c-2.22-.33-4.59-1.68-5.55-3.37'
        'L7 15l-4-3v3c0 3.88 4.92 7 9 7s9-3.12 9-7v-3l-4 3zM12 4c.55 0 1 '
        '.45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1z"/></svg>'
    )
    body_parts.append(
        '<div class="endmark"><span class="line"></span>'
        f"{anchor_svg}"
        '<span class="line"></span></div>'
    )
    content = "\n".join(p for p in body_parts if p)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{esc(doc.get("title"))}</title>
<style>{CSS}</style>
</head>
<body>
{build_cover(doc, pub_logo_uri, fleet_logo_uri)}
<table class="paged">
  <thead><tr><td></td></tr></thead>
  <tbody><tr><td>
{content}
  </td></tr></tbody>
  <tfoot><tr><td></td></tr></tfoot>
</table>
{build_footer(doc.get("links"))}
</body>
</html>"""


def main():
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    content_path = pathlib.Path(sys.argv[1]).resolve()
    out_pdf = pathlib.Path(sys.argv[2]).resolve()
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    doc = json.loads(content_path.read_text(encoding="utf-8"))
    html_path = out_pdf.with_suffix(".render.html")
    html_path.write_text(build_html(doc), encoding="utf-8")

    cmd = [
        CHROME,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--virtual-time-budget=10000",
        f"--print-to-pdf={out_pdf}",
        html_path.as_uri(),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if proc.returncode != 0 or not out_pdf.is_file() or out_pdf.stat().st_size == 0:
        print(proc.stdout, file=sys.stderr)
        print(proc.stderr, file=sys.stderr)
        print(f"ERROR: Chrome render failed (rc={proc.returncode})", file=sys.stderr)
        sys.exit(1)
    print(f"OK: {out_pdf} ({out_pdf.stat().st_size} bytes); html: {html_path}")


if __name__ == "__main__":
    main()
