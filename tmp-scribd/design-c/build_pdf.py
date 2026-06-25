#!/usr/bin/env python3
"""
build_pdf.py — Design C: "Editorial Magazine" branded PDF builder for BoatHire24.

Usage:
    python3 build_pdf.py <content.json> <out.pdf>

Takes a content JSON (schema below), composes an editorial-magazine A4 layout
as a temp HTML file next to the output, and renders it with headless Chrome.

Content JSON schema:
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

Layout strategy: Chrome no longer repeats position:fixed elements per printed
page, so the builder ships a tiny JS paginator. Content is emitted as a flat
stream of blocks; at render time the script composes explicit 210x297mm sheets
(each with its own running head, footer and folio) and distributes blocks,
keeping section headings attached to the block that follows them.

Stdlib only. Chrome is the only external dependency.
"""

import html as htmlmod
import json
import os
import re
import subprocess
import sys
from urllib.parse import quote

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BRAND_LOGO = "/Users/master/boat-rental-platform/public/brand-logo.jpg"   # BoatHire24
FLEET_LOGO = "/Users/master/boat-rental-marbella/site/img/logo-640.png"   # Boat Rental In Marbella

FOOTER_TAGLINE = "boathire24.com — rent boats worldwide | list your boat free"

DOC_TYPE_LABEL = {
    "spec": "Fleet Spec Sheet",
    "research": "Research Report",
    "guide": "Charter Guide",
}


def esc(s):
    return htmlmod.escape(str(s if s is not None else ""), quote=True)


def file_uri(path):
    return "file://" + quote(os.path.abspath(path), safe="/")


def existing_image(path, label):
    """Return path if it exists, else warn and return None."""
    if not path:
        return None
    if os.path.isfile(path):
        return path
    sys.stderr.write("WARNING: %s image not found, skipping: %s\n" % (label, path))
    return None


# Top-level block elements we paginate on. Schema guarantees these don't nest.
BLOCK_RE = re.compile(r"<(p|ul|ol|table|blockquote|h3)\b[^>]*>.*?</\1\s*>",
                      re.S | re.I)


def split_blocks(section_html):
    """Split author HTML into a list of top-level block strings."""
    parts = [m.group(0) for m in BLOCK_RE.finditer(section_html or "")]
    if not parts and (section_html or "").strip():
        parts = ["<div>" + section_html + "</div>"]
    return parts


def add_dropcap(block):
    """Give the first <p> of the document a magazine drop cap.

    Skipped when the paragraph is too short to wrap around the cap,
    which would leave the big letter floating awkwardly.
    """
    m = re.match(r"\s*<p\b[^>]*>(.*?)</p\s*>", block, re.S | re.I)
    if not m:
        return block
    text = re.sub(r"<[^>]+>", "", m.group(1))
    if len(text.strip()) < 180:
        return block
    return re.sub(r"<p\b", '<p class="dropcap"', block, count=1)


