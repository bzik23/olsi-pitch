import json, glob, re, os, html

order = ["errors-system-can-solves","business-independence","work-day-before-after",
"streamlining-processes","replace-excel","automation-development-case-study",
"access-outsource-development","access-development-2026","2026-software-development",
"software-dev-high-tech","custom-business-software","gantt-chart","access-to-sql",
"data-scraping","python-developer","legacy-system-modernization"]

base = os.path.dirname(__file__)
all_links = {}
for slug in order:
    with open(os.path.join(base, slug+".json"), encoding="utf-8") as f:
        data = json.load(f)[0]
    title = html.unescape(re.sub("<[^>]+>","",data["title"]["rendered"]))
    content = data["content"]["rendered"]
    # featured image
    feat = ""
    try:
        feat = data["_embedded"]["wp:featuredmedia"][0]["source_url"]
    except Exception:
        feat = ""
    # excerpt (strip tags)
    exc = html.unescape(re.sub("<[^>]+>","",data.get("excerpt",{}).get("rendered",""))).strip()
    exc = re.sub(r"\s+"," ",exc)
    # count internal links
    links = re.findall(r'href="([^"]+)"', content)
    internal = [l for l in links if "olsi.co.il" in l]
    imgs = re.findall(r'<img[^>]+src="([^"]+)"', content)
    print("="*70)
    print(f"SLUG: {slug}")
    print(f"TITLE: {title}")
    print(f"FEATURED: {feat}")
    print(f"CONTENT LEN: {len(content)}  IMGS: {len(imgs)}  INTERNAL LINKS: {len(internal)}")
    print(f"EXCERPT: {exc[:200]}")
    for l in internal:
        all_links[l] = all_links.get(l,0)+1

print("\n"+"#"*70)
print("ALL UNIQUE INTERNAL LINKS (olsi.co.il) ACROSS 16 POSTS:")
for l,c in sorted(all_links.items(), key=lambda x:-x[1]):
    print(f"  [{c}x] {l}")
