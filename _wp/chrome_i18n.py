# -*- coding: utf-8 -*-
"""
Bilingual (he / en) chrome for the Olsi Systems WordPress theme.

Exports three PHP fragments consumed by build_wp_theme.py:
  HELPERS_PHP -> injected into functions.php.  Language detection, the mechanical
                 bidirectional "counterpart URL" resolver (toggle the /en/ prefix),
                 the shared services list, the he/en UI string table, and hreflang.
  HEADER_PHP  -> header.php  (language-aware <html lang/dir>, nav, CTA cluster + the
                 language-switcher button, hreflang alternates).
  FOOTER_PHP  -> footer.php  (language-aware contact band, nav/services/contact
                 columns, legal links).

Language model (matches the site's existing architecture: custom theme, raw HTML in
post_content, all slugs already English):
  Hebrew  page  ->  /<slug>/            (or /  for home)         post_type page|post
  English page  ->  /en/<slug>/         (or /en/ for home)       post_type page, child of the "en" page
The switch is purely mechanical: add or strip the leading "en/" path segment, so a
visitor on any page lands on the exact same page in the other language, both ways.
"""

# ---- the 10 services (single source of truth: header dropdown + footer column) ----
# each row: slug, inner-svg (24-viewbox line icon), he_title, he_sub, en_title, en_sub
_SVC = [
    ("software-development",
     '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 8.5h18"/><path d="m9 13-2 2 2 2"/><path d="m13 13 2 2-2 2"/>',
     "פיתוח תוכנה", "מערכות עסקיות מותאמות לעסק שלכם",
     "Software Development", "Custom business systems, built around how you work"),
    ("app-development",
     '<rect x="6.5" y="3" width="11" height="18" rx="2.5"/><path d="M11 18h2"/>',
     "פיתוח אפליקציה", "אפליקציות מובייל לאנדרואיד ול-iOS",
     "App Development", "Mobile apps for Android and iOS"),
    ("crm-development",
     '<path d="M16 19v-1a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v1"/><circle cx="9.5" cy="7.5" r="3"/><path d="M21 19v-1a4 4 0 0 0-3-3.87"/><path d="M15.5 4.6a3 3 0 0 1 0 5.8"/>',
     "פיתוח מערכת CRM", "ניהול לקוחות, לידים ותהליכי מכירה",
     "CRM Development", "Manage customers, leads and sales processes"),
    ("excel-upgrade",
     '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M3 14.5h18M9 4v16M15 4v16"/>',
     "שדרוג מאקסל למערכת חכמה", "מגיליונות Excel לפלטפורמה יציבה",
     "Excel Upgrade", "From spreadsheets to a stable platform"),
    ("access-upgrade",
     '<ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v6c0 1.66 3.13 3 7 3s7-1.34 7-3V6"/><path d="M5 12v6c0 1.66 3.13 3 7 3s7-1.34 7-3v-6"/>',
     "שדרוג מאקסס לתוכנה חכמה", "ממסד Access ישן למערכת מודרנית",
     "Access Upgrade", "From legacy Access to a modern system"),
    ("inventory-system",
     '<path d="M3.5 8.5 12 4l8.5 4.5v7L12 20l-8.5-4.5z"/><path d="M3.5 8.5 12 13l8.5-4.5M12 13v7"/>',
     "מערכת לניהול מלאים", "מעקב מלאי, ספקים והזמנות",
     "Inventory Management", "Track stock, suppliers and orders"),
    ("custom-systems",
     '<rect x="3" y="3" width="8" height="8" rx="1.5"/><rect x="13" y="3" width="8" height="8" rx="1.5"/><rect x="3" y="13" width="8" height="8" rx="1.5"/><rect x="13" y="13" width="8" height="8" rx="1.5"/>',
     "מערכות מותאמות אישית", "פתרון שנבנה סביב התהליך שלכם",
     "Custom Systems", "A solution built around your process"),
    ("integrations-api",
     '<circle cx="6" cy="12" r="2.5"/><circle cx="18" cy="6" r="2.5"/><circle cx="18" cy="18" r="2.5"/><path d="M8.2 10.8 15.8 7.2M8.2 13.2l7.6 3.6"/>',
     "אינטגרציות ו-API", "חיבור בין מערכות כך שמידע זורם אוטומטית",
     "Integrations & API", "Connect systems so data flows automatically"),
    ("data-processing",
     '<path d="M3 5h18l-7 8.5V20l-4-2v-4.5z"/>',
     "איסוף ועיבוד נתונים", "סקרייפינג, פייפליינים ודוחות אוטומטיים",
     "Data Collection & Processing", "Scraping, pipelines and automated reports"),
    ("tech-support",
     '<circle cx="12" cy="12" r="3"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3M5.1 5.1l2.1 2.1M16.8 16.8l2.1 2.1M18.9 5.1l-2.1 2.1M7.2 16.8l-2.1 2.1"/>',
     "ליווי טכני שוטף", "שירות, תחזוקה ושיפורים אחרי ההשקה",
     "Ongoing Technical Support", "Service, maintenance and post-launch improvements"),
]

