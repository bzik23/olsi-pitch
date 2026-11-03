# -*- coding: utf-8 -*-
"""
Trilingual (he / en / ru) chrome for the Olsi Systems WordPress theme.

Exports three PHP fragments consumed by build_wp_theme.py:
  HELPERS_PHP -> injected into functions.php.  Language detection, the mechanical
                 "counterpart URL" resolver (toggle the /en/ or /ru/ prefix for any
                 target language), the shared services list, the he/en/ru UI string
                 tables, and hreflang.
  HEADER_PHP  -> header.php  (language-aware <html lang/dir>, nav, CTA cluster + the
                 segmented he|en|ru language switcher, hreflang alternates).
  FOOTER_PHP  -> footer.php  (language-aware contact band, nav/services/contact
                 columns, legal links).

Language model (matches the site's existing architecture: custom theme, raw HTML in
post_content, all slugs already English):
  Hebrew  page  ->  /<slug>/            (or /     for home)   post_type page|post
  English page  ->  /en/<slug>/         (or /en/  for home)   post_type page, child of the "en" page
  Russian page  ->  /ru/<slug>/         (or /ru/  for home)   post_type page, child of the "ru" page
The switch is purely mechanical: add/strip the leading language prefix, so a visitor
on any page lands on the exact same page in any other language. When an exact
counterpart does not exist yet the switch soft-falls-back (blog listing / home) and
drops its hreflang, so it is never hidden and never points at a 404.
"""

