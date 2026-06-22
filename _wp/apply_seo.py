# -*- coding: utf-8 -*-
"""Validate the SEO map (title<=60, desc<=160 & ends with a CTA) and (optionally) apply it
to the static HTML files: <title>, <meta name=description>, og:title, og:description.
Usage:  python apply_seo.py            # validate + report only
        python apply_seo.py --apply    # also write the HTML files
"""
import os, re, io, sys, html
sys.path.insert(0, os.path.dirname(__file__))
from seo_map import SEO, FILE_OF, CTA

SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TITLE_MAX, DESC_MAX, DESC_MIN = 60, 160, 110
apply = "--apply" in sys.argv

def esc(s):  # attribute-safe
    return html.escape(s, quote=True)

problems, rows = [], []
for slug, m in SEO.items():
    t, d = m["title"], m["desc"]
    tl, dl = len(t), len(d)
    flags = []
    if tl > TITLE_MAX: flags.append("TITLE>%d" % TITLE_MAX)
    if dl > DESC_MAX:  flags.append("DESC>%d" % DESC_MAX)
    if dl < DESC_MIN:  flags.append("DESC<%d" % DESC_MIN)
    if not any(d.endswith(c) for c in CTA): flags.append("NO-CTA")
    if flags: problems.append((slug, flags))
    rows.append((slug, tl, dl, " ".join(flags) or "ok"))

print("%-34s %4s %4s  %s" % ("slug", "T", "D", "status"))
for slug, tl, dl, st in rows:
    print("%-34s %4d %4d  %s" % (slug, tl, dl, st))
print("\n%d pages, %d with problems" % (len(rows), len(problems)))

if problems and apply:
    print("REFUSING to apply - fix problems first."); sys.exit(1)
if not apply:
    sys.exit(0)

# ---- apply to static HTML ----
def sub_meta(htmltext, slug, t, d):
    n = 0
    def rep(pat, val):
        nonlocal htmltext, n
        new, k = re.subn(pat, lambda _: val, htmltext, count=1, flags=re.S)
        htmltext = new; n += k
    rep(r"<title>.*?</title>", "<title>%s</title>" % esc(t))
    rep(r'<meta name="description" content=".*?">', '<meta name="description" content="%s">' % esc(d))
    rep(r'<meta property="og:title" content=".*?">', '<meta property="og:title" content="%s">' % esc(t))
    rep(r'<meta property="og:description" content=".*?">', '<meta property="og:description" content="%s">' % esc(d))
    return htmltext, n

changed = 0
for slug, m in SEO.items():
    stem = FILE_OF.get(slug, slug)
    path = os.path.join(SRC, stem + ".html")
    if not os.path.isfile(path):
        print("MISSING file:", stem); continue
    s = io.open(path, encoding="utf-8").read()
    s2, n = sub_meta(s, slug, m["title"], m["desc"])
    if s2 != s:
        io.open(path, "w", encoding="utf-8", newline="\n").write(s2)
        changed += 1
        print("updated %-28s (%d tags)" % (stem, n))
print("\napplied to %d files" % changed)
