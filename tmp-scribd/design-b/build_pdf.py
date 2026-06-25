#!/usr/bin/env python3
"""
BoatHire24 branded PDF builder — Design B: MODERN MINIMAL.

Generous whitespace, crisp sans-serif, one azure accent, thin rules,
Scandinavian charter-platform feel.

Usage:
    python3 build_pdf.py <content.json> <out.pdf>

Builds a temp HTML file next to the output PDF and renders it with
headless Chrome. Stdlib only.
"""

import html
import json
import os
import subprocess
import sys
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Fixed branding ------------------------------------------------------------
PUBLISHER_LOGO = "/Users/master/boat-rental-platform/public/brand-logo.jpg"
FLEET_LOGO = "/Users/master/boat-rental-marbella/site/img/logo-640.png"
FOOTER_TAGLINE = "boathire24.com — rent boats worldwide | list your boat free"

DOC_TYPE_KICKER = {
    "spec": "Charter Spec Sheet",
    "research": "Research Report",
    "guide": "Charter Guide",
}


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def file_uri(path):
    """Absolute file:// URI for an image path, or None."""
    if not path:
        return None
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        sys.stderr.write(f"warning: image not found, skipping: {p}\n")
        return None
    return p.as_uri()


# ---------------------------------------------------------------------------
# CSS — modern minimal
# ---------------------------------------------------------------------------
CSS = """
:root {
  --azure: #0E7FC1;
  --azure-tint: #F1F7FB;
  --ink: #1B2733;
  --mute: #66737E;
  --hair: #E3E8EC;
}
* { margin: 0; padding: 0; box-sizing: border-box; }

@page {
  size: A4;
  margin: 18mm 17mm 16mm 17mm;
}

/* Paper wrapper table: the repeating tfoot reserves room for the fixed
   runner footer at the bottom of every page. */
table.paper { width: 100%; border-collapse: collapse; }
table.paper > tbody > tr > td { padding: 0; vertical-align: top; }
table.paper .footspace { height: 13mm; }

html, body { margin: 0; padding: 0; }
body {
  font-family: -apple-system, "Helvetica Neue", "Segoe UI", Arial, sans-serif;
  color: var(--ink);
  font-size: 10.5pt;
  line-height: 1.62;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}

a { color: var(--azure); text-decoration: none; }

/* ---------- repeating page footer (skipped on the zero-margin cover) ---- */
.runner {
  position: fixed;
  left: 0; right: 0;
  bottom: 0;
  z-index: 50;
  background: #fff;
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 6mm;
  border-top: 0.6pt solid var(--hair);
  padding-top: 2.4mm;
  font-size: 7.2pt;
  letter-spacing: 0.02em;
  color: var(--mute);
}
.runner a { color: var(--azure); }
.runner .right { text-align: right; white-space: nowrap; }

/* ---------- cover ------------------------------------------------------- */
.cover {
  height: 246mm;
  position: relative;
  overflow: hidden;
  page-break-after: always;
  background: #fff;
}
.cover-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.brandline { display: flex; align-items: center; gap: 4mm; }
.brandline img {
  height: 11mm; width: 11mm;
  object-fit: cover;
  border-radius: 2.2mm;
  display: block;
}
.brandline .bn { font-size: 11pt; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; }
.brandline .bn .accent { color: var(--azure); }
.brandline .bt { font-size: 7pt; letter-spacing: 0.22em; text-transform: uppercase; color: var(--mute); margin-top: 0.6mm; }
.fleetmark img {
  height: 10mm;
  border-radius: 1.6mm;
  display: block;
}
.cover-img {
  margin: 10mm 0 0;
  height: 122mm;
  overflow: hidden;
}
.cover-img img { width: 100%; height: 100%; object-fit: cover; display: block; }
.cover-body { padding: 0; }
.kicker {
  margin-top: 12mm;
  font-size: 8pt;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--azure);
  font-weight: 600;
}
.cover h1 {
  margin-top: 4mm;
  font-size: 31pt;
  font-weight: 300;
  letter-spacing: -0.015em;
  line-height: 1.12;
}
.cover .rule {
  width: 22mm; height: 0; border: 0;
  border-top: 1.4pt solid var(--azure);
  margin: 6mm 0 5.5mm;
}
.cover .subtitle {
  font-size: 12pt;
  font-weight: 400;
  color: var(--mute);
  line-height: 1.55;
  max-width: 150mm;
}
.cover-foot {
  position: absolute;
  left: 0; right: 0; bottom: 1mm;
  display: flex;
  justify-content: space-between;
  border-top: 0.6pt solid var(--hair);
  padding-top: 3mm;
  font-size: 7.6pt;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--mute);
}

/* ---------- content ----------------------------------------------------- */
.sec { margin-top: 10mm; }
.sec:first-child { margin-top: 0; }
.sec-no {
  display: block;
  font-size: 7.6pt;
  font-weight: 600;
  letter-spacing: 0.28em;
  color: var(--azure);
  margin-bottom: 1.6mm;
}
h2 {
  font-size: 15.5pt;
  font-weight: 600;
  letter-spacing: -0.01em;
  margin-bottom: 3.4mm;
  page-break-after: avoid;
  break-after: avoid;
}
.sec-head { page-break-inside: avoid; break-inside: avoid; page-break-after: avoid; }

.body-html p { margin-bottom: 3mm; }
.body-html p:last-child { margin-bottom: 0; }
.body-html ul, .body-html ol { margin: 1mm 0 3mm 5mm; }
.body-html li { margin-bottom: 1.6mm; padding-left: 1mm; }
.body-html li::marker { color: var(--azure); }
.body-html strong { font-weight: 600; }
.body-html em { font-style: italic; }

.body-html table {
  width: 100%;
  border-collapse: collapse;
  margin: 3mm 0 4mm;
  font-size: 9.8pt;
  page-break-inside: avoid;
  break-inside: avoid;
}
.body-html th {
  text-align: left;
  font-size: 7.6pt;
  font-weight: 600;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--mute);
  padding: 0 2mm 2mm 0;
  border-bottom: 1.2pt solid var(--azure);
}
.body-html td {
  padding: 2.5mm 2mm 2.5mm 0;
  border-bottom: 0.6pt solid var(--hair);
  vertical-align: top;
}
.body-html th.num, .body-html td.num { text-align: right; padding-right: 0; }

figure {
  margin: 5mm 0 1mm;
  page-break-inside: avoid;
  break-inside: avoid;
}
figure img {
  width: 100%;
  height: 76mm;
  object-fit: cover;
  display: block;
}
figcaption {
  margin-top: 2.2mm;
  font-size: 8pt;
  color: var(--mute);
  letter-spacing: 0.02em;
}
figcaption::before { content: "—  "; color: var(--azure); }

/* ---------- spec at-a-glance grid --------------------------------------- */
.atglance { margin-top: 0; }
.spec-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  column-gap: 12mm;
  page-break-inside: avoid;
  break-inside: avoid;
}
.spec-cell {
  border-bottom: 0.6pt solid var(--hair);
  padding: 2.6mm 0 2.4mm;
  page-break-inside: avoid;
  break-inside: avoid;
}
.spec-cell .sl {
  font-size: 7.2pt;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--mute);
}
.spec-cell .sv { font-size: 10.5pt; font-weight: 500; margin-top: 0.6mm; }

/* ---------- callout ------------------------------------------------------ */
.callout {
  margin-top: 10mm;
  background: var(--azure-tint);
  border-top: 1.6pt solid var(--azure);
  padding: 6.5mm 7mm 6mm;
  page-break-inside: avoid;
  break-inside: avoid;
}
.callout h3 {
  font-size: 12pt;
  font-weight: 600;
  margin-bottom: 2.4mm;
}
.callout .links {
  margin-top: 3.6mm;
  padding-top: 3mm;
  border-top: 0.6pt solid #D5E4EE;
  font-size: 9.2pt;
}
.callout .links a { font-weight: 600; }
.callout .links .sep { color: var(--mute); margin: 0 2.4mm; }

.endlinks {
  margin-top: 10mm;
  border-top: 0.6pt solid var(--hair);
  padding-top: 3mm;
  font-size: 9.2pt;
}
"""