def _php_svc_rows():
    def q(s):  # single-quote a php string literal (utf-8 kept raw)
        return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"
    rows = []
    for slug, icon, ht, hs, et, es in _SVC:
        rows.append("    array(%s,%s,%s,%s,%s,%s)," % (q(slug), q(icon), q(ht), q(hs), q(et), q(es)))
    return "\n".join(rows)

# ---------------------------------------------------------------------------
# HELPERS_PHP  (injected into functions.php)
# ---------------------------------------------------------------------------
HELPERS_PHP = r"""
/* ===== Bilingual (he/en) chrome helpers ===================================== */

/* current request in the English tree? ( /en  or  /en/... ) */
if (!function_exists('olsi_is_en')) {
  function olsi_is_en() {
    static $e = null;
    if ($e !== null) return $e;
    $p = trim((string) parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH), '/');
    $e = ($p === 'en' || strpos($p, 'en/') === 0);
    return $e;
  }
}

/* the exact same page in the OTHER language (empty string if it does not exist yet,
   so we never render a switcher/hreflang that points at a 404). Purely path-based
   so the /en/ prefix toggles cleanly and identical slugs never collide. */
if (!function_exists('olsi_counterpart_url')) {
  function olsi_counterpart_url() {
    static $c = null;
    if ($c !== null) return $c;
    $c = '';
    $p = (string) parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH);
    $t = trim($p, '/');
    if ($t === '') {                                   // he home -> en home
      $c = get_page_by_path('en', OBJECT, 'page') ? home_url('/en/') : '';
    } elseif ($t === 'en') {                           // en home -> he home
      $c = home_url('/');
    } elseif (strpos($t, 'en/') === 0) {               // en page -> he counterpart
      $slug = substr($t, 3);
      $obj  = get_page_by_path($slug, OBJECT, 'page'); // services / case studies / legal are pages
      if (!$obj) {                                     // blog: he side is a top-level post
        $q = get_posts(array('name' => $slug, 'post_type' => 'post', 'post_parent' => 0,
                             'post_status' => 'publish', 'posts_per_page' => 1));
        $obj = $q ? $q[0] : null;
      }
      $c = $obj ? home_url('/' . $slug . '/') : '';
    } else {                                           // he page -> en counterpart (child of "en")
      $c = get_page_by_path('en/' . $t, OBJECT, 'page') ? home_url('/en/' . $t . '/') : '';
    }
    return $c;
  }
}

/* the URL the header language switch points at. Prefers the exact counterpart;
   when it does not exist yet (e.g. a fresh HE article with no translation) we fall
   back to the closest page in the other language - the blog listing for articles,
   the home page otherwise - so the switch is NEVER hidden. Returns
   array(url, exact) where exact=false marks a fallback (no hreflang on it). */
if (!function_exists('olsi_switch_target')) {
  function olsi_switch_target() {
    static $s = null;
    if ($s !== null) return $s;
    $alt = olsi_counterpart_url();
    if ($alt) { $s = array($alt, true); return $s; }
    $en   = olsi_is_en();
    $base = $en ? '' : 'en/';                       // prefix of the OTHER language
    $home = $en ? home_url('/') : (get_page_by_path('en', OBJECT, 'page') ? home_url('/en/') : home_url('/'));
    $url  = $home;
    if (is_singular('post')) {
      $listing = get_page_by_path($base . 'professional-info', OBJECT, 'page');
      if ($listing) $url = home_url('/' . $base . 'professional-info/');
    }
    $s = array($url, false);
    return $s;
  }
}

/* the 10 services, localized (header mega-menu + footer column) */
if (!function_exists('olsi_services')) {
  function olsi_services($lang) {
    $rows = array(
%SVC_ROWS%
    );
    $out = array();
    foreach ($rows as $r) {
      $out[] = array('slug' => $r[0], 'icon' => $r[1],
                     'title' => ($lang === 'en' ? $r[4] : $r[2]),
                     'sub'   => ($lang === 'en' ? $r[5] : $r[3]));
    }
    return $out;
  }
}

/* UI string table */
if (!function_exists('olsi_i18n')) {
  function olsi_i18n($lang) {
    $he = array(
      'brand_aria'   => 'אולסי מערכות · דף הבית',
      'nav_home'     => 'דף הבית',
      'nav_about'    => 'אודות',
      'nav_services' => 'שירותים',
      'nav_projects' => 'פרויקטים',
      'nav_how'      => 'איך עובדים',
      'nav_insights' => 'מידע מקצועי',
      'nav_contact'  => 'צרו קשר',
      'dd_services_aria' => 'שירותים',
      'dd_cta_strong' => 'לא בטוחים מה צריך?',
      'dd_cta_rest'   => ' נשמח לייעץ ולכוון אתכם.',
      'dd_cta_go'     => 'דברו איתנו ›',
      'phone_aria'    => 'חיוג מהיר - 09-8820511',
      'call_sr'       => 'חיוג',
      'wa_aria'       => 'שלחו לנו הודעת ווטסאפ',
      'wa_sr'         => 'ווטסאפ',
      'wa_href'       => 'https://wa.me/972505534398?text=%d7%94%d7%99%d7%99%2c%20%d7%94%d7%92%d7%a2%d7%aa%d7%99%20%d7%90%d7%9c%d7%99%d7%9b%d7%9d%20%d7%93%d7%a8%d7%9a%20%d7%94%d7%90%d7%aa%d7%a8...',
      'menu_aria'     => 'תפריט',
      'switch_code'   => 'EN',
      'switch_aria'   => 'Switch to English',
      'switch_aria_fb'=> 'Switch to English (this page is not translated yet)',
      'nav_aria'      => 'ניווט ראשי',
      'fc_h2'   => 'מוכנים לבנות את המערכת שתעבוד בשבילכם?',
      'fc_p'    => 'שיחת ייעוץ של 30 דקות, בלי התחייבות. נשמע על העסק שלכם, ונראה לכם איך המערכת יכולה להיראות בפועל.',
      'fc_call' => 'חייגו עכשיו &#183; 09-8820511',
      'fc_wa'   => 'וואטסאפ',
      'fc_or'   => 'או השאירו פרטים ונחזור אליכם',
      'fc_form_aria' => 'טופס יצירת קשר',
      'form_subject' => 'ליד חדש מאתר אולסי מערכות',
      'form_name'    => 'שם מלא',
      'form_phone'   => 'טלפון',
      'form_email'   => 'אימייל',
      'form_optional'=> '(לא חובה)',
      'form_msg'     => 'מהות הפנייה',
      'form_name_ph' => 'ישראל ישראלי',
      'form_phone_ph'=> '050-0000000',
      'form_email_ph'=> 'name@email.com',
      'form_msg_ph'  => 'ספרו לנו בקצרה על העסק ועל מה שאתם מחפשים...',
      'form_consent_pre'  => 'אני מאשר/ת את ',
      'form_consent_link' => 'מדיניות הפרטיות',
      'form_consent_post' => ' ומסכים/ה לשימוש כמפורט בה ',
      'form_submit' => 'שליחה',
      'form_ok'     => 'תודה! פנייתכם התקבלה ונחזור אליכם בהקדם.',
      'brand_p'     => 'בית תוכנה בוטיק מאז 1995. מערכות שמדברות זו עם זו.',
      'col_nav'     => 'ניווט',
      'col_services'=> 'שירותים',
      'col_contact' => 'צרו קשר',
      'addr'  => 'משרדי חברת אולסי מערכות בחדרה ממוקמים במתחם המסחרי והעסקים "מול החוף וילג\'" (במגדלי Unitowers), בסמוך למחלף אולגה על כביש 2 (כביש החוף).',
      'map_title' => 'מפת המשרדים - מול החוף וילג\', חדרה',
      'waze'  => 'ניווט עם Waze',
      'copy'  => '© 2026 אולסי מערכות · כל הזכויות שמורות',
      'legal_privacy' => 'מדיניות פרטיות',
      'legal_a11y'    => 'הצהרת נגישות',
      'credit' => 'האתר נבנה ע"י בזיק שיווק דיגיטלי',
    );
    $en = array(
      'brand_aria'   => 'OLSI Systems · Home',
      'nav_home'     => 'Home',
      'nav_about'    => 'About',
      'nav_services' => 'Services',
      'nav_projects' => 'Projects',
      'nav_how'      => 'How We Work',
      'nav_insights' => 'Insights',
      'nav_contact'  => 'Contact',
      'dd_services_aria' => 'Services',
      'dd_cta_strong' => 'Not sure what you need?',
      'dd_cta_rest'   => ' We\'ll gladly advise and point you the right way.',
      'dd_cta_go'     => 'Talk to us ›',
      'phone_aria'    => 'Quick call - 09-8820511',
      'call_sr'       => 'Call',
      'wa_aria'       => 'Send us a WhatsApp message',
      'wa_sr'         => 'WhatsApp',
      'wa_href'       => 'https://wa.me/972505534398?text=Hi%2C%20I%20found%20you%20through%20your%20website...',
      'menu_aria'     => 'Menu',
      'switch_code'   => 'עב',
      'switch_aria'   => 'עבור לעברית',
      'switch_aria_fb'=> 'עבור לעברית (העמוד הזה עדיין לא מתורגם)',
      'nav_aria'      => 'Main navigation',
      'fc_h2'   => 'Ready to build the system that works for you?',
      'fc_p'    => 'A 30-minute consultation, no obligation. We\'ll get to know your business and show you what the system could actually look like.',
      'fc_call' => 'Call now &#183; 09-8820511',
      'fc_wa'   => 'WhatsApp',
      'fc_or'   => 'Or leave your details and we\'ll get back to you',
      'fc_form_aria' => 'Contact form',
      'form_subject' => 'New lead from the OLSI Systems site (EN)',
      'form_name'    => 'Full name',
      'form_phone'   => 'Phone',
      'form_email'   => 'Email',
      'form_optional'=> '(optional)',
      'form_msg'     => 'How can we help?',
      'form_name_ph' => 'Your name',
      'form_phone_ph'=> '050-0000000',
      'form_email_ph'=> 'name@email.com',
      'form_msg_ph'  => 'Tell us briefly about your business and what you are looking for...',
      'form_consent_pre'  => 'I accept the ',
      'form_consent_link' => 'privacy policy',
      'form_consent_post' => ' and consent to the use described in it ',
      'form_submit' => 'Send',
      'form_ok'     => 'Thank you! Your message has been received and we will get back to you shortly.',
      'brand_p'     => 'A boutique software house since 1995. Systems that talk to each other.',
      'col_nav'     => 'Navigation',
      'col_services'=> 'Services',
      'col_contact' => 'Contact',
      'addr'  => 'The OLSI Systems offices in Hadera are located in the "Mul HaHof Village" commercial and business complex (Unitowers), next to the Olga interchange on Route 2 (the Coastal Highway).',
      'map_title' => 'Office location - Mul HaHof Village, Hadera',
      'waze'  => 'Navigate with Waze',
      'copy'  => '© 2026 OLSI Systems · All rights reserved',
      'legal_privacy' => 'Privacy Policy',
      'legal_a11y'    => 'Accessibility Statement',
      'credit' => 'Site by Bzik Digital Marketing',
    );
    return $lang === 'en' ? $en : $he;
  }
}

/* hreflang alternates (only when the counterpart page actually exists) */
if (!function_exists('olsi_hreflang')) {
  function olsi_hreflang() {
    $alt = olsi_counterpart_url();
    if (!$alt) return;
    $en = olsi_is_en();
    $t  = trim((string) parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH), '/');
    $self = home_url('/' . ($t === '' ? '' : $t . '/'));
    $he_url = $en ? $alt : $self;
    $en_url = $en ? $self : $alt;
    echo "\n<link rel=\"alternate\" hreflang=\"he\" href=\"" . esc_url($he_url) . "\">";
    echo "\n<link rel=\"alternate\" hreflang=\"en\" href=\"" . esc_url($en_url) . "\">";
    echo "\n<link rel=\"alternate\" hreflang=\"x-default\" href=\"" . esc_url($he_url) . "\">\n";
  }
}
""".replace("%SVC_ROWS%", _php_svc_rows())


