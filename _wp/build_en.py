# -*- coding: utf-8 -*-
"""
English-tree helpers for olsi.co.il.

  rewrite_links_en(html)  -> prefix internal page links with /en (leave assets,
                             on-page #anchors, tel:/mailto:/http, and already-/en/).
  fetch_body(id)          -> live post_content (the source of truth) via WP REST.
  push_en_page(...)       -> create/update an English child page under the "en" parent.

Translation of the visible text is done separately (LLM); this module only handles the
deterministic, review-safe transforms so a mistranslation can never break a link.
"""
import re, json, sys, urllib.request, urllib.parse, base64, io, os

SITE = "https://www.olsi.co.il"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wp_auth import USER, APPPW  # local-only, gitignored (see _wp/wp_auth.py)
_AUTH = "Basic " + base64.b64encode(("%s:%s" % (USER, APPPW)).encode()).decode()

# ---- English LTR cleanup: neutralize Hebrew-era inline RTL on EN pages -----------
# Some migrated blog posts carry element-level dir="rtl" / style="direction:rtl" /
# lang="he" from the old Elementor build. On an English page those must not force
# RTL. Applied AFTER fidelity verification (so it never masks a translator error).
def en_ltr_cleanup(html):
    html = re.sub(r'\s+dir="(?:rtl|RTL)"', '', html)
    # drop a direction:rtl declaration from inline style="" (keep the rest of the style)
    def _style(m):
        s = re.sub(r'direction\s*:\s*rtl\s*;?', '', m.group(1), flags=re.I)
        s = s.strip().strip(';').strip()
        return ('style="%s"' % s) if s else ''
    html = re.sub(r'style="([^"]*)"', _style, html)
    html = re.sub(r'\slang="he"', ' lang="en"', html)
    return html

# ---- internal link rewrite: /x/ -> /en/x/ , /#a -> /en/#a , / -> /en/ ------------
def rewrite_links_en(html):
    def repl(m):
        attr, url = m.group(1), m.group(2)
        # leave: assets, uploads, already-en, protocol/anchor/tel/mailto (those don't start with a single '/')
        if url.startswith("/wp-content/") or url.startswith("/wp-admin/") \
           or url.startswith("/en/") or url == "/en":
            return m.group(0)
        # url starts with a single '/': a page path or /#anchor -> prefix /en
        return '%s="/en%s"' % (attr, url)
    # only single-slash root-relative hrefs (not // ) ; src stays (images live in /wp-content)
    return re.sub(r'(href)="(/(?!/)[^"]*)"', repl, html)

# ---- live REST helpers -----------------------------------------------------------
def _req(method, path, data=None):
    url = SITE + path
    body = json.dumps(data).encode("utf-8") if data is not None else None
    r = urllib.request.Request(url, data=body, method=method)
    r.add_header("Authorization", _AUTH)
    if body is not None:
        r.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(r) as resp:
        return json.loads(resp.read().decode("utf-8"))

def fetch_item(item_id, ptype="pages"):
    """live raw post_content + title for a page/post id."""
    d = _req("GET", "/wp-json/wp/v2/%s/%d?context=edit" % (ptype, item_id))
    return {"id": d["id"], "slug": d["slug"],
            "title": d["title"]["raw"], "content": d["content"]["raw"]}

def get_en_parent_id():
    d = _req("GET", "/wp-json/wp/v2/pages?slug=en&status=publish,draft&_fields=id,slug")
    return d[0]["id"] if d else None

def push_en_page(slug, title, content, parent_id, page_id=None):
    """create (or update) an English page: child of the 'en' parent, EN body, links rewritten."""
    payload = {"slug": slug, "title": title, "content": content,
               "status": "publish", "parent": parent_id,
               "comment_status": "closed", "ping_status": "closed"}
    if page_id:
        return _req("POST", "/wp-json/wp/v2/pages/%d" % page_id, payload)
    return _req("POST", "/wp-json/wp/v2/pages", payload)

if __name__ == "__main__":
    # tiny self-test of the link rewriter
    tests = [
        ('<a href="/">x</a>', '<a href="/en/">x</a>'),
        ('<a href="/#contact">x</a>', '<a href="/en/#contact">x</a>'),
        ('<a href="/software-development/">x</a>', '<a href="/en/software-development/">x</a>'),
        ('<a href="/case-study-crm/">x</a>', '<a href="/en/case-study-crm/">x</a>'),
        ('<img src="/wp-content/uploads/a.jpg">', '<img src="/wp-content/uploads/a.jpg">'),
        ('<a href="/wp-content/x.pdf">x</a>', '<a href="/wp-content/x.pdf">x</a>'),
        ('<a href="#lets-talk">x</a>', '<a href="#lets-talk">x</a>'),
        ('<a href="/en/x/">x</a>', '<a href="/en/x/">x</a>'),
        ('<a href="mailto:a@b.c">x</a>', '<a href="mailto:a@b.c">x</a>'),
        ('<a href="tel:098820511">x</a>', '<a href="tel:098820511">x</a>'),
    ]
    ok = True
    for src, want in tests:
        got = rewrite_links_en(src)
        flag = "OK " if got == want else "FAIL"
        if got != want:
            ok = False
        print("%s  %-45s -> %s" % (flag, src, got))
    print("ALL PASS" if ok else "SOME FAILED")