# ---------------------------------------------------------------------------
# HTML assembly
# ---------------------------------------------------------------------------
def brand_block():
    logo = file_uri(PUBLISHER_LOGO)
    img = f'<img src="{logo}" alt="BoatHire24">' if logo else ""
    return (
        f'<div class="brandline">{img}'
        '<div><div class="bn">Boat<span class="accent">Hire</span>24</div>'
        '<div class="bt">rent boats worldwide</div></div></div>'
    )


def build_cover(doc):
    doc_type = doc.get("doc_type", "guide")
    kicker = DOC_TYPE_KICKER.get(doc_type, "Document")
    parts = ['<section class="cover">', '<div class="cover-top">', brand_block()]
    if doc_type == "spec":
        fleet = file_uri(FLEET_LOGO)
        if fleet:
            parts.append(
                f'<div class="fleetmark"><img src="{fleet}" alt="Boat Rental In Marbella"></div>'
            )
    parts.append("</div>")

    cover_img = file_uri(doc.get("cover_image"))
    if cover_img:
        parts.append(f'<div class="cover-img"><img src="{cover_img}" alt=""></div>')

    parts.append('<div class="cover-body">')
    parts.append(f'<div class="kicker">{esc(kicker)}</div>')
    parts.append(f"<h1>{esc(doc.get('title', ''))}</h1>")
    parts.append('<hr class="rule">')
    if doc.get("subtitle"):
        parts.append(f'<div class="subtitle">{esc(doc["subtitle"])}</div>')
    parts.append("</div>")

    parts.append(
        '<div class="cover-foot">'
        f"<span>{esc(doc.get('author', ''))}</span>"
        f"<span>{esc(doc.get('date', ''))}</span>"
        "</div>"
    )
    parts.append("</section>")
    return "".join(parts)


