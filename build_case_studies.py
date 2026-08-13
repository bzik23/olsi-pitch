# -*- coding: utf-8 -*-
"""Generator for Olsi case-study pages. Mirrors the hand-built case-study-curtains.html
template (header + svc-hero + overview/fit + solution + results + steps + CTA form + footer).
Run: python build_case_studies.py   ->  writes case-study-*.html for each project below.
Does NOT touch case-study-curtains.html (hand-tuned)."""
import io, os
from build_service_pages import FOOTER_CTA   # single-source full-width footer contact band

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- 40-viewBox feature icons (service-card__icon) ----
IC = {
 "folder": '<path d="M5 10h11l3 4h16v18H5z"/><path d="M5 10v22"/>',
 "login": '<path d="M22 6h9v28h-9"/><path d="M6 20h17"/><path d="m16 13 7 7-7 7"/>',
 "cursor": '<path d="M9 6l20 11-8 2-3 8z"/>',
 "stream": '<path d="M6 13h20"/><path d="m21 7 6 6-6 6"/><path d="M34 27H14"/><path d="m19 21-6 6 6 6"/>',
 "check": '<circle cx="20" cy="20" r="14"/><path d="m13 20 5 5 9-10"/>',
 "clock": '<circle cx="20" cy="20" r="14"/><path d="M20 12v8l6 3"/>',
 "upload": '<path d="M8 28v4a2 2 0 0 0 2 2h20a2 2 0 0 0 2-2v-4"/><path d="M20 6v20"/><path d="m12 14 8-8 8 8"/>',
 "gantt": '<line x1="7" y1="6" x2="7" y2="34"/><rect x="12" y="9" width="15" height="4" rx="1"/><rect x="18" y="18" width="15" height="4" rx="1"/><rect x="12" y="27" width="10" height="4" rx="1"/>',
 "filter": '<path d="M6 8h28L23 21v9l-6 3V21z"/>',
 "doc": '<path d="M10 4h13l7 7v25H10z"/><path d="M23 4v7h7"/><line x1="15" y1="22" x2="29" y2="22"/><line x1="15" y1="28" x2="25" y2="28"/>',
 "cloud": '<path d="M13 31a8 8 0 0 1 .4-16A11 11 0 0 1 33 19a7 7 0 0 1-2 12z"/>',
 "list": '<line x1="15" y1="11" x2="33" y2="11"/><line x1="15" y1="20" x2="33" y2="20"/><line x1="15" y1="29" x2="33" y2="29"/><circle cx="8" cy="11" r="1.8"/><circle cx="8" cy="20" r="1.8"/><circle cx="8" cy="29" r="1.8"/>',
 "dashboard": '<rect x="6" y="6" width="12" height="9" rx="2"/><rect x="22" y="6" width="12" height="14" rx="2"/><rect x="6" y="19" width="12" height="15" rx="2"/><rect x="22" y="24" width="12" height="10" rx="2"/>',
 "users": '<circle cx="14" cy="14" r="5"/><path d="M5 32a9 9 0 0 1 18 0"/><path d="M26 10a5 5 0 0 1 0 10"/><path d="M28 21a9 9 0 0 1 7 11"/>',
 "tablet": '<rect x="9" y="4" width="22" height="32" rx="3"/><line x1="17" y1="31" x2="23" y2="31"/>',
 "stopwatch": '<circle cx="20" cy="22" r="12"/><path d="M20 22v-6"/><path d="M16 4h8"/><path d="m31 11 2-2"/>',
 "progress": '<circle cx="20" cy="20" r="13"/><path d="M20 20l7-4"/><path d="M20 20v-13"/>',
 "sliders": '<line x1="8" y1="13" x2="32" y2="13"/><line x1="8" y1="27" x2="32" y2="27"/><circle cx="16" cy="13" r="3.4"/><circle cx="26" cy="27" r="3.4"/>',
 "user": '<circle cx="20" cy="13" r="6"/><path d="M8 34a12 12 0 0 1 24 0"/>',
 "shieldpay": '<path d="M20 5l13 5v9c0 8-5 13-13 16-8-3-13-8-13-16v-9z"/><path d="m14 19 4 4 8-9"/>',
 "track": '<path d="M20 34s11-9 11-18a11 11 0 0 0-22 0c0 9 11 18 11 18z"/><circle cx="20" cy="16" r="4"/>',
 "search": '<circle cx="17" cy="17" r="10"/><line x1="24.5" y1="24.5" x2="33" y2="33"/>',
 "cube": '<path d="M6 13 20 6l14 7v14L20 34 6 27z"/><path d="M6 13l14 7 14-7M20 20v14"/>',
 "calc": '<rect x="9" y="5" width="22" height="30" rx="3"/><line x1="13" y1="11" x2="27" y2="11"/><circle cx="14" cy="20" r="1.5"/><circle cx="20" cy="20" r="1.5"/><circle cx="26" cy="20" r="1.5"/><circle cx="14" cy="27" r="1.5"/><circle cx="20" cy="27" r="1.5"/><circle cx="26" cy="27" r="1.5"/>',
 "sync": '<path d="M8 20a12 12 0 0 1 20-9l5 4"/><path d="M33 8v7h-7"/><path d="M32 20a12 12 0 0 1-20 9l-5-4"/><path d="M7 32v-7h7"/>',
 "devices": '<rect x="5" y="9" width="20" height="14" rx="2"/><rect x="27" y="13" width="9" height="18" rx="2"/><line x1="9" y1="28" x2="18" y2="28"/>',
 "plane": '<path d="M34 6 6 18l11 4 4 11z"/><path d="M34 6 17 22"/>',
}

# ---- 24-viewBox small icons (hero meta + benefits) ----
SM = {
 "ind":  '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18"/>',
 "code": '<path d="m9 13-2 2 2 2"/><path d="m13 13 2 2-2 2"/><rect x="3" y="4" width="18" height="16" rx="2"/>',
 "year": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
 "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/><path d="M12 3v3M12 18v3M3 12h3M18 12h3"/>',
 "trend": '<path d="M3 17l6-6 4 4 7-7"/><path d="M17 8h4v4"/>',
 "shield": '<path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6z"/><path d="M9.5 12l2 2 3.5-4"/>',
 "bolt": '<path d="M13 2 4 14h6l-1 8 9-12h-6z"/>',
 "sync": '<path d="M3 12a9 9 0 0 1 15-6.7L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-15 6.7L3 16"/><path d="M3 21v-5h5"/>',
 "eye": '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
 "share": '<circle cx="6" cy="12" r="3"/><circle cx="18" cy="6" r="3"/><circle cx="18" cy="18" r="3"/><path d="m8.6 10.7 6.8-3.4M8.6 13.3l6.8 3.4"/>',
 "gauge": '<path d="M4 18a8 8 0 1 1 16 0"/><path d="M12 18l5-5"/><circle cx="12" cy="18" r="1.6"/>',
 "cursor": '<path d="M5 3l7 16 2.6-6.4L21 10z"/>',
 "money": '<circle cx="12" cy="12" r="9"/><path d="M12 7v10M9.5 9.6h4a1.7 1.7 0 0 1 0 3.4h-3a1.7 1.7 0 0 0 0 3.4h4.2"/>',
}