CSS = """
* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
:root {
  --ink: #16242e;
  --muted: #5d6b74;
  --sand: #f4eee1;
  --sand-deep: #e9e0cc;
  --hair: #d4cebf;
  --hair-ink: #9aa6ad;
  --sea: #0d7585;
  --maroon: #7a2330;
  --paper: #ffffff;
  --serif: Georgia, 'Iowan Old Style', Palatino, 'Times New Roman', serif;
  --sans: 'Helvetica Neue', Helvetica, Arial, sans-serif;
}
@page { size: A4; margin: 0; }
html, body { margin: 0; padding: 0; background: #ffffff; }
body { font-family: var(--serif); color: var(--ink); }

/* ---------- sheets ---------- */
.sheet {
  position: relative;
  width: 210mm; height: 297mm;
  overflow: hidden;
  background: var(--paper);
  break-after: page; page-break-after: always;
  display: flex; flex-direction: column;
  padding: 0 17mm;
}
.runhead {
  flex: 0 0 auto;
  padding: 11mm 0 2.2mm;
  border-bottom: 0.5pt solid var(--ink);
  display: flex; justify-content: space-between; align-items: baseline;
  font-family: var(--sans); font-size: 6.6pt; letter-spacing: 0.24em;
  text-transform: uppercase; color: var(--ink);
}
.runhead .rh-right { color: var(--muted); letter-spacing: 0.2em; }
.pagebody { flex: 1 1 auto; overflow: hidden; padding-top: 6.5mm; }
.pagefoot {
  flex: 0 0 auto;
  border-top: 0.5pt solid var(--hair-ink);
  margin-top: 2mm;
  padding: 2.4mm 0 9mm;
  display: flex; justify-content: space-between; align-items: baseline; gap: 6mm;
  font-family: var(--sans); font-size: 6.4pt; letter-spacing: 0.06em;
  color: var(--muted);
}
.pagefoot .ft-brand { color: var(--ink); font-weight: 700; letter-spacing: 0.18em; text-transform: uppercase; white-space: nowrap; }
.pagefoot .ft-mid { text-align: center; flex: 1 1 auto; }
.pagefoot .folio { white-space: nowrap; color: var(--ink); letter-spacing: 0.14em; }

/* ---------- shared text ---------- */
p { margin: 0 0 3.2mm; font-size: 9.6pt; line-height: 1.62; text-align: justify; hyphens: auto; -webkit-hyphens: auto; }
a { color: var(--sea); text-decoration: none; border-bottom: 0.4pt solid var(--sea); }
strong { color: var(--ink); }
em { font-style: italic; }
p.dropcap::first-letter {
  float: left; font-size: 33pt; line-height: 0.84;
  padding: 1.2mm 2.2mm 0 0; color: var(--maroon); font-weight: 700;
}
ul, ol { margin: 0 0 3.4mm; padding-left: 5.5mm; }
li { font-size: 9.6pt; line-height: 1.58; margin-bottom: 1.5mm; padding-left: 1.4mm; }
ul { list-style: none; padding-left: 1mm; }
ul li { padding-left: 5.5mm; position: relative; }
ul li::before { content: "—"; position: absolute; left: 0; color: var(--maroon); }

blockquote {
  margin: 6mm 4mm 6mm 0; padding: 1mm 0 1mm 6mm;
  border-left: 2.4pt solid var(--maroon);
  font-size: 13.5pt; line-height: 1.45; font-style: italic; color: var(--ink);
  text-align: left;
}

table { width: 100%; border-collapse: collapse; margin: 2mm 0 4.5mm; }
th {
  font-family: var(--sans); font-size: 6.8pt; letter-spacing: 0.16em;
  text-transform: uppercase; text-align: left; color: var(--ink);
  background: var(--sand); padding: 2.2mm 3mm;
  border-bottom: 0.9pt solid var(--ink);
}
td { font-size: 9.4pt; padding: 1.9mm 3mm; border-bottom: 0.4pt solid var(--hair); }
td:last-child, th:last-child { text-align: right; }

/* ---------- section heads ---------- */
.sec-head { margin: 6mm 0 3.5mm; }
.pagebody > .sec-head:first-child { margin-top: 1mm; }
.kick {
  display: flex; align-items: center; gap: 3mm; margin-bottom: 2.2mm;
  font-family: var(--sans); font-size: 6.6pt; letter-spacing: 0.3em;
  text-transform: uppercase; color: var(--maroon); font-weight: 700;
}
.kick .kickrule { flex: 1 1 auto; height: 0.5pt; background: var(--hair); }
.sec-head h2 {
  margin: 0; font-family: var(--serif); font-weight: 700;
  font-size: 18.5pt; line-height: 1.12; letter-spacing: -0.01em;
}

/* ---------- figures ---------- */
figure { margin: 4.5mm 0 5mm; }
figure img { display: block; width: 100%; height: 76mm; object-fit: cover; }
figcaption {
  border-top: 0.5pt solid var(--ink);
  margin-top: 1.8mm; padding-top: 1.6mm;
  font-size: 8pt; font-style: italic; color: var(--muted); line-height: 1.45;
}
figcaption .figno {
  font-family: var(--sans); font-style: normal; font-weight: 700;
  font-size: 6.4pt; letter-spacing: 0.22em; color: var(--maroon);
  text-transform: uppercase; margin-right: 2.4mm;
}

/* ---------- spec panel ---------- */
.spec-panel { background: var(--sand); padding: 5.5mm 7mm 4mm; margin: 1mm 0 5mm; }
.spec-panel .kick { color: var(--ink); margin-bottom: 3mm; }
.spec-panel .kick .kickrule { background: var(--sand-deep); }
.spec-grid { display: grid; grid-template-columns: 1fr 1fr; column-gap: 9mm; }
.spec-row {
  display: flex; justify-content: space-between; align-items: baseline; gap: 4mm;
  padding: 1.7mm 0; border-bottom: 0.4pt solid var(--sand-deep);
}
.spec-row .sl {
  font-family: var(--sans); font-size: 6.6pt; letter-spacing: 0.18em;
  text-transform: uppercase; color: var(--muted); white-space: nowrap;
}
.spec-row .sv { font-size: 9.6pt; text-align: right; font-weight: 700; }

/* ---------- callout / pull-quote CTA ---------- */
.callout {
  border-top: 2.6pt solid var(--ink); border-bottom: 0.6pt solid var(--ink);
  padding: 6mm 0 6.5mm; margin: 8mm 0 4mm;
}
.pagebody > .callout:first-child { margin-top: 12mm; }
.callout .kick { color: var(--maroon); }
.callout h3 {
  margin: 0 0 3.2mm; font-family: var(--serif); font-style: italic; font-weight: 700;
  font-size: 22.5pt; line-height: 1.18; letter-spacing: -0.01em;
}
.callout p { font-size: 10pt; line-height: 1.6; text-align: left; }
.linkrow { display: flex; flex-wrap: wrap; gap: 3mm; margin-top: 3.5mm; }
.pill {
  display: inline-block; border: 0.8pt solid var(--ink); border-radius: 99px;
  padding: 1.7mm 4.5mm; font-family: var(--sans); font-size: 7.4pt;
  letter-spacing: 0.08em; color: var(--ink); text-decoration: none;
}
.pill.primary { background: var(--ink); color: #fff; border-color: var(--ink); }
.pill .pl { font-weight: 700; margin-right: 2mm; text-transform: uppercase; letter-spacing: 0.16em; font-size: 6.4pt; }

/* ---------- colophon ---------- */
.colophon {
  margin-top: 6mm; padding-top: 3.5mm; border-top: 0.5pt solid var(--hair-ink);
  display: flex; align-items: center; gap: 4mm;
}
.colophon .stamp { width: 9mm; height: 9mm; border-radius: 2mm; object-fit: cover; border: 0.4pt solid var(--hair); }
.colophon .col-text { font-size: 8pt; font-style: italic; color: var(--muted); line-height: 1.5; }

/* ---------- cover ---------- */
.sheet.cover { padding: 0; color: #fff; }
.cover .cov-img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
.cover .cov-plain { position: absolute; inset: 0; background: linear-gradient(160deg, #122836 0%, #0d3d4d 55%, #145b6b 100%); }
.cover .scrim {
  position: absolute; inset: 0;
  background: linear-gradient(180deg,
    rgba(7,18,26,0.82) 0%, rgba(7,18,26,0.30) 18%, rgba(7,18,26,0.02) 38%,
    rgba(6,15,22,0.10) 52%, rgba(6,15,22,0.78) 74%, rgba(4,11,17,0.95) 100%);
}
.cover .cov-inner {
  position: relative; height: 100%;
  display: flex; flex-direction: column; padding: 12mm 16mm 0;
}
.cov-masthead { display: flex; justify-content: space-between; align-items: center; }
.cov-brand { display: flex; align-items: center; gap: 4mm; }
.cov-brand img { width: 13mm; height: 13mm; border-radius: 2.6mm; object-fit: cover; }
.cov-brand .bw { font-family: var(--sans); }
.cov-brand .bw .b1 { font-size: 12.5pt; font-weight: 700; letter-spacing: 0.3em; }
.cov-brand .bw .b2 { font-size: 5.8pt; letter-spacing: 0.34em; text-transform: uppercase; opacity: 0.85; margin-top: 1.2mm; }
.cov-date {
  font-family: var(--sans); font-size: 7pt; letter-spacing: 0.3em;
  text-transform: uppercase; text-align: right; opacity: 0.92;
}
.cov-title-block { margin-top: auto; padding-bottom: 7mm; }
.cov-kick {
  display: flex; align-items: center; gap: 3.5mm;
  font-family: var(--sans); font-size: 7.4pt; letter-spacing: 0.42em;
  text-transform: uppercase; font-weight: 700; color: #ffe9c4;
}
.cov-kick::before { content: ""; width: 14mm; height: 1.6pt; background: #ffe9c4; }
.cov-title {
  margin: 4.5mm 0 0; font-family: var(--serif); font-weight: 700;
  font-size: 42pt; line-height: 1.02; letter-spacing: -0.015em;
  text-shadow: 0 1px 14px rgba(0,0,0,0.45); max-width: 165mm;
}
.cov-sub {
  margin: 4.5mm 0 0; font-style: italic; font-size: 13pt; line-height: 1.5;
  max-width: 150mm; color: rgba(255,255,255,0.94);
}
.cov-byline {
  margin-top: 5mm; font-family: var(--sans); font-size: 6.8pt;
  letter-spacing: 0.26em; text-transform: uppercase; color: rgba(255,255,255,0.85);
}
.cov-fleet {
  margin-top: 6mm; padding-top: 3.5mm; border-top: 0.5pt solid rgba(255,255,255,0.45);
  display: flex; align-items: center; gap: 3.5mm;
}
.cov-fleet img { width: 8.5mm; height: 8.5mm; border-radius: 1.8mm; object-fit: cover; }
.cov-fleet span {
  font-family: var(--sans); font-size: 6.6pt; letter-spacing: 0.24em;
  text-transform: uppercase; color: rgba(255,255,255,0.9);
}
.cov-foot {
  position: relative;
  border-top: 0.5pt solid rgba(255,255,255,0.5);
  display: flex; justify-content: space-between; align-items: baseline; gap: 6mm;
  padding: 2.6mm 0 9mm;
  font-family: var(--sans); font-size: 6.4pt; letter-spacing: 0.06em;
  color: rgba(255,255,255,0.92);
}
.cov-foot .ft-brand { font-weight: 700; letter-spacing: 0.18em; text-transform: uppercase; }
"""

