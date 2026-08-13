# -*- coding: utf-8 -*-
"""
Apply English Yoast SEO meta (_yoast_wpseo_title / _yoast_wpseo_metadesc) to every
EN page, so Yoast stops emitting Hebrew <title>/og/schema on the English tree.

Source of titles/descs: _i18n/seo_en.json (crafted, translated from the HE seo_map).
For EN pages not in that map, auto-derive title from the English <h1> + a description
from the first substantial paragraph. Uses the proven code-snippets register-meta pass.
"""
import json, io, os, re
import build_en as B
import deploy_theme as D

HERE = os.path.dirname(__file__)
def _load(p): return json.load(io.open(os.path.join(HERE, p), encoding="utf-8"))

seo_en = _load("_i18n/seo_en.json")
ids = _load("_i18n/en_ids.json")          # slug -> en page id (41, excludes home)
ids["home"] = 3928                         # the "en" page = English home

def derive(slug):
    fn = os.path.join(HERE, "_i18n", "en", ("home" if slug == "home" else slug) + ".html")
    en = io.open(fn, encoding="utf-8").read()
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", en, re.S)
    t = re.sub(r"<[^>]+>", "", h1.group(1)) if h1 else slug.replace("-", " ").title()
    t = re.sub(r"\s+", " ", t).strip().rstrip(".").strip()
    if len(t) > 44:
        t = t[:44].rsplit(" ", 1)[0]
    title = t + " | OLSI Systems"
    desc = ""
    for p in re.findall(r"<p[^>]*>(.*?)</p>", en, re.S):
        txt = re.sub(r"<[^>]+>", "", p); txt = re.sub(r"\s+", " ", txt).strip()
        if len(txt) > 70:
            desc = txt; break
    if len(desc) > 155:
        desc = desc[:152].rsplit(" ", 1)[0] + "..."
    return title, desc

def build_map():
    out = {}
    for slug, enid in ids.items():
        if slug in seo_en and seo_en[slug].get("title") and seo_en[slug].get("desc"):
            out[slug] = {"id": enid, "title": seo_en[slug]["title"], "desc": seo_en[slug]["desc"]}
        else:
            t, d = derive(slug)
            out[slug] = {"id": enid, "title": t, "desc": d, "auto": True}
    return out

REG = ("add_action('init', function(){ foreach(array("
       "'_yoast_wpseo_title','_yoast_wpseo_metadesc','_yoast_wpseo_focuskw',"
       "'_yoast_wpseo_meta-robots-noindex') as $k){ register_post_meta('page', $k, array("
       "'show_in_rest'=>true,'single'=>true,'type'=>'string','auth_callback'=>'__return_true')); } });")

def apply():
    m = build_map()
    sn = D._create_snippet(REG, "olsi-yoast-reg-en")
    sid = sn.get("id")
    print("register snippet:", sid, "err" if "_http_error" in sn else "ok")
    done = 0
    for slug, info in sorted(m.items()):
        meta = {"_yoast_wpseo_title": info["title"], "_yoast_wpseo_metadesc": info["desc"]}
        if slug == "thank-you":
            meta["_yoast_wpseo_meta-robots-noindex"] = "1"
        r = B._req("POST", "/wp-json/wp/v2/pages/%d" % info["id"], {"meta": meta})
        got = r.get("meta", {}).get("_yoast_wpseo_title", "") if isinstance(r, dict) else ""
        ok = "OK" if got == info["title"] else "??(%s)" % str(r.get("_http_error", ""))[:20]
        flag = " [auto]" if info.get("auto") else ""
        print("  %-30s %s  %-55s%s" % (slug, ok, info["title"][:53], flag))
        if got == info["title"]:
            done += 1
    if sid:
        D._delete_snippet(sid)
    print("applied %d/%d ; register snippet removed" % (done, len(m)))

if __name__ == "__main__":
    apply()