def feat(icon):
    return ('<svg class="service-card__icon" viewBox="0 0 40 40" fill="none" stroke="currentColor" '
            'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            + IC[icon] + '</svg>')

def sm(icon):
    return ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + SM[icon] + '</svg>')

HEAD = '''<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#FAF7FF">
<title>@@TITLE@@</title>
<meta name="description" content="@@DESC@@">
<meta property="og:type" content="article">
<meta property="og:locale" content="he_IL">
<meta property="og:title" content="@@OGTITLE@@">
<meta property="og:description" content="@@OGDESC@@">
<link rel="icon" type="image/png" href="assets/logo-olsi-2026.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<noscript><style>[data-anim]{opacity:1!important;transform:none!important}</style></noscript>
<link rel="stylesheet" href="assets/olsi.css">
</head>
<body>

<!-- HEADER -->
<header class="site-header" id="site-header">
  <div class="site-header__inner">
    <a href="preview.html" class="site-header__brand" aria-label="אולסי מערכות · דף הבית">
      <img src="assets/logo-olsi-2026.png" alt="אולסי מערכות" height="38" width="auto" loading="eager" decoding="async">
      <span class="site-header__subtag" dir="ltr">OLSI · est. 1995</span>
    </a>
    <nav class="site-header__nav" id="site-nav" aria-label="ניווט ראשי">
      <a href="preview.html">דף הבית</a>
      <a href="preview.html#about">אודות</a>
      <div class="nav-has-dropdown" id="nav-services">
        <a href="preview.html#services" class="nav-dropdown__trigger" aria-haspopup="true" aria-expanded="false">
          שירותים
          <svg class="nav-dropdown__chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="6 9 12 15 18 9"/></svg>
        </a>
        <div class="nav-dropdown__panel" role="menu" aria-label="שירותים">
          <div class="nav-dropdown__grid">
            <a class="nav-dd-item" href="software-development.html" role="menuitem">
              <span class="nav-dd-item__icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 8.5h18"/><path d="m9 13-2 2 2 2"/><path d="m13 13 2 2-2 2"/></svg></span>
              <span class="nav-dd-item__text"><span class="nav-dd-item__title">פיתוח תוכנה</span><span class="nav-dd-item__sub">מערכות עסקיות מותאמות לעסק שלכם</span></span>
            </a>
            <a class="nav-dd-item" href="app-development.html" role="menuitem">
              <span class="nav-dd-item__icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6.5" y="3" width="11" height="18" rx="2.5"/><path d="M11 18h2"/></svg></span>
              <span class="nav-dd-item__text"><span class="nav-dd-item__title">פיתוח אפליקציה</span><span class="nav-dd-item__sub">אפליקציות מובייל לאנדרואיד ול-iOS</span></span>
            </a>
            <a class="nav-dd-item" href="crm-development.html" role="menuitem">
              <span class="nav-dd-item__icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M16 19v-1a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v1"/><circle cx="9.5" cy="7.5" r="3"/><path d="M21 19v-1a4 4 0 0 0-3-3.87"/><path d="M15.5 4.6a3 3 0 0 1 0 5.8"/></svg></span>
              <span class="nav-dd-item__text"><span class="nav-dd-item__title">פיתוח מערכת CRM</span><span class="nav-dd-item__sub">ניהול לקוחות, לידים ותהליכי מכירה</span></span>
            </a>
            <a class="nav-dd-item" href="excel-upgrade.html" role="menuitem">
              <span class="nav-dd-item__icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M3 14.5h18M9 4v16M15 4v16"/></svg></span>
              <span class="nav-dd-item__text"><span class="nav-dd-item__title">שדרוג מאקסל למערכת חכמה</span><span class="nav-dd-item__sub">מגיליונות Excel לפלטפורמה יציבה</span></span>
            </a>
            <a class="nav-dd-item" href="access-upgrade.html" role="menuitem">
              <span class="nav-dd-item__icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v6c0 1.66 3.13 3 7 3s7-1.34 7-3V6"/><path d="M5 12v6c0 1.66 3.13 3 7 3s7-1.34 7-3v-6"/></svg></span>
              <span class="nav-dd-item__text"><span class="nav-dd-item__title">שדרוג מאקסס לתוכנה חכמה</span><span class="nav-dd-item__sub">ממסד Access ישן למערכת מודרנית</span></span>
            </a>
            <a class="nav-dd-item" href="inventory-system.html" role="menuitem">
              <span class="nav-dd-item__icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3.5 8.5 12 4l8.5 4.5v7L12 20l-8.5-4.5z"/><path d="M3.5 8.5 12 13l8.5-4.5M12 13v7"/></svg></span>
              <span class="nav-dd-item__text"><span class="nav-dd-item__title">מערכת לניהול מלאים</span><span class="nav-dd-item__sub">מעקב מלאי, ספקים והזמנות</span></span>
            </a>
            <a class="nav-dd-item" href="custom-systems.html" role="menuitem">
              <span class="nav-dd-item__icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="8" height="8" rx="1.5"/><rect x="13" y="3" width="8" height="8" rx="1.5"/><rect x="3" y="13" width="8" height="8" rx="1.5"/><rect x="13" y="13" width="8" height="8" rx="1.5"/></svg></span>
              <span class="nav-dd-item__text"><span class="nav-dd-item__title">מערכות מותאמות אישית</span><span class="nav-dd-item__sub">פתרון שנבנה סביב התהליך שלכם</span></span>
            </a>
            <a class="nav-dd-item" href="integrations-api.html" role="menuitem">
              <span class="nav-dd-item__icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="6" cy="12" r="2.5"/><circle cx="18" cy="6" r="2.5"/><circle cx="18" cy="18" r="2.5"/><path d="M8.2 10.8 15.8 7.2M8.2 13.2l7.6 3.6"/></svg></span>
              <span class="nav-dd-item__text"><span class="nav-dd-item__title">אינטגרציות ו-API</span><span class="nav-dd-item__sub">חיבור בין מערכות כך שמידע זורם אוטומטית</span></span>
            </a>
            <a class="nav-dd-item" href="data-processing.html" role="menuitem">
              <span class="nav-dd-item__icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 5h18l-7 8.5V20l-4-2v-4.5z"/></svg></span>
              <span class="nav-dd-item__text"><span class="nav-dd-item__title">איסוף ועיבוד נתונים</span><span class="nav-dd-item__sub">סקרייפינג, פייפליינים ודוחות אוטומטיים</span></span>
            </a>
            <a class="nav-dd-item" href="tech-support.html" role="menuitem">
              <span class="nav-dd-item__icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="3"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3M5.1 5.1l2.1 2.1M16.8 16.8l2.1 2.1M18.9 5.1l-2.1 2.1M7.2 16.8l-2.1 2.1"/></svg></span>
              <span class="nav-dd-item__text"><span class="nav-dd-item__title">ליווי טכני שוטף</span><span class="nav-dd-item__sub">שירות, תחזוקה ושיפורים אחרי ההשקה</span></span>
            </a>
            <a class="nav-dd-cta" href="#lets-talk" role="menuitem">
              <span class="nav-dd-cta__txt"><b>לא בטוחים מה צריך?</b> נשמח לייעץ ולכוון אתכם.</span>
              <span class="nav-dd-cta__go">דברו איתנו ›</span>
            </a>
          </div>
        </div>
      </div>
      <a href="preview.html#work">פרויקטים</a>
      <a href="preview.html#approach">איך עובדים</a>
      <a href="#lets-talk">צרו קשר</a>
    </nav>
    <div class="site-header__cta">
      <a href="tel:098820511" class="site-header__phone" dir="ltr">09-8820511</a>
      <a href="https://wa.me/972505534398?text=%d7%94%d7%99%d7%99%2c%20%d7%94%d7%92%d7%a2%d7%aa%d7%99%20%d7%90%d7%9c%d7%99%d7%9b%d7%9d%20%d7%93%d7%a8%d7%9a%20%d7%94%d7%90%d7%aa%d7%a8..." class="site-header__wa" target="_blank" rel="noopener" aria-label="שלחו לנו הודעת ווטסאפ">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413z"/></svg>
        <span class="sr-only">ווטסאפ</span>
      </a>
      <button class="hamburger" id="hamburger" aria-expanded="false" aria-controls="site-nav" aria-label="תפריט">
        <span class="hamburger__bars"><span></span></span>
      </button>
    </div>
  </div>
</header>
<div class="menu-backdrop" id="menu-backdrop"></div>
'''
CTA_FOOTER = '''
<!-- FOOTER -->
<footer class="site-footer">
''' + FOOTER_CTA + '''
  <div class="footer-grid">
    <div class="footer-brand">
      <img src="assets/logo-olsi-2026.png" alt="אולסי מערכות" height="32" width="auto">
      <p>בית תוכנה בוטיק מאז 1995. מערכות שמדברות זו עם זו.</p>
      <span class="footer-sub" dir="ltr">OLSI · est. 1995</span>
    </div>
    <div class="footer-col">
      <h4>ניווט</h4>
      <ul>
        <li><a href="preview.html">דף הבית</a></li>
        <li><a href="preview.html#about">אודות</a></li>
        <li><a href="preview.html#services">שירותים</a></li>
        <li><a href="preview.html#work">פרויקטים</a></li>
        <li><a href="#lets-talk">צרו קשר</a></li>
      </ul>
    </div>
    <div class="footer-col">
      <h4>שירותים</h4>
      <ul>
        <li><a href="software-development.html">פיתוח תוכנה</a></li>
        <li><a href="app-development.html">פיתוח אפליקציה</a></li>
        <li><a href="crm-development.html">פיתוח מערכת CRM</a></li>
        <li><a href="excel-upgrade.html">שדרוג מאקסל למערכת חכמה</a></li>
        <li><a href="access-upgrade.html">שדרוג מאקסס לתוכנה חכמה</a></li>
        <li><a href="inventory-system.html">מערכת לניהול מלאים</a></li>
        <li><a href="custom-systems.html">מערכות מותאמות אישית</a></li>
        <li><a href="integrations-api.html">אינטגרציות ו-API</a></li>
        <li><a href="data-processing.html">איסוף ועיבוד נתונים</a></li>
        <li><a href="tech-support.html">ליווי טכני שוטף</a></li>
      </ul>
    </div>
    <div class="footer-col">
      <h4>צרו קשר</h4>
      <ul>
        <li><a href="tel:098820511" dir="ltr">09-8820511</a></li>
        <li><a href="mailto:info@olsi.co.il" dir="ltr">info@olsi.co.il</a></li>
        <li><span class="footer-static">ישראל</span></li>
        <li><a href="privacy-policy.html">מדיניות פרטיות</a></li>
        <li><a href="accessibility-statement.html">הצהרת נגישות</a></li>
      </ul>
    </div>
  </div>
  <div class="footer-bottom">
    <span class="footer-bottom__copy">© 2026 אולסי מערכות · כל הזכויות שמורות</span>
    <span class="footer-bottom__mono">האתר נבנה ע"י בזיק שיווק דיגיטלי</span>
  </div>
</footer>

<!-- FLOATING WHATSAPP -->
<a class="float-wa"
   href="https://wa.me/972505714405?text=%D7%94%D7%99%D7%99%2C%20%D7%94%D7%92%D7%A2%D7%AA%D7%99%20%D7%93%D7%A8%D7%9A%20%D7%94%D7%90%D7%AA%D7%A8"
   target="_blank" rel="noopener"
   aria-label="WhatsApp · 050-571-4405">
  <span class="float-wa__pulse" aria-hidden="true"></span>
  <svg viewBox="0 0 24 24" fill="#fff" aria-hidden="true"><path d="M20.5 3.5A11 11 0 0 0 3.7 17.3L2 22l4.8-1.6A11 11 0 1 0 20.5 3.5zM12 20.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-2.9 1 1-2.8-.2-.3a8.2 8.2 0 1 1 6.6 3.5z"/></svg>
</a>

<script src="assets/olsi.js" defer></script>
</body>
</html>'''
STD_STEPS = [
  ("אפיון עמוק", "יושבים עם הצוות וממפים את זרימת המידע האמיתית - מי עושה מה, מתי, ואיפה הדברים נתקעים."),
  ("זיהוי צווארי בקבוק", "מאתרים בדיוק את הנקודות שבהן נוצרות טעויות, כפילויות ועיכובים - שם נמצא הערך הגדול."),
  ("פיתוח מותאם", "בונים את המערכת סביב התהליך שלכם, מודול אחרי מודול, עם בדיקות לאורך כל הדרך."),
  ("הטמעה וליווי", "מעלים לאוויר, מדריכים את הצוות, ונשארים זמינים גם אחרי ההשקה להמשך שיפור והרחבה."),
]