PAGINATE_JS = """
document.addEventListener('DOMContentLoaded', function () {
  var flow = document.getElementById('flow');
  var pages = document.getElementById('pages');
  var tpl = document.getElementById('sheet-tpl');

  function newPage() {
    var frag = tpl.content.cloneNode(true);
    var s = frag.firstElementChild;
    pages.appendChild(s);
    return s.querySelector('.pagebody');
  }
  function over(b) { return b.scrollHeight > b.clientHeight + 1; }

  var blocks = Array.prototype.slice.call(flow.children);
  var body = newPage();
  for (var i = 0; i < blocks.length; i++) {
    var blk = blocks[i];
    body.appendChild(blk);
    if (over(body) && body.children.length > 1) {
      body = newPage();
      body.appendChild(blk);
    }
    /* keep headings (.kn) attached to the block that follows them */
    if (blk.classList.contains('kn') && i + 1 < blocks.length) {
      var nb = blocks[i + 1];
      body.appendChild(nb);
      var orphaned = over(body);
      body.removeChild(nb);
      if (orphaned && body.children.length > 1) {
        body = newPage();
        body.appendChild(blk);
      }
    }
  }
  flow.parentNode.removeChild(flow);

  var sheets = document.querySelectorAll('.sheet');
  for (var j = 0; j < sheets.length; j++) {
    var f = sheets[j].querySelector('.folio');
    if (f) f.textContent = (j + 1) + ' / ' + sheets.length;
    if (j === sheets.length - 1) {
      sheets[j].style.breakAfter = 'auto';
      sheets[j].style.pageBreakAfter = 'auto';
    }
  }

  /* pin the colophon to the foot of the closing page */
  var col = document.querySelector('.pagebody .colophon');
  if (col) {
    var lastBody = col.parentNode;
    lastBody.style.display = 'flex';
    lastBody.style.flexDirection = 'column';
    col.style.marginTop = 'auto';
  }
});
"""


