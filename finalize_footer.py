# -*- coding: utf-8 -*-
"""Post-build finalize step:
  1) inject the full-width footer contact band into the hand-maintained pages
     (homepage + legal pages) that aren't produced by a build script;
  2) generate thank-you.html, reusing the live header/footer chrome so it always
     matches the rest of the site.
Run AFTER build_service_pages.py (which regenerates software-development.html).
The band markup has a single source of truth: build_service_pages.FOOTER_CTA."""
import io, os, re
import build_service_pages as B

BASE = os.path.dirname(os.path.abspath(__file__))
BAND = B.FOOTER_CTA
ANCHOR = '<footer class="site-footer">\n  <div class="footer-grid">'

def read(fn):
    with io.open(os.path.join(BASE, fn), encoding="utf-8") as f:
        return f.read()

def write(fn, s):
    with io.open(os.path.join(BASE, fn), "w", encoding="utf-8", newline="\n") as f:
        f.write(s)

# 1) inject the band into the footer of hand-maintained pages (idempotent) --------
#    case-study-curtains.html is hand-tuned (build_case_studies.py skips it) and
#    still carries the OLD standalone CTA band, so strip that first.
for fn in ["preview.html", "privacy-policy.html", "accessibility-statement.html",
           "case-study-curtains.html"]:
    s = read(fn)
    if "footer-cta" in s:
        print("skip (already has band):", fn); continue
    # drop any standalone CTA band section - it now lives inside the footer
    s = re.sub(r'(?:<!--[^>]*CTA BAND[^>]*-->\s*)?<section class="section cta-band"[^>]*>.*?</section>\s*',
               '', s, flags=re.S)
    if ANCHOR not in s:
        print("WARN anchor not found:", fn); continue
    s = s.replace(ANCHOR, '<footer class="site-footer">\n' + BAND + '\n  <div class="footer-grid">', 1)
    write(fn, s)
    print("band injected:", fn)

# 2) build thank-you.html from the live chrome ------------------------------------
TPL = read("software-development.html")
hi = TPL.index("<!-- ── HEADER ── -->")
mb = '<div class="menu-backdrop" id="menu-backdrop"></div>'
HEADER = TPL[hi:TPL.index(mb, hi) + len(mb)]
# no service-dropdown item is "active" on the thank-you page
HEADER = HEADER.replace('class="nav-dd-item is-active"', 'class="nav-dd-item"').replace(' aria-current="page"', '')
FOOTER = TPL[TPL.index("<!-- ── FOOTER ── -->"):]
# build credit in the footer bottom strip
FOOTER = re.sub(r'<span class="footer-bottom__mono"[^>]*>.*?</span>',
                '<span class="footer-bottom__mono">האתר נבנה ע"י בזיק שיווק דיגיטלי</span>', FOOTER, count=1)

WA = ("https://wa.me/972505534398?text=%d7%94%d7%99%d7%99%2c%20%d7%94%d7%92%d7%a2%d7%aa%d7%99%20"
      "%d7%90%d7%9c%d7%99%d7%9b%d7%9d%20%d7%93%d7%a8%d7%9a%20%d7%94%d7%90%d7%aa%d7%a8...")

HEAD = '''<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#FAF7FF">
<title>תודה שפניתם אלינו | אולסי מערכות</title>
<meta name="description" content="פנייתכם התקבלה ותענה בהקדם. תודה שפניתם לאולסי מערכות - בית תוכנה בוטיק מאז 1995.">
<meta name="robots" content="noindex, follow">
<meta property="og:type" content="website">
<meta property="og:locale" content="he_IL">
<meta property="og:title" content="תודה שפניתם אלינו · אולסי מערכות">
<meta property="og:description" content="פנייתכם התקבלה ותענה בהקדם.">
<link rel="icon" type="image/png" href="assets/logo-olsi-2026.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<noscript><style>[data-anim]{opacity:1!important;transform:none!important}</style></noscript>
<link rel="stylesheet" href="assets/olsi.css">
</head>
<body>

'''

BODY = '''
<!-- ── THANK YOU ── -->
<main class="thanks">
  <div class="grid-bg" aria-hidden="true"></div>
  <div class="thanks__inner" data-anim>
    <div class="thanks__badge" aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
    </div>
    <h1>תודה שפניתם אלינו</h1>
    <p class="thanks__lead">פנייתכם התקבלה ותענה בהקדם.</p>

    <p class="thanks__sub">מה תרצו לעשות עכשיו?</p>
    <div class="thanks__cards">
      <a class="thanks-card" href="preview.html">
        <span class="thanks-card__icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 11.5 12 4l9 7.5"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/></svg></span>
        <span class="thanks-card__txt"><b>חזרה לאתר הבית</b><span>לעמוד הראשי של אולסי מערכות</span></span>
      </a>
      <a class="thanks-card" href="professional-info.html">
        <span class="thanks-card__icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6"/><path d="M8 13h8M8 17h6"/></svg></span>
        <span class="thanks-card__txt"><b>לקריאת מידע מקצועי</b><span>מאמרים, מדריכים ותובנות מהשטח</span></span>
      </a>
      <a class="thanks-card thanks-card--wa" href="''' + WA + '''" target="_blank" rel="noopener">
        <span class="thanks-card__icon"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413z"/></svg></span>
        <span class="thanks-card__txt"><b>להתחלת התכתבות בוואטסאפ</b><span>נדבר עכשיו, בלי להמתין</span></span>
      </a>
    </div>
  </div>
</main>

'''

page = HEAD + HEADER + "\n" + BODY + FOOTER
write("thank-you.html", page)
print("wrote thank-you.html", len(page), "bytes")