def hero(p):
    meta = "\n".join(
        f'        <span>{sm(k)}{t}</span>' for k, t in p["meta"])
    kpis = "".join(
        f'<div class="ui-mock__kpi"><b>{b}</b><span>{s}</span></div>' for b, s in p["kpis"])
    return f'''
<!-- CASE STUDY HERO -->
<section class="svc-hero" id="top">
  <div class="grid-bg" aria-hidden="true"></div>
  <div class="hero__mesh" aria-hidden="true">
    <svg viewBox="0 0 600 600" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="mesh-1" cx="180" cy="220" r="320" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stop-color="#9333EA" stop-opacity=".22"/>
          <stop offset="60%" stop-color="#9333EA" stop-opacity="0"/>
        </radialGradient>
        <radialGradient id="mesh-2" cx="440" cy="380" r="300" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stop-color="#DB2777" stop-opacity=".18"/>
          <stop offset="60%" stop-color="#DB2777" stop-opacity="0"/>
        </radialGradient>
      </defs>
      <rect x="0" y="0" width="600" height="600" fill="url(#mesh-1)"/>
      <rect x="0" y="0" width="600" height="600" fill="url(#mesh-2)"/>
    </svg>
  </div>
  <div class="svc-hero__inner">
    <div class="svc-hero__left">
      <nav class="breadcrumb" aria-label="ניווט מסלול">
        <a href="preview.html">בית</a>
        <span class="breadcrumb__sep" aria-hidden="true">›</span>
        <a href="preview.html#work">פרויקטים</a>
        <span class="breadcrumb__sep" aria-hidden="true">›</span>
        <span class="breadcrumb__current">{p["crumb"]}</span>
      </nav>
      <span class="svc-hero__eyebrow"><span class="code-comment">{p["eyebrow"]}</span></span>
      <h1 class="svc-hero__title">{p["h1p"]} <span class="accent">{p["h1a"]}</span></h1>
      <p class="svc-hero__sub">{p["sub"]}</p>
      <div class="svc-hero__actions">
        <a href="#lets-talk" class="btn btn--primary btn--lg">תיאום שיחת ייעוץ</a>
        <a href="preview.html#work" class="btn btn--ghost btn--lg">חזרה לכל הפרויקטים</a>
      </div>
      <div class="svc-hero__meta">
{meta}
      </div>
    </div>
    <div class="svc-hero__visual" aria-hidden="true">
      <div class="ui-mock">
        <div class="ui-mock__bar">
          <span class="ui-mock__dot ui-mock__dot--r"></span>
          <span class="ui-mock__dot ui-mock__dot--y"></span>
          <span class="ui-mock__dot ui-mock__dot--g"></span>
          <span class="ui-mock__tab">{p["tab"]}</span>
        </div>
        <div class="ui-mock__body">
          <div class="ui-mock__side"><i></i><i></i><i></i><i></i><i></i></div>
          <div class="ui-mock__main">
            <div class="ui-mock__kpis">{kpis}</div>
            <div class="ui-mock__chart"><i></i><i></i><i></i><i></i><i></i><i></i></div>
            <div class="ui-mock__rows"><span class="ui-mock__row"></span><span class="ui-mock__row"></span><span class="ui-mock__row"></span></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>
'''