def render_footer_inner(links):
    boat = links.get("boat_url")
    right = '<span class="folio"></span>'
    mid = esc(FOOTER_TAGLINE)
    if boat:
        mid += " &nbsp;·&nbsp; " + esc(boat)
    return ('<span class="ft-brand">BoatHire24</span>'
            '<span class="ft-mid">%s</span>%s' % (mid, right))


def render_cover(doc):
    links = doc.get("links") or {}
    cover_img = existing_image(doc.get("cover_image"), "cover")
    brand_logo = existing_image(BRAND_LOGO, "brand logo")
    fleet_logo = existing_image(FLEET_LOGO, "fleet logo")
    label = DOC_TYPE_LABEL.get(doc.get("doc_type"), "Feature")

    bg = ('<img class="cov-img" src="%s" alt="">' % file_uri(cover_img)) if cover_img \
        else '<div class="cov-plain"></div>'

    brand_stamp = ('<img src="%s" alt="BoatHire24">' % file_uri(brand_logo)) if brand_logo else ""

    fleet_row = ""
    if doc.get("doc_type") == "spec" and fleet_logo:
        fleet_row = ('<div class="cov-fleet"><img src="%s" alt="Boat Rental In Marbella">'
                     '<span>From the fleet of Boat Rental In Marbella · Puerto Ban&uacute;s</span></div>'
                     % file_uri(fleet_logo))

    byline = " · ".join(x for x in [esc(doc.get("author")), esc(doc.get("date"))] if x)

    boat = links.get("boat_url")
    foot_mid = esc(FOOTER_TAGLINE) + ((" &nbsp;·&nbsp; " + esc(boat)) if boat else "")

    return """
<section class="sheet cover">
  %(bg)s
  <div class="scrim"></div>
  <div class="cov-inner">
    <div class="cov-masthead">
      <div class="cov-brand">%(brand_stamp)s
        <div class="bw"><div class="b1">BOATHIRE24</div>
        <div class="b2">Rent boats worldwide · List your boat free</div></div>
      </div>
      <div class="cov-date">%(date)s</div>
    </div>
    <div class="cov-title-block">
      <div class="cov-kick">%(label)s</div>
      <h1 class="cov-title">%(title)s</h1>
      <p class="cov-sub">%(subtitle)s</p>
      <div class="cov-byline">%(byline)s</div>
      %(fleet_row)s
    </div>
    <div class="cov-foot"><span class="ft-brand">BoatHire24</span>
      <span class="ft-mid">%(foot_mid)s</span></div>
  </div>
</section>""" % dict(bg=bg, brand_stamp=brand_stamp, date=esc(doc.get("date")),
                     label=esc(label), title=esc(doc.get("title")),
                     subtitle=esc(doc.get("subtitle")), byline=byline,
                     fleet_row=fleet_row, foot_mid=foot_mid)