# ---- the 12 services (single source of truth: header dropdown + footer column) ----
# each row: slug, inner-svg (24-viewbox line icon), he_title, he_sub, en_title, en_sub,
#           ru_title, ru_sub
_SVC = [
    ("software-development",
     '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 8.5h18"/><path d="m9 13-2 2 2 2"/><path d="m13 13 2 2-2 2"/>',
     "פיתוח תוכנה", "מערכות עסקיות מותאמות לעסק שלכם",
     "Software Development", "Custom business systems, built around how you work",
     "Разработка ПО", "Бизнес-системы под то, как работает ваш бизнес"),
    ("app-development",
     '<rect x="6.5" y="3" width="11" height="18" rx="2.5"/><path d="M11 18h2"/>',
     "פיתוח אפליקציה", "אפליקציות מובייל לאנדרואיד ול-iOS",
     "App Development", "Mobile apps for Android and iOS",
     "Разработка приложений", "Мобильные приложения для Android и iOS"),
    ("crm-development",
     '<path d="M16 19v-1a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v1"/><circle cx="9.5" cy="7.5" r="3"/><path d="M21 19v-1a4 4 0 0 0-3-3.87"/><path d="M15.5 4.6a3 3 0 0 1 0 5.8"/>',
     "פיתוח מערכת CRM", "ניהול לקוחות, לידים ותהליכי מכירה",
     "CRM Development", "Manage customers, leads and sales processes",
     "Разработка CRM", "Управление клиентами, лидами и продажами"),
    ("excel-upgrade",
     '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M3 14.5h18M9 4v16M15 4v16"/>',
     "שדרוג מאקסל למערכת חכמה", "מגיליונות Excel לפלטפורמה יציבה",
     "Excel Upgrade", "From spreadsheets to a stable platform",
     "Переход с Excel", "От таблиц Excel к стабильной платформе"),
    ("access-upgrade",
     '<ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v6c0 1.66 3.13 3 7 3s7-1.34 7-3V6"/><path d="M5 12v6c0 1.66 3.13 3 7 3s7-1.34 7-3v-6"/>',
     "שדרוג מאקסס לתוכנה חכמה", "ממסד Access ישן למערכת מודרנית",
     "Access Upgrade", "From legacy Access to a modern system",
     "Переход с Access", "От устаревшего Access к современной системе"),
    ("inventory-system",
     '<path d="M3.5 8.5 12 4l8.5 4.5v7L12 20l-8.5-4.5z"/><path d="M3.5 8.5 12 13l8.5-4.5M12 13v7"/>',
     "מערכת לניהול מלאים", "מעקב מלאי, ספקים והזמנות",
     "Inventory Management", "Track stock, suppliers and orders",
     "Управление складом", "Учёт запасов, поставщиков и заказов"),
    ("custom-systems",
     '<rect x="3" y="3" width="8" height="8" rx="1.5"/><rect x="13" y="3" width="8" height="8" rx="1.5"/><rect x="3" y="13" width="8" height="8" rx="1.5"/><rect x="13" y="13" width="8" height="8" rx="1.5"/>',
     "מערכות מותאמות אישית", "פתרון שנבנה סביב התהליך שלכם",
     "Custom Systems", "A solution built around your process",
     "Индивидуальные системы", "Решение, построенное вокруг вашего процесса"),
    ("integrations-api",
     '<circle cx="6" cy="12" r="2.5"/><circle cx="18" cy="6" r="2.5"/><circle cx="18" cy="18" r="2.5"/><path d="M8.2 10.8 15.8 7.2M8.2 13.2l7.6 3.6"/>',
     "אינטגרציות ו-API", "חיבור בין מערכות כך שמידע זורם אוטומטית",
     "Integrations & API", "Connect systems so data flows automatically",
     "Интеграции и API", "Соединяем системы, чтобы данные шли автоматически"),
    ("data-processing",
     '<path d="M3 5h18l-7 8.5V20l-4-2v-4.5z"/>',
     "איסוף ועיבוד נתונים", "סקרייפינג, פייפליינים ודוחות אוטומטיים",
     "Data Collection & Processing", "Scraping, pipelines and automated reports",
     "Сбор и обработка данных", "Парсинг, пайплайны и автоматические отчёты"),
    ("tech-support",
     '<circle cx="12" cy="12" r="3"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3M5.1 5.1l2.1 2.1M16.8 16.8l2.1 2.1M18.9 5.1l-2.1 2.1M7.2 16.8l-2.1 2.1"/>',
     "ליווי טכני שוטף", "שירות, תחזוקה ושיפורים אחרי ההשקה",
     "Ongoing Technical Support", "Service, maintenance and post-launch improvements",
     "Постоянная техподдержка", "Сервис, обслуживание и улучшения после запуска"),
    # added 2026-10-08: two new service pages (he 4335/4340, en 3957/3963).
    # Row-major 2-col grid: #11 lands bottom-start (right in RTL), #12 bottom-end.
    ("gantt-chart",
     '<rect x="3" y="4.5" width="9" height="3.5" rx="1.2"/><rect x="7" y="10.25" width="11" height="3.5" rx="1.2"/><rect x="12" y="16" width="9" height="3.5" rx="1.2"/>',
     "פיתוח תרשים גאנט", "תכנון פרויקטים, משימות ואבני דרך במערכת אחת",
     "Gantt Chart Development", "Project planning, tasks and milestones in one system",
     "Разработка диаграммы Ганта", "Планирование проектов, задач и этапов в одной системе"),
    ("python-developer",
     '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="m7 9 3 3-3 3"/><path d="M12 15h5"/>',
     "פיתוח תוכנה ב-Python", "אוטומציה, עיבוד נתונים ובינה מלאכותית",
     "Python Development", "Automation, data processing and AI",
     "Разработка на Python", "Автоматизация, обработка данных и ИИ"),
]

def _php_svc_rows():
    def q(s):  # single-quote a php string literal (utf-8 kept raw)
        return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"
    rows = []
    for slug, icon, ht, hs, et, es, rt, rs in _SVC:
        rows.append("    array(%s,%s,%s,%s,%s,%s,%s,%s)," % (
            q(slug), q(icon), q(ht), q(hs), q(et), q(es), q(rt), q(rs)))
    return "\n".join(rows)