def chk():
    return ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>')

def overview(p):
    fit = "\n".join(f'          <li>{chk()}{x}</li>' for x in p["fit"])
    return f'''
<!-- OVERVIEW / THE CHALLENGE -->
<section class="section section--white">
  <div class="container--wide">
    <div class="overview__grid">
      <div class="overview__body" data-anim>
        <p class="eyebrow"><span class="code-comment">overview</span></p>
        <h2>הסיפור מאחורי הפרויקט.</h2>
        <p>{p["ov_p1"]}</p>
        <p>{p["ov_p2"]}</p>
      </div>
      <aside class="fit-card" data-anim>
        <h3>{p["fit_h3"]}</h3>
        <ul class="checklist">
{fit}
        </ul>
      </aside>
    </div>
  </div>
</section>
'''

def solution(p):
    cards = "\n".join(
        f'''      <article class="service-card" data-anim>
        {feat(ic)}
        <h3>{t}</h3>
        <p>{d}</p>
      </article>''' for ic, t, d in p["feats"])
    return f'''
<!-- THE SOLUTION -->
<section class="services section section--alt">
  <div class="container--wide">
    <div class="section-header section-header--center" data-anim>
      <p class="eyebrow"><span class="code-comment">the solution</span></p>
      <h2 class="section-title">{p["sol_h2"]}</h2>
      <p class="section-sub">{p["sol_sub"]}</p>
    </div>
    <div class="services__grid">
{cards}
    </div>
  </div>
</section>
'''

def results(p):
    bens = "\n".join(
        f'''      <div class="benefit" data-anim>
        <div class="benefit__ic">{sm(k)}</div>
        <h3>{t}</h3>
        <p>{d}</p>
      </div>''' for k, t, d in p["bens"])
    return f'''
<!-- RESULTS -->
<section class="section section--white">
  <div class="container--wide">
    <div class="section-header section-header--center" data-anim>
      <p class="eyebrow"><span class="code-comment">results</span></p>
      <h2 class="section-title">{p["res_h2"]}</h2>
      <p class="section-sub">{p["res_sub"]}</p>
    </div>
    <div class="benefits__grid">
{bens}
    </div>
  </div>
</section>
'''