def render_spec_panel(spec_table):
    rows = "".join(
        '<div class="spec-row"><span class="sl">%s</span><span class="sv">%s</span></div>'
        % (esc(l), esc(v)) for l, v in spec_table)
    return ('<div class="blk spec-panel">'
            '<div class="kick"><span>At a glance</span><span class="kickrule"></span></div>'
            '<div class="spec-grid">%s</div></div>' % rows)


def render_flow_blocks(doc):
    """Flat stream of blocks the JS paginator distributes across sheets."""
    blocks = []
    fig_no = 0

    if doc.get("doc_type") == "spec" and doc.get("spec_table"):
        blocks.append(render_spec_panel(doc["spec_table"]))

    sections = doc.get("sections") or []
    for i, sec in enumerate(sections):
        blocks.append(
            '<div class="blk sec-head kn">'
            '<div class="kick"><span class="kickno">No. %02d</span>'
            '<span class="kickrule"></span></div>'
            '<h2>%s</h2></div>' % (i + 1, esc(sec.get("heading"))))

        img = existing_image(sec.get("image"), "section %d" % (i + 1))
        if img:
            fig_no += 1
            cap = sec.get("image_caption")
            capline = ('<figcaption><span class="figno">Fig. %02d</span>%s</figcaption>'
                       % (fig_no, esc(cap))) if cap else ""
            blocks.append('<figure class="blk"><img src="%s" alt="">%s</figure>'
                          % (file_uri(img), capline))

        body_blocks = split_blocks(sec.get("html") or "")
        if i == 0 and body_blocks:
            body_blocks[0] = add_dropcap(body_blocks[0])
        blocks.extend('<div class="blk">%s</div>' % b for b in body_blocks)

    callout = doc.get("callout")
    links = doc.get("links") or {}
    if callout:
        pills = []
        if links.get("primary"):
            pills.append('<a class="pill primary" href="%s"><span class="pl">Book / List</span>%s</a>'
                         % (esc(links["primary"]), esc(links["primary"])))
        if links.get("boat_url"):
            pills.append('<a class="pill" href="%s"><span class="pl">This boat</span>%s</a>'
                         % (esc(links["boat_url"]), esc(links["boat_url"])))
        blocks.append(
            '<div class="blk callout">'
            '<div class="kick"><span>The invitation</span><span class="kickrule"></span></div>'
            '<h3>%s</h3>%s<div class="linkrow">%s</div></div>'
            % (esc(callout.get("heading")), callout.get("html") or "", "".join(pills)))

    # colophon / publisher credit
    brand_logo = existing_image(BRAND_LOGO, "brand logo")
    fleet_logo = existing_image(FLEET_LOGO, "fleet logo")
    stamps = ""
    if brand_logo:
        stamps += '<img class="stamp" src="%s" alt="">' % file_uri(brand_logo)
    if doc.get("doc_type") == "spec" and fleet_logo:
        stamps += '<img class="stamp" src="%s" alt="">' % file_uri(fleet_logo)
    blocks.append(
        '<div class="blk colophon">%s<div class="col-text">'
        'Published by <strong>BoatHire24</strong> — rent boats worldwide, '
        'list your boat free. %s · %s</div></div>'
        % (stamps, esc(doc.get("author")), esc(doc.get("date"))))

    return "".join(blocks)


