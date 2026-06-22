# -*- coding: utf-8 -*-
"""Build the מידע מקצועי listing page + 16 article pages for the new Olsi site.
Reads the 16 cached WP-REST JSON files, downloads images locally, fixes internal
links, and renders static HTML using the existing site's header/footer/CTA markup."""
import json, re, os, html, urllib.request, urllib.parse

BASE   = r"C:\Users\bzik2\olsi"
SRC    = os.path.join(BASE, "_src")
BLOG   = os.path.join(BASE, "assets", "blog")
os.makedirs(BLOG, exist_ok=True)

ORDER = ["errors-system-can-solves","business-independence","work-day-before-after",
"streamlining-processes","replace-excel","automation-development-case-study",
"access-outsource-development","access-development-2026","2026-software-development",
"software-dev-high-tech","custom-business-software","gantt-chart","access-to-sql",
"data-scraping","python-developer","legacy-system-modernization"]

# old olsi.co.il URL -> new-site target (trailing-slash variants handled in code)
LINK_MAP = {
    "https://www.olsi.co.il/contact-us/":          "#lets-talk",
    "https://www.olsi.co.il/software-development/": "software-development.html",
    "https://www.olsi.co.il/project-specification/":"preview.html#approach",
    "https://www.olsi.co.il/":                      "preview.html",
}
HE_MONTHS = {1:"ינואר",2:"פברואר",3:"מרץ",4:"אפריל",5:"מאי",6:"יוני",
             7:"יולי",8:"אוגוסט",9:"ספטמבר",10:"אוקטובר",11:"נובמבר",12:"דצמבר"}

# ---------------------------------------------------------------- helpers
def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)

def clean_text(s):
    return re.sub(r"\s+", " ", html.unescape(strip_tags(s))).strip()

def download(url, dest):
    pr = urllib.parse.urlsplit(url)
    safe = urllib.parse.urlunsplit((pr.scheme, pr.netloc,
            urllib.parse.quote(pr.path), urllib.parse.quote(pr.query, safe="=&"), ""))
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return
    req = urllib.request.Request(safe, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=90) as r, open(dest, "wb") as f:
        f.write(r.read())

def ext_of(url):
    path = urllib.parse.urlsplit(url).path
    e = os.path.splitext(path)[1].lower()
    return e if e in (".jpg", ".jpeg", ".png", ".webp", ".gif") else ".jpg"

def map_href(href):
    """Return (new_href, needs_blank)."""
    h = href.strip()
    base = h.rstrip("/")
    cand = None
    for k, v in LINK_MAP.items():
        if h == k or base == k.rstrip("/"):
            cand = v
            break
    if cand is None:
        if "olsi.co.il" in h:
            cand = "preview.html"          # safe fallback for any other internal link
        else:
            cand = h                        # external link: keep as-is
    blank = not (cand.startswith("#") or cand.startswith("tel:") or cand.startswith("mailto:"))
    return cand, blank

# ---------------------------------------------------------------- load existing chrome
with open(os.path.join(BASE, "software-development.html"), encoding="utf-8") as f:
    TPL = f.read()

def slice_between(text, start, end, inclusive_end=False):
    i = text.index(start)
    j = text.index(end, i)
    return text[i:(j + len(end)) if inclusive_end else j]

HEADER  = slice_between(TPL, "<!-- ── HEADER ── -->",
                        '<div class="menu-backdrop" id="menu-backdrop"></div>', True)
# The contact band now lives INSIDE the footer (full-width), so it travels with
# the FOOTER slice - blog pages no longer get a separate standalone CTA band.
FOOTER  = TPL[TPL.index("<!-- ── FOOTER ── -->"):]   # footer (incl. contact band) + float-wa + script + </body></html>

# --- modify chrome for blog pages ---
# 1) no service dropdown item is "active" on a blog page
HEADER = HEADER.replace('class="nav-dd-item is-active"', 'class="nav-dd-item"')
HEADER = HEADER.replace(' aria-current="page"', '')
# 2) add מידע מקצועי to the top nav (after "איך עובדים") - idempotent: the
#    source template may already carry it once build_service_pages.py is updated
if 'professional-info.html' not in HEADER:
    HEADER = HEADER.replace(
        '<a href="preview.html#approach">איך עובדים</a>',
        '<a href="preview.html#approach">איך עובדים</a>\n      <a href="professional-info.html">מידע מקצועי</a>')
# 3) add מידע מקצועי to the footer nav list (anchored on פרויקטים; איך עובדים was removed from the footer)
if 'professional-info.html' not in FOOTER:
    FOOTER = FOOTER.replace(
        '<li><a href="preview.html#work">פרויקטים</a></li>',
        '<li><a href="preview.html#work">פרויקטים</a></li>\n        <li><a href="professional-info.html">מידע מקצועי</a></li>')