def steps(p):
    items = p.get("steps", STD_STEPS)
    lis = "\n".join(
        f'''      <li class="step" data-anim>
        <span class="step__n" dir="ltr">{i+1}</span>
        <h3>{t}</h3>
        <p>{d}</p>
      </li>''' for i, (t, d) in enumerate(items))
    return f'''
<!-- APPROACH / HOW WE WORKED -->
<section class="section section--alt">
  <div class="container--wide">
    <div class="section-header section-header--center" data-anim>
      <p class="eyebrow"><span class="code-comment">our approach</span></p>
      <h2 class="section-title">איך בנינו את המערכת</h2>
      <p class="section-sub">{p["appr_sub"]}</p>
    </div>
    <ol class="steps">
{lis}
    </ol>
    <div class="steps__foot" data-anim>
      <a href="{p["svc_link"]}" class="btn btn--secondary">{p["svc_label"]}</a>
    </div>
  </div>
</section>
'''

def build(p):
    head = (HEAD.replace("@@TITLE@@", p["title"]).replace("@@DESC@@", p["desc"])
                .replace("@@OGTITLE@@", p["ogtitle"]).replace("@@OGDESC@@", p["ogdesc"]))
    foot = CTA_FOOTER.replace("@@MONO@@", p["mono"])
    return head + hero(p) + overview(p) + solution(p) + results(p) + steps(p) + foot