def build_html(doc):
    label = DOC_TYPE_LABEL.get(doc.get("doc_type"), "Feature")
    links = doc.get("links") or {}
    rh_left = "BoatHire24 — " + label
    rh_right = doc.get("title") or ""

    sheet_tpl = """
<template id="sheet-tpl">
  <section class="sheet">
    <div class="runhead"><span>%s</span><span class="rh-right">%s</span></div>
    <div class="pagebody"></div>
    <div class="pagefoot">%s</div>
  </section>
</template>""" % (esc(rh_left), esc(rh_right), render_footer_inner(links))

    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>%(title)s</title>
<style>%(css)s</style>
</head>
<body>
%(cover)s
<div id="pages"></div>
<div id="flow" style="position:absolute; left:-9999mm; top:0; width:176mm; visibility:hidden;">%(flow)s</div>
%(sheet_tpl)s
<script>%(js)s</script>
</body>
</html>""" % dict(title=esc(doc.get("title")), css=CSS, cover=render_cover(doc),
                  flow=render_flow_blocks(doc), sheet_tpl=sheet_tpl, js=PAGINATE_JS)


def main():
    if len(sys.argv) != 3:
        sys.stderr.write("usage: python3 build_pdf.py <content.json> <out.pdf>\n")
        return 2
    content_path, out_pdf = sys.argv[1], os.path.abspath(sys.argv[2])

    with open(content_path, "r", encoding="utf-8") as f:
        doc = json.load(f)

    html_path = os.path.splitext(out_pdf)[0] + ".build.html"
    os.makedirs(os.path.dirname(out_pdf) or ".", exist_ok=True)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(build_html(doc))

    cmd = [CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
           "--virtual-time-budget=10000",
           "--print-to-pdf=" + out_pdf, file_uri(html_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    ok = os.path.isfile(out_pdf) and os.path.getsize(out_pdf) > 1000
    if not ok:
        sys.stderr.write("Chrome render failed (exit %s)\n%s\n" % (proc.returncode, proc.stderr[-3000:]))
        return 1
    print("OK  %s  (%d bytes)\nHTML kept at %s" % (out_pdf, os.path.getsize(out_pdf), html_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