def head(title, desc, og_extra=""):
    desc = desc.replace('"', "&quot;")
    return f'''<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#FAF7FF">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:locale" content="he_IL">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{desc}">{og_extra}
<link rel="icon" type="image/png" href="assets/logo-olsi.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<noscript><style>[data-anim]{{opacity:1!important;transform:none!important}}</style></noscript>
<link rel="stylesheet" href="assets/olsi.css">
</head>
<body>
'''

# ---------------------------------------------------------------- process posts
cards = []
log = []
for slug in ORDER:
    with open(os.path.join(SRC, slug + ".json"), encoding="utf-8") as f:
        data = json.load(f)[0]
    title   = clean_text(data["title"]["rendered"])
    content = data["content"]["rendered"]
    dt      = data["date"][:10]
    y, m, d = int(dt[:4]), int(dt[5:7]), int(dt[8:10])
    date_he = f"{d} ב{HE_MONTHS[m]} {y}"

    # remove WP spacer paragraphs
    content = re.sub(r"<p>\s*(?:&nbsp;|&#160;| |\s)*</p>", "", content)

    # drop responsive srcset/sizes (we keep one local copy per image, referenced via src)
    content = re.sub(r'\s+srcset="[^"]*"', '', content)
    content = re.sub(r'\s+sizes="[^"]*"', '', content)

    # featured image
    feat = ""
    try:
        feat = data["_embedded"]["wp:featuredmedia"][0]["source_url"]
    except Exception:
        feat = ""

    # collect content image urls (unique, order-preserving)
    img_urls = []
    for u in re.findall(r'<img[^>]+src="([^"]+)"', content):
        if u not in img_urls:
            img_urls.append(u)

    # decide cover
    cover_url = feat if feat else (img_urls[0] if img_urls else "")
    used_first_as_cover = (not feat) and bool(img_urls)

    def img_base(u):
        n = os.path.splitext(os.path.basename(urllib.parse.urlsplit(u).path))[0]
        return re.sub(r'-\d+x\d+$', '', n)
    feat_base = img_base(feat) if feat else None

    # download cover
    cover_local = ""
    if cover_url:
        cover_local = f"assets/blog/{slug}-cover{ext_of(cover_url)}"
        try:
            download(cover_url, os.path.join(BASE, cover_local.replace('/', os.sep)))
        except Exception as e:
            log.append(f"  !! cover fail {slug}: {e}")
            cover_local = ""

    # download + rewrite inline content images
    for n, u in enumerate(img_urls, 1):
        # skip images that are the same as the cover (author re-embedded the hero in the body)
        if feat_base and img_base(u) == feat_base:
            content = re.sub(r'<img[^>]*' + re.escape(u) + r'[^>]*>', '', content)
            continue
        local = f"assets/blog/{slug}-{n}{ext_of(u)}"
        try:
            download(u, os.path.join(BASE, local.replace('/', os.sep)))
            content = content.replace(u, local)
        except Exception as e:
            log.append(f"  !! img fail {slug} #{n}: {e}")
    # tidy paragraphs left empty after removing a duplicated image
    content = re.sub(r'<p[^>]*>\s*</p>', '', content)

    # if the first inline image became the cover, drop it from the body to avoid duplication
    if used_first_as_cover:
        content = re.sub(r'<img[^>]*>', '', content, count=1)
        # clean now-empty wrapping <p>
        content = re.sub(r"<p[^>]*>\s*</p>", "", content, count=1)

    # add lazy-load + class to remaining imgs
    content = re.sub(r'<img ', '<img loading="lazy" decoding="async" class="post-img" ', content)

    # fix anchors: map internal links, add target/rel
    def _a(mm):
        tag = mm.group(0)
        hm = re.search(r'href="([^"]*)"', tag) or re.search(r"href='([^']*)'", tag)
        if not hm:
            return tag
        new, blank = map_href(hm.group(1))
        if blank:
            return f'<a href="{new}" target="_blank" rel="noopener noreferrer">'
        return f'<a href="{new}">'
    content = re.sub(r'<a\b[^>]*>', _a, content)

    # excerpt: first substantial paragraph
    exc = ""
    for pm in re.findall(r"<p[^>]*>(.*?)</p>", content, flags=re.S):
        t = clean_text(pm)
        if len(t) >= 45:
            exc = t
            break
    if not exc:
        exc = clean_text(data.get("excerpt", {}).get("rendered", ""))
    exc = exc.replace("…", "").strip()
    if len(exc) > 165:
        cut = exc[:165].rsplit(" ", 1)[0]
        exc = cut + "…"

    # ---- render the article page ----
    cover_html = ""
    if cover_local:
        cover_html = (f'\n    <figure class="post-cover">'
                      f'<img src="{cover_local}" alt="{html.escape(title)}" '
                      f'width="1200" loading="eager" decoding="async"></figure>')
    page = head(f"{title} | אולסי מערכות", exc)
    page += HEADER
    page += f'''
<!-- ── POST HERO ── -->
<section class="post-hero">
  <div class="grid-bg" aria-hidden="true"></div>
  <div class="post-hero__inner" data-anim>
    <nav class="breadcrumb" aria-label="ניווט מסלול">
      <a href="preview.html">בית</a>
      <span class="breadcrumb__sep" aria-hidden="true">›</span>
      <a href="professional-info.html">מידע מקצועי</a>
      <span class="breadcrumb__sep" aria-hidden="true">›</span>
      <span class="breadcrumb__current">{html.escape(title)}</span>
    </nav>
    <h1 class="post-hero__title">{html.escape(title)}</h1>
    <div class="post-hero__meta">
      <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>{date_he}</span>
      <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="8" r="4"/><path d="M4 21v-1a6 6 0 0 1 12 0v1"/></svg>אולסי מערכות</span>
    </div>
  </div>
</section>

<!-- ── POST BODY ── -->
<section class="section section--white">
  <div class="post-wrap">{cover_html}
    <div class="post-body" data-anim>
{content}
    </div>
    <div class="post-back">
      <a href="professional-info.html">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14"/><path d="m12 5-7 7 7 7"/></svg>
        חזרה לכל המאמרים
      </a>
    </div>
  </div>
</section>

{FOOTER}'''
    with open(os.path.join(BASE, slug + ".html"), "w", encoding="utf-8") as f:
        f.write(page)

    cards.append({"slug": slug, "title": title, "exc": exc,
                  "cover": cover_local, "date_he": date_he, "iso": dt})
    log.append(f"OK  {slug}  cover={'yes' if cover_local else 'NO'}  imgs={len(img_urls)}  exc={len(exc)}")

