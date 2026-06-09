#!/usr/bin/env python3
"""Ensure every built page carries the Google Analytics (gtag.js) tag.

Runs after all page generators in deploy.sh, like the other inject_*.py
post-processors. The main template (templates/page.html.template) already
includes the GA snippet, but some generators build their own <head>
(build_languages.py for the language homes, build_es.py / build_de.py for
legal pages, etc.) and would otherwise ship without analytics. This guarantees
site-wide coverage regardless of which generator produced a page.

Idempotent: any page that already has the tag is left untouched, so it is safe
to run on every deploy.
"""
import pathlib

GA_ID = "G-SPMRYJVTHD"
GA_TAG = (
    "<!-- Google tag (gtag.js) -->\n"
    f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>\n'
    "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}"
    f"gtag('js',new Date());gtag('config','{GA_ID}');</script>"
)


def main() -> None:
    site = pathlib.Path(__file__).resolve().parent.parent / "site"
    patched = 0
    already = 0
    no_head = []
    for f in site.rglob("*.html"):
        text = f.read_text(encoding="utf-8")
        if "googletagmanager.com/gtag/js" in text:
            already += 1
            continue
        if "<head>" in text:
            f.write_text(text.replace("<head>", "<head>\n" + GA_TAG, 1), encoding="utf-8")
            patched += 1
        elif "</head>" in text:
            f.write_text(text.replace("</head>", GA_TAG + "\n</head>", 1), encoding="utf-8")
            patched += 1
        else:
            no_head.append(str(f.relative_to(site)))
    print(f"inject_ga: patched {patched}, already-tagged {already}")
    if no_head:
        print(f"inject_ga: WARNING no <head> in {len(no_head)} file(s): {no_head[:10]}")


if __name__ == "__main__":
    main()