# ---------------------------------------------------------------------------
# HEADER_PHP  ->  header.php
# ---------------------------------------------------------------------------
HEADER_PHP = r"""<?php /* Olsi Systems - header (auto-generated, bilingual he/en) */ ?>
<?php
$en  = function_exists('olsi_is_en') ? olsi_is_en() : false;
$L   = olsi_i18n($en ? 'en' : 'he');
$HP  = $en ? '/en/' : '/';                 // home base (for #anchor links)
$u   = function ($slug) use ($en) { return ($en ? '/en/' : '/') . $slug . '/'; };
$alt = olsi_counterpart_url();
list($sw_url, $sw_exact) = function_exists('olsi_switch_target') ? olsi_switch_target() : array($alt, true);
?>
<!DOCTYPE html>
<html lang="<?= $en ? 'en' : 'he' ?>" dir="<?= $en ? 'ltr' : 'rtl' ?>">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#FAF7FF">
<link rel="icon" type="image/png" href="<?php echo esc_url(get_template_directory_uri()); ?>/assets/logo-olsi-2026.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<noscript><style>[data-anim]{opacity:1!important;transform:none!important}</style></noscript>
<?php olsi_hreflang(); ?>
<?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>

<!-- HEADER -->
<header class="site-header" id="site-header">
  <div class="site-header__inner">
    <a href="<?= $HP ?>" class="site-header__brand" aria-label="<?= esc_attr($L['brand_aria']) ?>">
      <img src="<?php echo esc_url(get_template_directory_uri()); ?>/assets/logo-olsi-2026.png" alt="OLSI" height="38" width="auto" loading="eager" decoding="async">
      <span class="site-header__subtag" dir="ltr">OLSI · est. 1995</span>
    </a>
    <nav class="site-header__nav" id="site-nav" aria-label="<?= esc_attr($L['nav_aria']) ?>">
      <a href="<?= $HP ?>"><?= $L['nav_home'] ?></a>
      <a href="<?= $HP ?>#about"><?= $L['nav_about'] ?></a>
      <div class="nav-has-dropdown" id="nav-services">
        <a href="<?= $HP ?>#services" class="nav-dropdown__trigger" aria-haspopup="true" aria-expanded="false">
          <?= $L['nav_services'] ?>
          <svg class="nav-dropdown__chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="6 9 12 15 18 9"/></svg>
        </a>
        <div class="nav-dropdown__panel" role="menu" aria-label="<?= esc_attr($L['dd_services_aria']) ?>">
          <div class="nav-dropdown__grid">
<?php foreach (olsi_services($en ? 'en' : 'he') as $s): ?>
            <a class="nav-dd-item" href="<?= $u($s['slug']) ?>" role="menuitem">
              <span class="nav-dd-item__icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><?= $s['icon'] ?></svg></span>
              <span class="nav-dd-item__text"><span class="nav-dd-item__title"><?= $s['title'] ?></span><span class="nav-dd-item__sub"><?= $s['sub'] ?></span></span>
            </a>
<?php endforeach; ?>
            <a class="nav-dd-cta" href="<?= $HP ?>#contact" role="menuitem">
              <span class="nav-dd-cta__txt"><b><?= $L['dd_cta_strong'] ?></b><?= $L['dd_cta_rest'] ?></span>
              <span class="nav-dd-cta__go"><?= $L['dd_cta_go'] ?></span>
            </a>
          </div>
        </div>
      </div>
      <a href="<?= $HP ?>#work"><?= $L['nav_projects'] ?></a>
      <a href="<?= $HP ?>#approach"><?= $L['nav_how'] ?></a>
      <a href="<?= $u('professional-info') ?>"><?= $L['nav_insights'] ?></a>
      <a href="<?= $HP ?>#contact"><?= $L['nav_contact'] ?></a>
    </nav>
    <div class="site-header__cta">
      <a href="tel:098820511" class="site-header__phone" dir="ltr">09-8820511</a>
      <a href="tel:098820511" class="site-header__call" aria-label="<?= esc_attr($L['phone_aria']) ?>">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true"><path d="M6.62 10.79c1.44 2.83 3.76 5.15 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.24.2 2.45.57 3.57.11.35.03.74-.24 1.02l-2.2 2.2z"/></svg>
        <span class="sr-only"><?= $L['call_sr'] ?></span>
      </a>
      <a href="<?= esc_url($L['wa_href']) ?>" class="site-header__wa" target="_blank" rel="noopener" aria-label="<?= esc_attr($L['wa_aria']) ?>">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413z"/></svg>
        <span class="sr-only"><?= $L['wa_sr'] ?></span>
      </a>
      <a href="<?= esc_url($sw_url) ?>" class="lang-switch<?= $sw_exact ? '' : ' lang-switch--fallback' ?>"<?= $sw_exact ? ' hreflang="' . ($en ? 'he' : 'en') . '"' : ' rel="nofollow"' ?> aria-label="<?= esc_attr($sw_exact ? $L['switch_aria'] : $L['switch_aria_fb']) ?>">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3c2.5 2.5 3.8 5.7 3.8 9s-1.3 6.5-3.8 9c-2.5-2.5-3.8-5.7-3.8-9S9.5 5.5 12 3z"/></svg>
        <span class="lang-switch__code"><?= $L['switch_code'] ?></span>
      </a>
      <button class="hamburger" id="hamburger" aria-expanded="false" aria-controls="site-nav" aria-label="<?= esc_attr($L['menu_aria']) ?>">
        <span class="hamburger__bars"><span></span></span>
      </button>
    </div>
  </div>
</header>
<div class="menu-backdrop" id="menu-backdrop"></div>
"""