PROJECTS = [
 {
  "slug": "case-study-selenium",
  "title": "אוטומציה להזנת הזמנות (Selenium) | פרויקט · אולסי מערכות",
  "desc": "פרויקט אוטומציה: תוכנת דסקטופ שמזינה הזמנות מקובצי אקסל אל אתר ספק ללא API - וחוסכת ללקוח משכורת עובד מלאה. אולסי מערכות, בית תוכנה בוטיק מאז 1995.",
  "ogtitle": "אוטומציה להזנת הזמנות · אולסי מערכות",
  "ogdesc": "תוכנת דסקטופ שמזינה הזמנות מאקסל לאתר ללא API - חיסכון של עובד שלם והחזר השקעה תוך חודשים.",
  "crumb": "אוטומציה להזנת הזמנות",
  "eyebrow": "case study · automation",
  "h1p": "אוטומציה שמזינה הזמנות לבד",
  "h1a": "במקום שעות של הקלדה ידנית.",
  "sub": "לקוח נאלץ להזין ידנית הזמנות מורכבות מתוך קובצי אקסל ארוכים אל אתר ספק שאין לו API. בנינו תוכנת דסקטופ שעושה את כל העבודה הזו לבד - מדויק, מהיר, ומשלם על עצמו תוך חודשים.",
  "meta": [("ind","ענף · הזנת הזמנות"),("code","טכנולוגיה · Selenium"),("year","פרויקט · 2023")],
  "tab": "autofill.app",
  "kpis": [("100%","AUTOMATED"),("1","FTE SAVED"),("0","TYPOS")],
  "ov_p1": "לפעמים צוואר הבקבוק הוא לא תהליך חכם, אלא פשוט הקלדה. אצל הלקוח, כל הזמנה הגיעה כקובץ אקסל ארוך והייתה צריכה להיות מוזנת ידנית, שורה אחר שורה, לתוך אתר של ספק שלא חשף שום API להתממשקות.",
  "ov_p2": "זה גזל שעות עבודה יקרות בכל יום, היה משעמם ונוטה לטעויות, ודרש עובד שכל תפקידו העתקה והדבקה. חיפשנו דרך לתת למחשב לעשות את זה במקום בן אדם.",
  "fit_h3": "מה זיהינו באפיון:",
  "fit": [
    "הזמנות ארוכות מוזנות ידנית מאקסל אל אתר חיצוני.",
    "לאתר הספק אין API, אז אין דרך נקייה להתממשק.",
    "העבודה חוזרת, משעממת ונוטה לטעויות הקלדה.",
    "שעות יקרות של עובד מושקעות בהעתקה והדבקה.",
  ],
  "sol_h2": "מה בנינו.",
  "sol_sub": "תוכנת דסקטופ פשוטה שמדמה משתמש אמיתי מול האתר ומזינה את ההזמנות במקומכם - מדויק, מהיר ובלי להתעייף.",
  "feats": [
    ("folder","בחירת קובץ אקסל","בוחרים את קובץ ההזמנה הרצוי בלחיצה, והתוכנה קוראת ממנו את כל הנתונים."),
    ("login","התחברות אוטומטית","התוכנה נכנסת לאתר הספק ומתחברת עם פרטי המשתמש, בלי התערבות ידנית."),
    ("cursor","ניווט חכם בין מסכים","היא מגיעה בדיוק לעמודים הנכונים באתר, כמו שעובד מנוסה היה עושה."),
    ("stream","הזרמת הנתונים","שדה אחרי שדה, ההזמנה מוזנת מהאקסל לתוך הטופס באתר במהירות."),
    ("check","בלי טעויות הקלדה","מה שכתוב באקסל מגיע לאתר בדיוק - בלי שגיאות אנוש."),
    ("clock","ריצה ללא השגחה","מפעילים ושוכחים. התוכנה עובדת לבד בזמן שהצוות עוסק בדברים חשובים."),
  ],
  "res_h2": "התוצאות, בזמן ובכסף.",
  "res_sub": 'הקלדה שלמה הפכה לאוטומציה: <span class="accent">חיסכון של משכורת עובד מלאה</span>, והחזר על עלות הפיתוח תוך חודשים בודדים.',
  "bens": [
    ("money","חיסכון של עובד שלם","העבודה שדרשה כוח אדם ייעודי נעשית עכשיו אוטומטית, מקצה לקצה."),
    ("trend","מהירות ודיוק","מה שלקח שעות נעשה בדקות, בלי טעויות הקלדה ובלי תלות באדם."),
    ("sync","החזר השקעה מהיר","התוכנה החזירה את עלות הפיתוח תוך חודשים, וממשיכה לחסוך מאז."),
  ],
  "appr_sub": "אנחנו מתאימים את התוכנה אליכם, לא הפוך. קודם מבינים לעומק איך העבודה זורמת באמת, ורק אז כותבים שורת קוד.",
  "svc_link": "data-processing.html",
  "svc_label": "עוד על איסוף ועיבוד נתונים",
  "mono": "case study · selenium automation",
 },
 {
  "slug": "case-study-gantt",
  "title": "מערכת לניהול לוחות זמנים GANTT בבנייה | פרויקט · אולסי מערכות",
  "desc": "פלטפורמת SaaS שמייבאת קובצי Microsoft Project והופכת אותם לתרשימי גאנט דינמיים, מסוננים וברורים, עם ייצוא ל-PDF ואקסל. אולסי מערכות, בית תוכנה בוטיק מאז 1995.",
  "ogtitle": "מערכת לניהול לוחות זמנים GANTT · אולסי מערכות",
  "ogdesc": "מ-Microsoft Project לדשבורד גאנט חי בשניות: סינון, מיון, שיתוף וייצוא ל-PDF ואקסל.",
  "crumb": "ניהול לוחות זמנים GANTT בבנייה",
  "eyebrow": "case study · construction",
  "h1p": "לוחות זמנים של פרויקטי בנייה",
  "h1a": "הופכים לדשבורד חי בשניות.",
  "sub": "חברות בנייה מנהלות לוחות זמנים מורכבים בקובצי Microsoft Project כבדים. בנינו פלטפורמת SaaS שמייבאת את הקבצים האלה והופכת אותם לתרשימי גאנט דינמיים, מסוננים וברורים - תוך שניות, מכל דפדפן.",
  "meta": [("ind","ענף · בנייה ותשתיות"),("code","טכנולוגיה · Web SaaS"),("year","פרויקט · 2023")],
  "tab": "gantt.webit",
  "kpis": [("SaaS","CLOUD"),("PDF","EXPORT"),("sec","LOAD")],
  "ov_p1": "בפרויקט בנייה גדול, לוח הזמנים הוא הלב. אבל קובצי Microsoft Project כבדים, קשים לשיתוף, וכמעט בלתי אפשריים לסנן ולהבין במבט מהיר - בטח לא בשטח או מול לקוח.",
  "ov_p2": "חברות הבנייה רצו דרך להפוך את הקבצים האלה למשהו חי: תרשים שאפשר לסנן, למיין, לשתף ולהדפיס - בלי להתקין תוכנה כבדה ובלי תלות במומחה.",
  "fit_h3": "מה זיהינו באפיון:",
  "fit": [
    "לוחות הזמנים יושבים בקובצי Microsoft Project כבדים.",
    "קשה לסנן, למיין ולהבין את התמונה במבט מהיר.",
    "שיתוף הלוח עם שותפים ולקוחות מסורבל.",
    "אין דרך נוחה להפיק פלט מסודר ל-PDF או לאקסל.",
  ],
  "sol_h2": "מה בנינו.",
  "sol_sub": "פלטפורמת ענן (SaaS) שמייבאת קובצי Microsoft Project והופכת אותם לתרשימי גאנט דינמיים, יפים וברורים - נגישים מכל דפדפן.",
  "feats": [
    ("upload","ייבוא מ-Microsoft Project","מעלים את הקובץ הקיים, והמערכת קוראת ממנו את כל המשימות והתאריכים."),
    ("gantt","תרשים גאנט דינמי","לוח הזמנים הופך לתרשים חי, ויזואלי וברור - במקום טבלה אינסופית."),
    ("filter","סינון ומיון גמיש","מסננים לפי כל פרמטר וממיינים בלחיצה, ורואים בדיוק את מה שחשוב עכשיו."),
    ("clock","תוצאות בשניות","כל שינוי ותצוגה מתעדכנים על המסך כמעט מיידית."),
    ("doc","ייצוא ל-PDF ואקסל","מפיקים פלט מסודר לשיתוף, לדיווח או להדפסה - בלחיצה."),
    ("cloud","ענן ושיתוף","SaaS בענן: נכנסים מכל מקום ומשתפים שותפים ולקוחות בקלות."),
  ],
  "res_h2": "התוצאה: שליטה מלאה בלוח הזמנים.",
  "res_sub": 'במקום קבצים כבדים - <span class="accent">תמונה אחת ברורה</span> של כל הפרויקט, לכל בעלי העניין, בכל רגע.',
  "bens": [
    ("eye","בהירות מיידית","כל מי שמסתכל מבין את מצב הפרויקט בשנייה, בלי לפענח טבלאות."),
    ("share","שיתוף קל","שותפים, קבלני משנה ולקוחות מקבלים גישה לתמונה עדכנית."),
    ("sync","חיסכון בזמן","מה שדרש שעות עבודה עם Project נעשה עכשיו בכמה לחיצות."),
  ],
  "appr_sub": "קודם מבינים איך מנהלי הפרויקטים עובדים באמת מול לוחות הזמנים, ורק אז בונים את הכלי שמתאים להם בדיוק.",
  "svc_link": "custom-systems.html",
  "svc_label": "עוד על מערכות מותאמות אישית",
  "mono": "case study · gantt scheduling",
 },
 {
  "slug": "case-study-production",
  "title": "מערכת לניהול הייצור במפעל אלקטרוניקה (MES) | פרויקט · אולסי מערכות",
  "desc": "מערכת MES לניהול ייצור: דשבורד פקודות עבודה, הקצאת משימות, טאבלט בקו הייצור, מעקב זמני ביצוע וזיהוי זמני מתה. אולסי מערכות, בית תוכנה בוטיק מאז 1995.",
  "ogtitle": "מערכת לניהול הייצור במפעל אלקטרוניקה · אולסי מערכות",
  "ogdesc": "דשבורד ייצור בזמן אמת, הקצאת משימות לעובדים, טאבלט בקו הייצור ומעקב זמני מתה.",
  "crumb": "ניהול הייצור במפעל אלקטרוניקה",
  "eyebrow": "case study · manufacturing",
  "h1p": "ניהול ייצור חכם",
  "h1a": "ממפעל אלקטרוניקה לדשבורד אחד.",
  "sub": "בנינו למפעל אלקטרוניקה מערכת לניהול הייצור (MES) שמרכזת את כל פקודות העבודה, מציגה אותן על דשבורד ברור, ומאפשרת לכל עובד לראות את המשימות שלו בזמן אמת - על טאבלט, בקו הייצור.",
  "meta": [("ind","ענף · תעשייה ואלקטרוניקה"),("code","טכנולוגיה · MES"),("year","פרויקט · 2024")],
  "tab": "mes.factory",
  "kpis": [("LIVE","STATUS"),("0","DEAD TIME"),("%","PER WORKER")],
  "ov_p1": "ברצפת ייצור כל דקה נספרת. אבל בלי מערכת קשה לדעת מה הסטטוס של כל פקודת עבודה, מי עובד על מה, וכמה זמן באמת לוקח כל שלב - וזמני מתה מצטברים בלי שאף אחד שם לב.",
  "ov_p2": "המפעל רצה תמונה אחת, בזמן אמת, של כל הייצור: מה מאושר, מה בעבודה, מה הסתיים ואיפה נתקעים. וגם לתת לכל עובד בקו לראות בדיוק מה הוא צריך לעשות.",
  "fit_h3": "מה זיהינו באפיון:",
  "fit": [
    "אין תמונה אחת בזמן אמת של סטטוס הייצור.",
    "קשה לדעת מי עובד על מה וכמה זמן זה לוקח.",
    "זמני מתה מצטברים בלי שמזהים אותם.",
    "העברת משימות לעובדים בקו נעשית ידנית ולא יעילה.",
  ],
  "sol_h2": "מה בנינו.",
  "sol_sub": "מערכת MES בהתאמה אישית שמרכזת את כל הייצור בדשבורד אחד, ומחברת את ההנהלה לרצפת הייצור בזמן אמת.",
  "feats": [
    ("list","קליטת פקודות עבודה","המערכת מושכת את פקודות העבודה מהמפעל לפי סדר עדיפויות."),
    ("dashboard","דשבורד ייצור מפורט","כל הפעולות המאושרות מוצגות על מסך אחד, ברור ומעודכן."),
    ("users","הקצאת משימות לעובדים","מנהל הייצור מקצה משימות לעובדים בלחיצה, לפי עומסים ועדיפויות."),
    ("tablet","טאבלט בקו הייצור","כל עובד רואה את המשימות שלו על טאבלט ומעדכן סטטוס בזמן אמת."),
    ("stopwatch","מעקב זמני ביצוע","השוואה בין זמן מתוכנן לזמן בפועל, וזיהוי זמני מתה לטיפול."),
    ("progress","תמונת התקדמות אישית","לכל עובד: המשימות, שעות העבודה הצפויות ואחוז ההשלמה."),
  ],
  "res_h2": "התוצאה: יותר תפוקה, פחות בזבוז.",
  "res_sub": 'מההנהלה ועד קו הייצור: <span class="accent">שליטה מלאה ברצפת הייצור</span> וזיהוי מיידי של כל עיכוב.',
  "bens": [
    ("gauge","יעילות ייצור גבוהה יותר","מזהים בעיות וצווארי בקבוק בזמן אמת ומנצלים את המשאבים טוב יותר."),
    ("eye","שקיפות מלאה","נתונים על תפוקה, איכות וזמני מחזור - הכול גלוי ומדיד."),
    ("year","פחות זמני מתה","מאתרים זמן מבוזבז ומצמצמים אותו, וכל שעת עבודה שווה יותר."),
  ],
  "appr_sub": "יורדים לרצפת הייצור, מבינים את התהליך האמיתי של המפעל, ורק אז בונים מערכת שמשתלבת בעבודה בלי לשבש אותה.",
  "svc_link": "custom-systems.html",
  "svc_label": "עוד על מערכות מותאמות אישית",
  "mono": "case study · production management",
 },
 {
  "slug": "case-study-sales-site",
  "title": "אתר מכירתי למפעל יצרני (Wiresnet) | פרויקט · אולסי מערכות",
  "desc": "מערכת הזמנות אונליין ליצרן: מחשבון הזמנה ויזואלי, הצעת מחיר אוטומטית, תשלום מאובטח ומעקב הזמנות. .NET ו-SQL Server. אולסי מערכות, בית תוכנה בוטיק מאז 1995.",
  "ogtitle": "אתר מכירתי למפעל יצרני · אולסי מערכות",
  "ogdesc": "Wiresnet: מחשבון הזמנה, הצעת מחיר אוטומטית, תשלום מאובטח ומעקב - הכול אונליין.",
  "crumb": "אתר מכירתי למפעל יצרני",
  "eyebrow": "case study · e-commerce",
  "h1p": "אתר מכירתי שמזמין לבד",
  "h1a": "מהצעת מחיר ועד תשלום, אונליין.",
  "sub": "תהליך הזמנה במפעל יצרני יכול להיות ארוך ומסורבל - שיחות, פרטים, סבבי אישורים. בנינו ל-Wiresnet מערכת אונליין שבה הלקוח מגדיר בדיוק מה הוא צריך, מקבל הצעת מחיר אוטומטית, משלם ועוקב - הכול לבד.",
  "meta": [("ind","ענף · תעשייה ומסחר"),("code","טכנולוגיה · .NET ו-SQL Server"),("year","פרויקט · 2024")],
  "tab": "wiresnet.shop",
  "kpis": [("24/7","ORDERS"),("AUTO","QUOTE"),("SSL","SECURE")],
  "ov_p1": "במפעל יצרני, כל הזמנה מותאמת אישית מתחילה לרוב בשרשרת ארוכה: יצירת קשר, איסוף פרטים מדויקים, חישוב מחיר וכמה סבבי אישורים. התהליך גוזל זמן יקר - ולקוח שמתעייף בדרך פשוט נוטש.",
  "ov_p2": "היצרן רצה לקצר את כל זה: לתת ללקוח להגדיר בעצמו בדיוק מה הוא צריך, לקבל מחיר מיידי ולסגור הזמנה - בלי טלפונים ובלי המתנה.",
  "fit_h3": "מה זיהינו באפיון:",
  "fit": [
    "תהליך ההזמנה ארוך ומסורבל, עם הרבה סבבים.",
    "חישוב הצעת מחיר נעשה ידנית לכל הזמנה מותאמת.",
    "לקוחות נוטשים בגלל ההמתנה והסרבול.",
    "אין דרך ללקוח להזמין ולשלם באופן עצמאי.",
  ],
  "sol_h2": "מה בנינו.",
  "sol_sub": "Wiresnet - מערכת אונליין ליצרני כבלים מותאמים לאלקטרוניקה, שבה הלקוח מגדיר, מתמחר, משלם ועוקב בעצמו.",
  "feats": [
    ("sliders","מחשבון הזמנה ויזואלי","הלקוח בוחר סוג כבל, צבע, סוג בידוד ויחידות מידה בממשק גרפי פשוט וברור."),
    ("sync","עדכון פרמטרים בזמן אמת","כל שינוי מתעדכן מיד, כך שהלקוח רואה בדיוק מה הוא מזמין."),
    ("user","אזור אישי","חשבון אישי עם שמירת קובצי PDF, היסטוריית הזמנות ופרטים שמורים."),
    ("doc","הצעת מחיר אוטומטית","המערכת מחשבת מחיר לפי הפרמטרים, הכמות ומועד האספקה - מיידית."),
    ("shieldpay","תשלום מאובטח אונליין","סליקה מאובטחת עם דגש על אבטחת המידע והפרטיות של הלקוח."),
    ("track","מעקב הזמנות","הלקוח עוקב אחרי הסטטוס של ההזמנה שלו בכל רגע."),
  ],
  "res_h2": "התוצאה: הזמנות פשוטות, יותר המרות.",
  "res_sub": 'תהליך קצר וברור מקצה לקצה: <span class="accent">פחות חיכוך, יותר הזמנות שנסגרות</span> - בלי טלפונים ובלי המתנה.',
  "bens": [
    ("cursor","חוויית הזמנה פשוטה","הלקוח מזין בדיוק מה שהוא צריך, בלי ניחושים ובלי תלות בנציג."),
    ("trend","יותר המרות","תהליך קצר וברור מקטין נטישה ומגדיל את אחוז ההזמנות שנסגרות."),
    ("year","זמינות 24/7","לקוחות מזמינים מתי שנוח להם, גם מחוץ לשעות העבודה."),
  ],
  "appr_sub": "לומדים את תהליך ההזמנה של היצרן לפרטים, ובונים חוויה אונליין שמרגישה פשוטה ללקוח - גם כשמאחורי הקלעים היא מורכבת.",
  "svc_link": "software-development.html",
  "svc_label": "עוד על שירות פיתוח התוכנה שלנו",
  "mono": "case study · sales website",
 },
 {
  "slug": "case-study-crm",
  "title": "אפליקציית CRM לצוות מכירות בשטח | פרויקט · אולסי מערכות",
  "desc": "אפליקציית CRM למכירות שטח, מסונכרנת עם ה-ERP: חיפוש לקוחות, איתור מוצרים וחישוב עלויות מהנייד, הטאבלט והמחשב. אולסי מערכות, בית תוכנה בוטיק מאז 1995.",
  "ogtitle": "אפליקציית CRM לצוות מכירות בשטח · אולסי מערכות",
  "ogdesc": "כל פרטי הלקוח, המוצר והעלות בכף היד - אפליקציית CRM מסונכרנת ל-ERP לצוותי שטח.",
  "crumb": "CRM לצוות מכירות בשטח",
  "eyebrow": "case study · crm",
  "h1p": "CRM שיוצא לשטח",
  "h1a": "כל פרטי הלקוח, בכף היד.",
  "sub": "אנשי מכירות בשטח צריכים גישה מיידית לפרטי לקוח, מידע על מוצרים וחישובי עלות - בלי לחזור למשרד. בנינו אפליקציה שמחוברת ל-ERP של הארגון ומביאה את כל המידע העדכני ישר לנייד, לטאבלט ולמחשב.",
  "meta": [("ind","ענף · מכירות שטח B2B"),("code","טכנולוגיה · Mobile ו-ERP"),("year","פרויקט · 2024")],
  "tab": "crm.mobile",
  "kpis": [("ERP","SYNC"),("LIVE","DATA"),("3","DEVICES")],
  "ov_p1": "איש מכירות מול לקוח לא יכול להרשות לעצמו לומר 'אני אבדוק ואחזור אליך'. הוא צריך כאן ועכשיו את פרטי הלקוח, את המוצרים, את הזמינות ואת המחיר - אחרת העסקה מתקררת.",
  "ov_p2": "הארגון רצה לתת לצוות השטח את כל הכוח של המשרד, בנייד: מידע עדכני שמסונכרן עם ה-ERP, נגיש מכל מכשיר, בכל מקום.",
  "fit_h3": "מה זיהינו באפיון:",
  "fit": [
    "לצוות השטח אין גישה מיידית לפרטי לקוח ומוצר.",
    "חישובי עלות נעשים ידנית או דורשים חזרה למשרד.",
    "המידע בשטח לא תמיד עדכני מול ה-ERP.",
    "עסקאות מתעכבות כי חסר מידע ברגע האמת.",
  ],
  "sol_h2": "מה בנינו.",
  "sol_sub": "אפליקציית CRM לצוותי מכירות בשטח, שמסתנכרנת עם ה-ERP הארגוני ועובדת על נייד, טאבלט ומחשב.",
  "feats": [
    ("search","חיפוש לקוחות","איש המכירות מאתר כל לקוח ואת כל ההיסטוריה שלו בשניות, מהשטח."),
    ("cube","איתור מוצרים","חיפוש מהיר של פריטים, מפרטים וזמינות - בלי לחזור למשרד."),
    ("calc","חישוב עלויות","חישוב מחיר ועלות מוצר במקום, מול הלקוח, בלי טעויות."),
    ("sync","סנכרון עם ה-ERP","כל המידע מגיע ומתעדכן מול מערכת ה-ERP הארגונית בזמן אמת."),
    ("devices","עובד מכל מכשיר","נייד, טאבלט או מחשב - אותה אפליקציה ואותו מידע עדכני."),
    ("plane","בנוי לשטח","ממשק מהיר ופשוט שמתאים לעבודה תוך כדי תנועה, מול הלקוח."),
  ],
  "res_h2": "התוצאה: צוות שטח שסוגר יותר.",
  "res_sub": 'אין יותר חזרות למשרד: <span class="accent">כל המשרד בכף היד</span>, עם מידע עדכני בכל פגישה.',
  "bens": [
    ("bolt","תשובות במקום","אין יותר 'אבדוק ואחזור אליך' - הכול זמין מול הלקוח."),
    ("sync","מידע תמיד עדכני","סנכרון מול ה-ERP מבטיח שהשטח עובד עם נתונים נכונים."),
    ("target","יותר עסקאות נסגרות","כשהמידע זמין ברגע האמת, פחות עסקאות מתקררות."),
  ],
  "appr_sub": "יוצאים לשטח עם אנשי המכירות, מבינים מה חסר להם ברגע האמת, ובונים אפליקציה שנותנת להם בדיוק את זה.",
  "svc_link": "crm-development.html",
  "svc_label": "עוד על פיתוח מערכת CRM",
  "mono": "case study · crm field sales",
 },
]

def main():
    for p in PROJECTS:
        html = build(p)
        path = os.path.join(HERE, p["slug"] + ".html")
        with io.open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print("wrote", p["slug"] + ".html", "(%d chars)" % len(html))

if __name__ == "__main__":
    main()
