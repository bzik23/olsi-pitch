# -*- coding: utf-8 -*-
"""
Publish translated English pages to olsi.co.il as children of the "en" parent (3928).

For each slug:
  1. verify the translation against the HE source (tag-count parity, zero Hebrew,
     identical href/src BEFORE rewrite) -> refuse to publish on mismatch
  2. rewrite internal links to the /en/ tree
  3. upsert the EN child page (parent 3928) via REST
  4. re-save the HE counterpart (page or post) to purge its SeoEdge cache so its
     language switcher lights up for anonymous visitors
Records EN page ids in _i18n/en_ids.json. Idempotent (updates instead of duplicating).
"""
import json, io, os, re, sys, time
import build_en as B

HERE = os.path.dirname(__file__)
EN_PARENT = 3928
MAN = {m["slug"]: m for m in json.load(io.open(os.path.join(HERE, "_i18n", "manifest.json"), encoding="utf-8"))}
IDS_PATH = os.path.join(HERE, "_i18n", "en_ids.json")

def _tags(s):
    return re.findall(r"<[^>]+>", s)

def _norm_tag(t):
    return re.sub(r'(alt|title|placeholder|aria-label)="[^"]*"', r'\1="~"', t)

def verify(slug):
    he = io.open(os.path.join(HERE, "_i18n", "he", slug + ".html"), encoding="utf-8").read()
    en = io.open(os.path.join(HERE, "_i18n", "en", slug + ".html"), encoding="utf-8").read()
    th, te = _tags(he), _tags(en)
    problems = []
    if len(th) != len(te):
        problems.append("tag count %d!=%d" % (len(th), len(te)))
    else:
        d = [i for i, (a, b) in enumerate(zip(map(_norm_tag, th), map(_norm_tag, te))) if a != b]
        if d:
            problems.append("%d tag-structure diffs (first: %s | %s)" % (len(d), th[d[0]][:60], te[d[0]][:60]))
    if re.search(r"[֐-׿]", en):
        problems.append("hebrew remains (%d runs)" % len(re.findall(r"[֐-׿]+", en)))
    hh = re.findall(r'href="[^"]*"', he); eh = re.findall(r'href="[^"]*"', en)
    if hh != eh:
        problems.append("href mismatch (HE=%d EN=%d)" % (len(hh), len(eh)))
    hs = re.findall(r'src="[^"]*"', he); es = re.findall(r'src="[^"]*"', en)
    if hs != es:
        problems.append("src mismatch (HE=%d EN=%d)" % (len(hs), len(es)))
    if re.search(r"[–—]", en):
        problems.append("en/em dash present")
    return problems, en

def en_title(en_html, slug):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", en_html, re.S)
    if m:
        t = re.sub(r"<[^>]+>", "", m.group(1))
        t = re.sub(r"\s+", " ", t).strip().rstrip(".").strip()
        if t:
            return t
    return slug.replace("-", " ").title()

def find_en_page(slug):
    d = B._req("GET", "/wp-json/wp/v2/pages?slug=%s&parent=%d&status=publish,draft&_fields=id,slug" % (slug, EN_PARENT))
    return d[0]["id"] if isinstance(d, list) and d else None

def purge_he(slug):
    m = MAN.get(slug)
    if not m:
        return "no-manifest"
    ep = "pages" if m["type"] == "page" else "posts"
    # re-save with identical content (raw) to trigger SeoEdge purge for that URL
    cur = B._req("GET", "/wp-json/wp/v2/%s/%d?context=edit&_fields=content" % (ep, m["id"]))
    body = cur.get("content", {}).get("raw", "")
    r = B._req("POST", "/wp-json/wp/v2/%s/%d" % (ep, m["id"]), {"content": body})
    return r.get("modified", r)

def publish(slug, do_purge=True):
    problems, en = verify(slug)
    if problems:
        return {"slug": slug, "status": "SKIPPED", "problems": problems}
    body = B.en_ltr_cleanup(B.rewrite_links_en(en))
    title = en_title(en, slug)
    existing = find_en_page(slug)
    r = B.push_en_page(slug, title, body, EN_PARENT, page_id=existing)
    if r.get("_http_error"):
        return {"slug": slug, "status": "ERROR", "resp": str(r)[:300]}
    enid = r.get("id")
    purged = purge_he(slug) if do_purge else "skipped"
    return {"slug": slug, "status": "OK", "en_id": enid, "title": title,
            "link": r.get("link"), "purged_he": str(purged)[:40], "action": "update" if existing else "create"}

def load_ids():
    if os.path.exists(IDS_PATH):
        return json.load(io.open(IDS_PATH, encoding="utf-8"))
    return {}

def save_ids(d):
    json.dump(d, io.open(IDS_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    slugs = sys.argv[1:]
    if not slugs:
        print("usage: publish_en.py <slug> [slug...]  (or 'ALL' for every translated file)")
        sys.exit(1)
    if slugs == ["ALL"]:
        slugs = sorted(s[:-5] for s in os.listdir(os.path.join(HERE, "_i18n", "en")) if s.endswith(".html") and s != "home.html")
    ids = load_ids()
    for s in slugs:
        if not os.path.exists(os.path.join(HERE, "_i18n", "en", s + ".html")):
            print("%-34s MISSING translation" % s); continue
        res = publish(s)
        if res["status"] == "OK":
            ids[s] = res["en_id"]
            print("%-34s OK  id=%s  [%s]  %s" % (s, res["en_id"], res["action"], res["title"][:50]))
        else:
            print("%-34s %s  %s" % (s, res["status"], res.get("problems") or res.get("resp")))
        time.sleep(0.2)
    save_ids(ids)
    print("saved ids for", len(ids), "pages ->", IDS_PATH)