# ---------------------------------------------------------------- listing page
card_html = []
for c in cards:
    nt = 'target="_blank" rel="noopener noreferrer"'   # all post links open in a new tab
    media = (f'<a class="post-card__media" href="{c["slug"]}.html" {nt} aria-label="{html.escape(c["title"])}">'
             f'<img src="{c["cover"]}" alt="{html.escape(c["title"])}" loading="lazy" decoding="async"></a>'
             if c["cover"] else
             f'<a class="post-card__media" href="{c["slug"]}.html" {nt} aria-label="{html.escape(c["title"])}"></a>')
    card_html.append(f'''      <article class="post-card" data-anim>
        {media}
        <div class="post-card__body">
          <span class="post-card__date">{c["date_he"]}</span>
          <h2 class="post-card__title"><a href="{c["slug"]}.html" {nt}>{html.escape(c["title"])}</a></h2>
          <p class="post-card__excerpt">{html.escape(c["exc"])}</p>
          <a class="post-card__more btn btn--secondary btn--sm" href="{c["slug"]}.html" {nt}>המשך קריאה
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 12H5"/><path d="m12 19-7-7 7-7"/></svg>
          </a>
        </div>
      </article>''')

listing = head("מידע מקצועי | אולסי מערכות",
               "מאמרים, מדריכים ותובנות על פיתוח תוכנה בהתאמה אישית, שדרוג מערכות ואוטומציה לעסקים - מבית אולסי מערכות, בית תוכנה בוטיק מאז 1995.")
listing += HEADER
listing += '''
<!-- ── BLOG HERO ── -->
<section class="blog-hero">
  <div class="grid-bg" aria-hidden="true"></div>
  <div class="blog-hero__inner" data-anim>
    <p class="eyebrow"><span class="code-comment">knowledge</span></p>
    <h1>מידע <span class="accent">מקצועי</span></h1>
    <p>מאמרים, מדריכים ותובנות מהשטח - על פיתוח תוכנה בהתאמה אישית, שדרוג מערכות ישנות, אוטומציה ואיסוף נתונים. כל מה שלמדנו ב-30 שנה של בניית מערכות לעסקים.</p>
  </div>
</section>

<!-- ── BLOG GRID ── -->
<section class="section section--white">
  <div class="container--wide">
    <div class="blog-grid">
'''
listing += "\n".join(card_html)
listing += '''
    </div>
  </div>
</section>

'''
listing += FOOTER
with open(os.path.join(BASE, "professional-info.html"), "w", encoding="utf-8") as f:
    f.write(listing)

# ---------------------------------------------------------------- report
with open(os.path.join(SRC, "build_report.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(log))
    f.write(f"\n\nGenerated {len(cards)} article pages + professional-info.html")
print("done")