def build_spec_grid(spec_table):
    cells = "".join(
        f'<div class="spec-cell"><div class="sl">{esc(label)}</div>'
        f'<div class="sv">{esc(value)}</div></div>'
        for label, value in spec_table
    )
    return (
        '<div class="sec atglance"><div class="sec-head">'
        '<span class="sec-no">At a glance</span></div>'
        f'<div class="spec-grid">{cells}</div></div>'
    )


def build_sections(sections):
    out = []
    for i, sec in enumerate(sections, 1):
        out.append('<div class="sec">')
        out.append(
            '<div class="sec-head">'
            f'<span class="sec-no">{i:02d}</span>'
            f"<h2>{esc(sec.get('heading', ''))}</h2></div>"
        )
        out.append(f'<div class="body-html">{sec.get("html", "")}</div>')
        img = file_uri(sec.get("image"))
        if img:
            cap = sec.get("image_caption")
            cap_html = f"<figcaption>{esc(cap)}</figcaption>" if cap else ""
            out.append(f'<figure><img src="{img}" alt="">{cap_html}</figure>')
        out.append("</div>")
    return "".join(out)


def build_links_html(links):
    if not links:
        return ""
    bits = []
    primary = links.get("primary")
    if primary:
        bits.append(f'<a href="{esc(primary)}">{esc(primary.replace("https://", "").rstrip("/"))}</a>')
    boat_url = links.get("boat_url")
    if boat_url:
        bits.append(f'<a href="{esc(boat_url)}">{esc(boat_url.replace("https://", "").rstrip("/"))}</a>')
    return '<span class="sep">·</span>'.join(bits)


def build_callout(doc):
    callout = doc.get("callout")
    links_html = build_links_html(doc.get("links") or {})
    if callout:
        link_row = f'<div class="links">{links_html}</div>' if links_html else ""
        return (
            '<div class="callout">'
            f"<h3>{esc(callout.get('heading', ''))}</h3>"
            f'<div class="body-html">{callout.get("html", "")}</div>'
            f"{link_row}</div>"
        )
    if links_html:
        return f'<div class="endlinks">{links_html}</div>'
    return ""


def build_runner(doc):
    links = doc.get("links") or {}
    boat_url = links.get("boat_url")
    primary = links.get("primary") or "https://boathire24.com"
    left = (
        f'<span><a href="{esc(primary)}">boathire24.com</a>'
        " — rent boats worldwide&nbsp;&nbsp;|&nbsp;&nbsp;list your boat free</span>"
    )
    right = ""
    if boat_url:
        label = boat_url.replace("https://", "").replace("http://", "").rstrip("/")
        right = f'<span class="right"><a href="{esc(boat_url)}">{esc(label)}</a></span>'
    return f'<footer class="runner">{left}{right}</footer>'


def build_html(doc):
    content = [build_cover(doc), "<main>"]
    if doc.get("doc_type") == "spec" and doc.get("spec_table"):
        content.append(build_spec_grid(doc["spec_table"]))
    content.append(build_sections(doc.get("sections") or []))
    content.append(build_callout(doc))
    content.append("</main>")
    body = (
        '<table class="paper"><tbody><tr><td>'
        + "".join(content)
        + "</td></tr></tbody>"
        '<tfoot><tr><td><div class="footspace"></div></td></tr></tfoot>'
        "</table>" + build_runner(doc)
    )
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en"><head><meta charset="utf-8">'
        f"<title>{esc(doc.get('title', 'Document'))}</title>"
        f"<style>{CSS}</style></head><body>"
        + body
        + "</body></html>"
    )


# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) != 3:
        sys.exit("usage: python3 build_pdf.py <content.json> <out.pdf>")
    content_path = Path(sys.argv[1]).resolve()
    out_pdf = Path(sys.argv[2]).resolve()
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    with open(content_path, encoding="utf-8") as f:
        doc = json.load(f)

    html_path = out_pdf.parent / (out_pdf.stem + ".tmp.html")
    html_path.write_text(build_html(doc), encoding="utf-8")

    cmd = [
        CHROME,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--virtual-time-budget=10000",
        f"--print-to-pdf={out_pdf}",
        html_path.resolve().as_uri(),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not out_pdf.is_file():
        sys.stderr.write(proc.stdout + proc.stderr)
        sys.exit(f"Chrome render failed (exit {proc.returncode})")
    print(f"wrote {out_pdf} ({out_pdf.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