# ---------------------------------------------------------------------------
# FOOTER_PHP  ->  footer.php
# ---------------------------------------------------------------------------
FOOTER_PHP = r"""<?php
$en = function_exists('olsi_is_en') ? olsi_is_en() : false;
$L  = olsi_i18n($en ? 'en' : 'he');
$HP = $en ? '/en/' : '/';
$u  = function ($slug) use ($en) { return ($en ? '/en/' : '/') . $slug . '/'; };
?>
<footer class="site-footer">
  <!-- full-width contact band -->
  <section class="footer-cta" id="lets-talk">
    <div class="grid-bg--dark" aria-hidden="true"></div>
    <div class="footer-cta__glow" aria-hidden="true"></div>
    <div class="footer-cta__inner">
      <div class="footer-cta__head" data-anim>
        <p class="eyebrow"><span class="code-comment">let's talk</span></p>
        <h2><?= $L['fc_h2'] ?></h2>
        <p><?= $L['fc_p'] ?></p>
        <div class="cta-band__actions">
          <a href="tel:098820511" class="btn btn--primary btn--lg"><?= $L['fc_call'] ?></a>
          <a href="<?= esc_url($L['wa_href']) ?>" target="_blank" rel="noopener" class="btn btn--whatsapp btn--lg">
            <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413z"/></svg>
            <?= $L['fc_wa'] ?>
          </a>
        </div>
      </div>
      <div class="cta-band__or"><span><?= $L['fc_or'] ?></span></div>
      <form class="cta-form" action="<?= esc_url( rest_url('olsi/v1/contact') ) ?>" method="POST" aria-label="<?= esc_attr($L['fc_form_aria']) ?>">
        <input type="hidden" name="_subject" value="<?= esc_attr($L['form_subject']) ?>">
        <input type="text" name="_honey" class="cta-hp" tabindex="-1" autocomplete="off" aria-hidden="true">
        <input type="hidden" name="עמוד מקור" id="cf-page" value="">
        <div class="cta-form__grid">
          <div class="cta-field">
            <label for="cf-name"><?= $L['form_name'] ?> <span class="req" aria-hidden="true">*</span></label>
            <input id="cf-name" name="שם מלא" type="text" required autocomplete="name" placeholder="<?= esc_attr($L['form_name_ph']) ?>">
          </div>
          <div class="cta-field">
            <label for="cf-phone"><?= $L['form_phone'] ?> <span class="req" aria-hidden="true">*</span></label>
            <input id="cf-phone" name="טלפון" type="tel" required autocomplete="tel" inputmode="tel" placeholder="<?= esc_attr($L['form_phone_ph']) ?>">
          </div>
          <div class="cta-field">
            <label for="cf-email"><?= $L['form_email'] ?> <span class="cta-field__opt"><?= $L['form_optional'] ?></span></label>
            <input id="cf-email" name="אימייל" type="email" autocomplete="email" placeholder="<?= esc_attr($L['form_email_ph']) ?>">
          </div>
        </div>
        <div class="cta-field">
          <label for="cf-msg"><?= $L['form_msg'] ?> <span class="cta-field__opt"><?= $L['form_optional'] ?></span></label>
          <textarea id="cf-msg" name="מהות הפנייה" rows="3" placeholder="<?= esc_attr($L['form_msg_ph']) ?>"></textarea>
        </div>
        <div class="cta-turnstile" style="margin:.25rem 0 .5rem">
          <div class="cf-turnstile" data-sitekey="0x4AAAAAADv9Jp8Sxjx6NMBi" data-action="contact" data-language="<?= $en ? 'en' : 'he' ?>"></div>
        </div>
        <div class="cta-form__foot">
          <div class="cta-field cta-consent">
            <label class="cta-check">
              <input type="checkbox" name="אישור פרטיות" value="כן" aria-required="true">
              <span class="cta-check__box" aria-hidden="true"></span>
              <span class="cta-check__txt"><?= $L['form_consent_pre'] ?><a href="<?= $u('privacy-policy') ?>" target="_blank" rel="noopener"><?= $L['form_consent_link'] ?></a><?= $L['form_consent_post'] ?><span class="req" aria-hidden="true">*</span></span>
            </label>
            <p class="cta-consent__err" role="alert" style="display:none;color:#e05a4d;font-weight:600;margin-top:.4rem;font-size:.85rem"><?= $en ? 'Please check this box to submit the form.' : 'יש לסמן תיבה זו כדי לשלוח את הטופס.' ?></p>
          </div>
          <button type="submit" class="btn btn--primary btn--lg cta-form__submit"><?= $L['form_submit'] ?></button>
        </div>
        <p class="cta-form__ok" role="status"><?= $L['form_ok'] ?></p>
        <p class="cta-form__err" role="alert" style="display:none;color:#e05a4d;font-weight:600;margin-top:.6rem"><?= $en ? 'Sending failed. Please try again or call 09-8820511.' : 'השליחה נכשלה. אנא נסו שוב או התקשרו 09-8820511.' ?></p>
      </form>
    </div>
  </section>
  <div class="footer-grid">
    <div class="footer-brand">
      <img src="<?php echo esc_url(get_template_directory_uri()); ?>/assets/logo-olsi-2026.png" alt="OLSI" height="32" width="auto">
      <p><?= $L['brand_p'] ?></p>
      <span class="footer-sub" dir="ltr">OLSI · est. 1995</span>
    </div>
    <div class="footer-col">
      <h4><?= $L['col_nav'] ?></h4>
      <ul>
        <li><a href="<?= $HP ?>"><?= $L['nav_home'] ?></a></li>
        <li><a href="<?= $HP ?>#about"><?= $L['nav_about'] ?></a></li>
        <li><a href="<?= $HP ?>#services"><?= $L['nav_services'] ?></a></li>
        <li><a href="<?= $HP ?>#work"><?= $L['nav_projects'] ?></a></li>
        <li><a href="<?= $u('professional-info') ?>"><?= $L['nav_insights'] ?></a></li>
        <li><a href="<?= $HP ?>#contact"><?= $L['nav_contact'] ?></a></li>
      </ul>
    </div>
    <div class="footer-col footer-col--wide">
      <h4><?= $L['col_services'] ?></h4>
      <ul>
<?php foreach (olsi_services($en ? 'en' : 'he') as $s): ?>
        <li><a class="footer-svc" href="<?= $u($s['slug']) ?>"><svg class="footer-svc__ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><?= $s['icon'] ?></svg><span><?= $s['title'] ?></span></a></li>
<?php endforeach; ?>
      </ul>
    </div>
    <div class="footer-col">
      <h4><?= $L['col_contact'] ?></h4>
      <ul>
        <li><a href="tel:098820511" dir="ltr">09-8820511</a></li>
        <li><a href="mailto:info@olsi.co.il" dir="ltr">info@olsi.co.il</a></li>
      </ul>
      <p class="footer-addr"><?= $L['addr'] ?></p>
      <div class="footer-map">
        <iframe title="<?= esc_attr($L['map_title']) ?>" src="https://maps.google.com/maps?q=%D7%9E%D7%95%D7%9C%20%D7%94%D7%97%D7%95%D7%A3%20%D7%95%D7%99%D7%9C%D7%92%27%20%D7%97%D7%93%D7%A8%D7%94&hl=he&z=16&output=embed" width="100%" height="170" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe>
      </div>
      <a class="footer-waze" href="https://waze.com/ul?ll=32.4414786%2C34.8958675&navigate=yes" target="_blank" rel="noopener noreferrer"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21s-6-5.3-6-10a6 6 0 0 1 12 0c0 4.7-6 10-6 10z"/><circle cx="12" cy="11" r="2"/></svg><span><?= $L['waze'] ?></span></a>
    </div>
  </div>
  <div class="footer-bottom">
    <div class="footer-bottom__start">
      <span class="footer-bottom__copy"><?= $L['copy'] ?></span>
      <nav class="footer-legal" aria-label="<?= $en ? 'Legal links' : 'קישורים משפטיים' ?>">
        <a href="<?= $u('privacy-policy') ?>"><?= $L['legal_privacy'] ?></a>
        <span class="footer-legal__sep" aria-hidden="true">|</span>
        <a href="<?= $u('accessibility-statement') ?>"><?= $L['legal_a11y'] ?></a>
      </nav>
    </div>
    <span class="footer-bottom__mono"><?= $L['credit'] ?></span>
  </div>
</footer>



<?php wp_footer(); ?>
</body>
</html>
"""