# ---------------------------------------------------------------------------
# HELPERS_PHP  (injected into functions.php)
# ---------------------------------------------------------------------------
HELPERS_PHP = r"""
/* ===== Trilingual (he/en/ru) chrome helpers ================================= */

/* current request language, from the first path segment: 'he' (default), 'en', 'ru' */
if (!function_exists('olsi_lang')) {
  function olsi_lang() {
    static $l = null;
    if ($l !== null) return $l;
    $p = trim((string) parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH), '/');
    if ($p === 'en' || strpos($p, 'en/') === 0)      $l = 'en';
    elseif ($p === 'ru' || strpos($p, 'ru/') === 0)  $l = 'ru';
    else                                             $l = 'he';
    return $l;
  }
}
/* back-compat shim (older call sites) */
if (!function_exists('olsi_is_en')) {
  function olsi_is_en() { return olsi_lang() === 'en'; }
}

/* the ordered language roster for the switcher + <html> dir. */
if (!function_exists('olsi_langs')) {
  function olsi_langs() {
    return array(
      'he' => array('label' => 'עב', 'dir' => 'rtl',
                    'aria' => 'עבור לעברית',
                    'aria_fb' => 'עבור לעברית (העמוד הזה עדיין לא מתורגם)'),
      'en' => array('label' => 'EN', 'dir' => 'ltr',
                    'aria' => 'Switch to English',
                    'aria_fb' => 'Switch to English (this page is not translated yet)'),
      'ru' => array('label' => 'RU', 'dir' => 'ltr',
                    'aria' => 'Переключить на русский',
                    'aria_fb' => 'Переключить на русский (эта страница ещё не переведена)'),
    );
  }
}

/* the language-neutral slug of the current page ('' = home), with any /en or /ru
   prefix stripped. The slug is identical across languages (same slug, different tree). */
if (!function_exists('olsi_neutral_slug')) {
  function olsi_neutral_slug() {
    static $s = null;
    if ($s !== null) return $s;
    $p    = trim((string) parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH), '/');
    $lang = olsi_lang();
    if ($lang === 'he')      $s = $p;
    elseif ($p === $lang)    $s = '';                      // bare /en or /ru (home)
    else                     $s = substr($p, strlen($lang) + 1);
    return $s;
  }
}

/* resolve the URL of a given neutral slug in a given language, or '' if that exact
   page does not exist. Purely path-based so prefixes toggle cleanly. */
if (!function_exists('olsi_url_for')) {
  function olsi_url_for($slug, $lang) {
    if ($lang === 'he') {
      if ($slug === '') return home_url('/');
      if (get_page_by_path($slug, OBJECT, 'page')) return home_url('/' . $slug . '/');
      // blog: the Hebrew side is a top-level post
      $q = get_posts(array('name' => $slug, 'post_type' => 'post', 'post_parent' => 0,
                           'post_status' => 'publish', 'posts_per_page' => 1));
      return $q ? home_url('/' . $slug . '/') : '';
    }
    // en / ru: pages that are children of the "en" / "ru" parent, same slug
    $pfx = $lang . '/';
    if ($slug === '') {
      return get_page_by_path($lang, OBJECT, 'page') ? home_url('/' . $pfx) : '';
    }
    return get_page_by_path($pfx . $slug, OBJECT, 'page') ? home_url('/' . $pfx . $slug . '/') : '';
  }
}

/* the exact same page in another language (empty string if it does not exist yet). */
if (!function_exists('olsi_counterpart_url')) {
  function olsi_counterpart_url($lang) {
    static $c = array();
    if (array_key_exists($lang, $c)) return $c[$lang];
    $c[$lang] = olsi_url_for(olsi_neutral_slug(), $lang);
    return $c[$lang];
  }
}

/* the URL the switcher points at for a target language. Prefers the exact
   counterpart; otherwise a soft fallback (the blog listing for an article, the
   language home otherwise) so the switch is NEVER hidden. Returns array(url, exact)
   where exact=false marks a fallback (no hreflang on it). */
if (!function_exists('olsi_switch_target')) {
  function olsi_switch_target($lang) {
    static $s = array();
    if (array_key_exists($lang, $s)) return $s[$lang];
    $alt = olsi_counterpart_url($lang);
    if ($alt) { $s[$lang] = array($alt, true); return $s[$lang]; }
    $home = olsi_url_for('', $lang);
    if (!$home) $home = home_url('/');                 // target home not built yet -> HE home
    $url  = $home;
    if (is_singular('post')) {
      $pfx = ($lang === 'he') ? '' : $lang . '/';
      if (get_page_by_path($pfx . 'professional-info', OBJECT, 'page')) {
        $url = home_url('/' . $pfx . 'professional-info/');
      }
    }
    $s[$lang] = array($url, false);
    return $s[$lang];
  }
}

/* the 12 services, localized (header mega-menu + footer column) */
if (!function_exists('olsi_services')) {
  function olsi_services($lang) {
    $rows = array(
%SVC_ROWS%
    );
    $i = ($lang === 'en') ? array(4, 5) : (($lang === 'ru') ? array(6, 7) : array(2, 3));
    $out = array();
    foreach ($rows as $r) {
      $out[] = array('slug' => $r[0], 'icon' => $r[1],
                     'title' => $r[$i[0]], 'sub' => $r[$i[1]]);
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
      'wa_text'       => 'היי, הגעתי אליכם דרך האתר...',
      'menu_aria'     => 'תפריט',
      'lang_group_aria' => 'בחירת שפה',
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
      'err_consent' => 'יש לסמן תיבה זו כדי לשלוח את הטופס.',
      'err_send'    => 'השליחה נכשלה. אנא נסו שוב או התקשרו 09-8820511.',
      'brand_p'     => 'בית תוכנה בוטיק מאז 1995. מערכות שמדברות זו עם זו.',
      'col_nav'     => 'ניווט',
      'col_services'=> 'שירותים',
      'col_contact' => 'צרו קשר',
      'legal_aria'  => 'קישורים משפטיים',
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
      'wa_text'       => 'Hi, I found you through your website...',
      'menu_aria'     => 'Menu',
      'lang_group_aria' => 'Choose language',
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
      'err_consent' => 'Please check this box to submit the form.',
      'err_send'    => 'Sending failed. Please try again or call 09-8820511.',
      'brand_p'     => 'A boutique software house since 1995. Systems that talk to each other.',
      'col_nav'     => 'Navigation',
      'col_services'=> 'Services',
      'col_contact' => 'Contact',
      'legal_aria'  => 'Legal links',
      'addr'  => 'The OLSI Systems offices in Hadera are located in the "Mul HaHof Village" commercial and business complex (Unitowers), next to the Olga interchange on Route 2 (the Coastal Highway).',
      'map_title' => 'Office location - Mul HaHof Village, Hadera',
      'waze'  => 'Navigate with Waze',
      'copy'  => '© 2026 OLSI Systems · All rights reserved',
      'legal_privacy' => 'Privacy Policy',
      'legal_a11y'    => 'Accessibility Statement',
      'credit' => 'Site by Bzik Digital Marketing',
    );
    $ru = array(
      'brand_aria'   => 'OLSI Systems · Главная',
      'nav_home'     => 'Главная',
      'nav_about'    => 'О нас',
      'nav_services' => 'Услуги',
      'nav_projects' => 'Проекты',
      'nav_how'      => 'Как мы работаем',
      'nav_insights' => 'Статьи',
      'nav_contact'  => 'Контакты',
      'dd_services_aria' => 'Услуги',
      'dd_cta_strong' => 'Не знаете, что нужно?',
      'dd_cta_rest'   => ' Мы с радостью проконсультируем и подскажем.',
      'dd_cta_go'     => 'Напишите нам ›',
      'phone_aria'    => 'Быстрый звонок - 09-8820511',
      'call_sr'       => 'Звонок',
      'wa_aria'       => 'Напишите нам в WhatsApp',
      'wa_sr'         => 'WhatsApp',
      'wa_text'       => 'Здравствуйте, я нашёл вас через ваш сайт...',
      'menu_aria'     => 'Меню',
      'lang_group_aria' => 'Выбор языка',
      'nav_aria'      => 'Основная навигация',
      'fc_h2'   => 'Готовы построить систему, которая работает на вас?',
      'fc_p'    => 'Консультация 30 минут, без обязательств. Мы познакомимся с вашим бизнесом и покажем, как система может выглядеть на практике.',
      'fc_call' => 'Позвонить &#183; 09-8820511',
      'fc_wa'   => 'WhatsApp',
      'fc_or'   => 'Или оставьте свои данные, и мы перезвоним',
      'fc_form_aria' => 'Форма обратной связи',
      'form_subject' => 'Новый лид с сайта OLSI Systems (RU)',
      'form_name'    => 'Имя и фамилия',
      'form_phone'   => 'Телефон',
      'form_email'   => 'Эл. почта',
      'form_optional'=> '(необязательно)',
      'form_msg'     => 'Чем мы можем помочь?',
      'form_name_ph' => 'Ваше имя',
      'form_phone_ph'=> '050-0000000',
      'form_email_ph'=> 'name@email.com',
      'form_msg_ph'  => 'Коротко расскажите о вашем бизнесе и о том, что вы ищете...',
      'form_consent_pre'  => 'Я принимаю ',
      'form_consent_link' => 'политику конфиденциальности',
      'form_consent_post' => ' и согласен на использование данных, как в ней описано ',
      'form_submit' => 'Отправить',
      'form_ok'     => 'Спасибо! Ваше сообщение получено, мы скоро свяжемся с вами.',
      'err_consent' => 'Пожалуйста, отметьте это поле, чтобы отправить форму.',
      'err_send'    => 'Не удалось отправить. Попробуйте ещё раз или позвоните 09-8820511.',
      'brand_p'     => 'Бутиковая софтверная студия с 1995 года. Системы, которые говорят друг с другом.',
      'col_nav'     => 'Навигация',
      'col_services'=> 'Услуги',
      'col_contact' => 'Контакты',
      'legal_aria'  => 'Юридические ссылки',
      'addr'  => 'Офисы OLSI Systems в Хадере расположены в торгово-деловом комплексе "Mul HaHof Village" (башни Unitowers), рядом с развязкой Ольга на шоссе 2 (Приморское шоссе).',
      'map_title' => 'Расположение офиса - Mul HaHof Village, Хадера',
      'waze'  => 'Навигация через Waze',
      'copy'  => '© 2026 OLSI Systems · Все права защищены',
      'legal_privacy' => 'Политика конфиденциальности',
      'legal_a11y'    => 'Заявление о доступности',
      'credit' => 'Сайт разработан Bzik Digital Marketing',
    );
    if ($lang === 'en') return $en;
    if ($lang === 'ru') return $ru;
    return $he;
  }
}

/* WhatsApp buttons: the number is never printed in the page source (it was being
   harvested from the wa.me links). It is kept reversed + base64, and olsi.js
   (section 0b) builds the real link only on a genuine interaction with the button.
   Without JS the button falls back to the contact band. */
if (!function_exists('olsi_wa_attrs')) {
  function olsi_wa_attrs($text) {
    return 'href="#lets-talk" data-wa="ODkzNDM1NTA1Mjc5" data-wa-text="' . esc_attr($text) . '"';
  }
}

/* hreflang alternates: self + every OTHER language whose exact counterpart exists. */
if (!function_exists('olsi_hreflang')) {
  function olsi_hreflang() {
    $self = olsi_lang();
    $out  = array();
    $t    = trim((string) parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH), '/');
    $out[$self] = home_url('/' . ($t === '' ? '' : $t . '/'));   // self
    foreach (array('he', 'en', 'ru') as $lg) {
      if ($lg === $self) continue;
      $u = olsi_counterpart_url($lg);
      if ($u) $out[$lg] = $u;
    }
    if (count($out) < 2) return;                                  // only self: nothing to alternate
    foreach ($out as $lg => $u) {
      echo "\n<link rel=\"alternate\" hreflang=\"" . $lg . "\" href=\"" . esc_url($u) . "\">";
    }
    $xd = isset($out['he']) ? $out['he'] : reset($out);
    echo "\n<link rel=\"alternate\" hreflang=\"x-default\" href=\"" . esc_url($xd) . "\">\n";
  }
}
""".replace("%SVC_ROWS%", _php_svc_rows())


# ---------------------------------------------------------------------------
# HEADER_PHP  ->  header.php
# ---------------------------------------------------------------------------
HEADER_PHP = r"""<?php /* Olsi Systems - header (auto-generated, trilingual he/en/ru) */ ?>
<?php
$lang = function_exists('olsi_lang') ? olsi_lang() : 'he';
$dir  = ($lang === 'he') ? 'rtl' : 'ltr';
$L    = olsi_i18n($lang);
$pfx  = ($lang === 'he') ? '/' : '/' . $lang . '/';
$HP   = $pfx;                               // home base (for #anchor links)
$u    = function ($slug) use ($pfx) { return $pfx . $slug . '/'; };
?>
<!DOCTYPE html>
<html lang="<?= esc_attr($lang) ?>" dir="<?= $dir ?>">
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
<?php foreach (olsi_services($lang) as $s): ?>
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
      <a <?= olsi_wa_attrs($L['wa_text']) ?> class="site-header__wa" aria-label="<?= esc_attr($L['wa_aria']) ?>">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413z"/></svg>
        <span class="sr-only"><?= $L['wa_sr'] ?></span>
      </a>
      <div class="lang-switch" role="group" aria-label="<?= esc_attr($L['lang_group_aria']) ?>">
        <svg class="lang-switch__globe" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3c2.5 2.5 3.8 5.7 3.8 9s-1.3 6.5-3.8 9c-2.5-2.5-3.8-5.7-3.8-9S9.5 5.5 12 3z"/></svg>
<?php foreach (olsi_langs() as $code => $meta): ?>
<?php if ($code === $lang): ?>
        <span class="lang-switch__item is-active" aria-current="true"><?= $meta['label'] ?></span>
<?php else: list($sw_url, $sw_exact) = olsi_switch_target($code); ?>
        <a href="<?= esc_url($sw_url) ?>" class="lang-switch__item<?= $sw_exact ? '' : ' lang-switch__item--fb' ?>"<?= $sw_exact ? ' hreflang="' . $code . '"' : ' rel="nofollow"' ?> aria-label="<?= esc_attr($sw_exact ? $meta['aria'] : $meta['aria_fb']) ?>"><?= $meta['label'] ?></a>
<?php endif; ?>
<?php endforeach; ?>
      </div>
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
$lang = function_exists('olsi_lang') ? olsi_lang() : 'he';
$L  = olsi_i18n($lang);
$pfx = ($lang === 'he') ? '/' : '/' . $lang . '/';
$HP = $pfx;
$u  = function ($slug) use ($pfx) { return $pfx . $slug . '/'; };
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
          <a <?= olsi_wa_attrs($L['wa_text']) ?> class="btn btn--whatsapp btn--lg">
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
          <div class="cf-turnstile" data-sitekey="0x4AAAAAADv9Jp8Sxjx6NMBi" data-action="contact" data-language="<?= esc_attr($lang) ?>"></div>
        </div>
        <div class="cta-form__foot">
          <div class="cta-field cta-consent">
            <label class="cta-check">
              <input type="checkbox" name="אישור פרטיות" value="כן" aria-required="true">
              <span class="cta-check__box" aria-hidden="true"></span>
              <span class="cta-check__txt"><?= $L['form_consent_pre'] ?><a href="<?= $u('privacy-policy') ?>" target="_blank" rel="noopener"><?= $L['form_consent_link'] ?></a><?= $L['form_consent_post'] ?><span class="req" aria-hidden="true">*</span></span>
            </label>
            <p class="cta-consent__err" role="alert" style="display:none;color:#e05a4d;font-weight:600;margin-top:.4rem;font-size:.85rem"><?= $L['err_consent'] ?></p>
          </div>
          <button type="submit" class="btn btn--primary btn--lg cta-form__submit"><?= $L['form_submit'] ?></button>
        </div>
        <p class="cta-form__ok" role="status"><?= $L['form_ok'] ?></p>
        <p class="cta-form__err" role="alert" style="display:none;color:#e05a4d;font-weight:600;margin-top:.6rem"><?= $L['err_send'] ?></p>
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
<?php foreach (olsi_services($lang) as $s): ?>
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
      <nav class="footer-legal" aria-label="<?= esc_attr($L['legal_aria']) ?>">
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
