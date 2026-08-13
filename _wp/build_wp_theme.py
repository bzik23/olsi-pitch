# -*- coding: utf-8 -*-
"""
Build a self-contained WordPress THEME from the static Olsi site.

Output: _wp/dist/olsi-systems/   (+ olsi-systems.zip)

Design:
  - The shared chrome (head + header + menu-backdrop) -> header.php  (wp_head, theme-URI assets)
  - The shared chrome (<footer class="site-footer"> .. </html>) -> footer.php (wp_footer)
  - Each static page's BODY (between menu-backdrop and <footer>) -> content/<slug>.html
  - functions.php auto-provisions WP Pages/Posts on theme activation, importing each
    content/<slug>.html into post_content (so it is editable in WP / Elementor later),
    sets the static front page, and registers the primary menu location.
  - Templates (front-page / page / single) render the_content() raw (wpautop removed).
  - Internal .html links -> pretty permalinks (/slug/); same-page nav anchors -> /#anchor.

Assumes the theme folder stays named 'olsi-systems' and WP is installed at the domain root.
Re-runnable: edit the static site, re-run, re-send the ZIP.
"""
import os, re, io, glob, shutil, zipfile, sys
sys.path.insert(0, os.path.dirname(__file__))
from seo_map import SEO            # canonical per-page <title> + meta description (with CTA)
from redirects_map import REDIRECTS  # 301s from the old olsi.co.il URLs
from chrome_i18n import HELPERS_PHP, HEADER_PHP, FOOTER_PHP  # bilingual he/en chrome
from wp_auth import TURNSTILE_SECRET, LEAD_TO, LEAD_CC  # local-only, gitignored (see _wp/wp_auth.py)

SRC   = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DIST  = os.path.join(os.path.dirname(__file__), "dist")
SLUG  = "olsi-systems"
THEME = os.path.join(DIST, SLUG)

HEADER_END = '<div class="menu-backdrop" id="menu-backdrop"></div>'
FOOTER_TAG = '<footer class="site-footer">'

SERVICES = ["software-development","app-development","crm-development","excel-upgrade",
            "access-upgrade","inventory-system","custom-systems","integrations-api",
            "data-processing","tech-support"]
LEGAL    = ["privacy-policy","accessibility-statement"]
SPECIAL  = ["thank-you"]
BLOG_LISTING = "professional-info"
EXCLUDE  = {"index","preview-dark-v1"}   # index = GH-pages redirect; dark = backup

def read(p):
    with io.open(p, encoding="utf-8") as f:
        return f.read()

def write(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)

# ---------- link / asset rewriting -------------------------------------------
def rewrite_links(html):
    # cross-page home anchors
    html = re.sub(r'href="preview\.html#', 'href="/#', html)
    html = html.replace('href="preview.html"', 'href="/"')
    # any other relative <name>.html  ->  /<name>/   (keep optional #anchor)
    html = re.sub(r'href="(?!https?:|#|tel:|mailto:|/)([a-z0-9\-]+)\.html(#[^"]*)?"',
                  lambda m: 'href="/%s/%s"' % (m.group(1), (m.group(2) or "")), html)
    # same-page nav anchors -> home-anchored (work from every page)
    html = html.replace('href="#hero"', 'href="/"')
    for a in ("about", "services", "work", "approach", "contact"):
        html = html.replace('href="#%s"' % a, 'href="/#%s"' % a)
    return html

def assets_php(html):   # for header.php / footer.php (PHP context)
    return html.replace('"assets/', '"<?php echo esc_url(get_template_directory_uri()); ?>/assets/')

def assets_static(html):  # for content/*.html (no PHP) -> root-relative theme path
    return html.replace('"assets/', '"/wp-content/themes/%s/assets/' % SLUG)

# ---------- bilingual chrome (header.php / footer.php) ------------------------
# Header/footer are language-aware PHP (he/en) authored in chrome_i18n.py; they no
# longer derive from preview.html (the bilingual logic + switcher can't be extracted
# from a static file). preview.html stays the HE visual reference for page BODIES only.
header_php = HEADER_PHP
footer_php = FOOTER_PHP

# ---------- per-page content extraction --------------------------------------
def extract_body(html):
    body = html[html.index(HEADER_END) + len(HEADER_END): html.index(FOOTER_TAG)]
    body = re.sub(r'\s*<!--[^>]*FOOTER[^>]*-->\s*$', '\n', body)   # trailing footer comment
    return body.strip() + "\n"

def title_of(html, fallback):
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    if not m:
        return fallback
    t = re.split(r"\s[|·]\s", m.group(1).strip())[0].strip()
    return t or fallback

# build the page manifest
manifest = []  # dict: slug,title,type,file,front
def add(slug, ptype, front=False, title=None):
    src = os.path.join(SRC, slug + ".html")
    html = read(src)
    body = assets_static(rewrite_links(extract_body(html)))
    write(os.path.join(THEME, "content", slug + ".html"), body)
    manifest.append({
        "slug": slug, "type": ptype, "front": front,
        "title": title or title_of(html, slug), "file": slug + ".html",
    })

# home (front page)
add("preview", "page", front=True, title="אולסי מערכות")
# rename the home content file/slug to 'home' for clarity
os.replace(os.path.join(THEME, "content", "preview.html"),
           os.path.join(THEME, "content", "home.html"))
manifest[-1]["slug"] = "home"; manifest[-1]["file"] = "home.html"

for s in SERVICES:                         add(s, "page")
for s in sorted(glob.glob(os.path.join(SRC, "case-study-*.html"))):
    add(os.path.basename(s)[:-5], "page")
add(BLOG_LISTING, "page")
for s in LEGAL:                            add(s, "page")
for s in SPECIAL:                          add(s, "page")

# blog posts = everything else
known = {"preview"} | set(SERVICES) | set(LEGAL) | set(SPECIAL) | {BLOG_LISTING} | EXCLUDE
known |= {os.path.basename(p)[:-5] for p in glob.glob(os.path.join(SRC, "case-study-*.html"))}
for p in sorted(glob.glob(os.path.join(SRC, "*.html"))):
    stem = os.path.basename(p)[:-5]
    if stem in known:
        continue
    add(stem, "post")

# ---------- PHP manifest array -----------------------------------------------
def php_arr(m):
    rows = []
    for x in m:
        rows.append("    array('slug'=>%r,'title'=>%r,'type'=>%r,'file'=>%r,'front'=>%s)," % (
            x["slug"], x["title"], x["type"], x["file"], "true" if x["front"] else "false"))
    body = "\n".join(rows).replace("\\x", "\\u")  # safety; we keep utf-8 though
    return "array(\n" + "\n".join(rows) + "\n  )"

# build with single quotes but PHP needs real UTF-8 (file is utf-8) -> emit raw
def php_quote(s):
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"

rows = []
for x in manifest:
    rows.append("    array('slug'=>%s,'title'=>%s,'type'=>%s,'file'=>%s,'front'=>%s)," % (
        php_quote(x["slug"]), php_quote(x["title"]), php_quote(x["type"]),
        php_quote(x["file"]), "true" if x["front"] else "false"))
MANIFEST_PHP = "array(\n" + "\n".join(rows) + "\n  )"

seo_rows = []
for slug, m in SEO.items():
    seo_rows.append("    %s => array('t'=>%s,'d'=>%s)," % (
        php_quote(slug), php_quote(m["title"]), php_quote(m["desc"])))
SEO_PHP = "array(\n" + "\n".join(seo_rows) + "\n  )"

redir_rows = []
for old, new in REDIRECTS.items():
    redir_rows.append("    %s => %s," % (php_quote(old), php_quote(new)))
REDIR_PHP = "array(\n" + "\n".join(redir_rows) + "\n  )"

# ---------- theme files ------------------------------------------------------
STYLE_CSS = """/*
Theme Name: Olsi Systems
Theme URI: https://www.olsi.co.il
Author: Bzik Digital Marketing
Description: ערכת נושא מותאמת לאתר אולסי מערכות - בית תוכנה בוטיק מאז 1995. עיצוב פיקסל-פרפקט, תואם Elementor.
Version: 1.0.0
Requires at least: 6.0
Tested up to: 6.7
Requires PHP: 7.4
Text Domain: olsi-systems
*/
"""

FUNCTIONS_PHP = r"""<?php
/* Olsi Systems theme - functions */
if (!defined('ABSPATH')) exit;

if (!function_exists('olsi_setup')) {
  function olsi_setup() {
    add_theme_support('title-tag');
    add_theme_support('post-thumbnails');
    add_theme_support('html5', array('search-form','comment-form','gallery','caption','style','script'));
    add_theme_support('automatic-feed-links');
    add_theme_support('elementor');            // play nice with Elementor
    register_nav_menus(array('primary' => 'תפריט ראשי', 'footer' => 'תפריט תחתון'));
  }
}
add_action('after_setup_theme', 'olsi_setup');

/* enqueue the original site CSS/JS (single source of truth) + Google fonts */
function olsi_assets() {
  $u = get_template_directory_uri();
  $d = get_template_directory();
  // Google fonts are linked in header.php (with preconnect); only enqueue our css/js here.
  wp_enqueue_style('olsi-main', $u . '/assets/olsi.css', array(), @filemtime($d . '/assets/olsi.css'));
  wp_enqueue_script('olsi-main', $u . '/assets/olsi.js', array(), @filemtime($d . '/assets/olsi.js'), true);
  // Cloudflare Turnstile (contact-form anti-spam) - the form lives in the footer of every page.
  wp_enqueue_script('cf-turnstile', 'https://challenges.cloudflare.com/turnstile/v0/api.js', array(), null, true);
}
add_action('wp_enqueue_scripts', 'olsi_assets');

/* ---------------------------------------------------------------------------
   Contact form endpoint: server-side Cloudflare Turnstile validation, then relay
   to FormSubmit (with a wp_mail backup). The public form posts HERE - not to
   FormSubmit directly - so the recipient emails and the FormSubmit endpoint never
   appear in page source, and a lead is delivered only when it carries a Turnstile
   token that Cloudflare confirms. No token / bad token / honeypot => no email.
--------------------------------------------------------------------------- */
if (!defined('OLSI_TURNSTILE_SECRET')) define('OLSI_TURNSTILE_SECRET', '__OLSI_TURNSTILE_SECRET__');
if (!defined('OLSI_LEAD_TO'))          define('OLSI_LEAD_TO', '__OLSI_LEAD_TO__');
if (!defined('OLSI_LEAD_CC'))          define('OLSI_LEAD_CC', '__OLSI_LEAD_CC__');

add_action('rest_api_init', function () {
  register_rest_route('olsi/v1', '/contact', array(
    'methods'             => 'POST',
    'callback'            => 'olsi_handle_contact',
    'permission_callback' => '__return_true',
  ));
});

function olsi_handle_contact(WP_REST_Request $req) {
  // The form always posts multipart/form-data, so PHP populates $_POST reliably
  // (incl. the Hebrew field names and Turnstile's cf-turnstile-response).
  $src = wp_unslash($_POST);
  $get = function ($k) use ($src) {
    if (isset($src[$k])) return trim((string) $src[$k]);
    // PHP rewrites spaces and dots in POST field names to underscores, so a field
    // named "שם מלא" arrives as "שם_מלא". Look it up under the mangled key too.
    $mk = str_replace(array(' ', '.'), '_', $k);
    if ($mk !== $k && isset($src[$mk])) return trim((string) $src[$mk]);
    return '';
  };
  $olsi_log = function ($stage, $detail = '') {
    $log = get_option('olsi_contact_log', array());
    if (!is_array($log)) $log = array();
    $log[] = array('t' => current_time('mysql'), 'stage' => $stage, 'detail' => (string) $detail);
    update_option('olsi_contact_log', array_slice($log, -25), false);
  };

  // 1) Honeypot: bots fill the hidden _honey field. Pretend success, deliver nothing.
  if ($get('_honey') !== '') {
    $olsi_log('honeypot');
    return new WP_REST_Response(array('success' => 'true'), 200);
  }

  // 2) Cloudflare Turnstile - the submission must carry a token Cloudflare confirms.
  $token = $get('cf-turnstile-response');
  if ($token === '') {
    $olsi_log('no-token', 'postkeys=' . count($src));
    return new WP_REST_Response(array('success' => 'false', 'error' => 'no-token'), 200);
  }
  $vr = wp_remote_post('https://challenges.cloudflare.com/turnstile/v0/siteverify', array(
    'timeout' => 10,
    'body'    => array(
      'secret'   => OLSI_TURNSTILE_SECRET,
      'response' => $token,
    ),
  ));
  if (is_wp_error($vr)) {
    $olsi_log('verify-unreachable', $vr->get_error_message());
    return new WP_REST_Response(array('success' => 'false', 'error' => 'verify-unreachable'), 200);
  }
  $vd = json_decode(wp_remote_retrieve_body($vr), true);
  if (empty($vd['success'])) {
    $codes = isset($vd['error-codes']) ? implode(',', (array) $vd['error-codes']) : 'unknown';
    $host  = isset($vd['hostname']) ? $vd['hostname'] : '';
    $olsi_log('turnstile-rejected', $codes . ' host=' . $host);
    return new WP_REST_Response(array('success' => 'false', 'error' => 'turnstile-rejected', 'codes' => $codes), 200);
  }

  // 3) Collect visitor fields (Hebrew keys match the form markup).
  $name    = sanitize_text_field($get('שם מלא'));
  $phone   = sanitize_text_field($get('טלפון'));
  $email   = sanitize_email($get('אימייל'));
  $msg     = sanitize_textarea_field($get('מהות הפנייה'));
  $page    = sanitize_text_field($get('עמוד מקור'));
  $subject = $get('_subject');
  $subject = $subject !== '' ? sanitize_text_field($subject) : 'ליד חדש מאתר אולסי מערכות';
  if ($name === '' || $phone === '') {
    $olsi_log('missing-fields');
    return new WP_REST_Response(array('success' => 'false', 'error' => 'missing-fields'), 200);
  }

  // 4) Relay to FormSubmit (keeps their deliverability). Recipients live server-side.
  $relay = wp_remote_post('https://formsubmit.co/ajax/' . OLSI_LEAD_TO, array(
    'timeout' => 15,
    'headers' => array('Accept' => 'application/json', 'Referer' => home_url('/'), 'Origin' => untrailingslashit(home_url('/'))),
    'body'    => array(
      '_subject'    => $subject,
      '_cc'         => OLSI_LEAD_CC,
      '_template'   => 'table',
      '_captcha'    => 'false',
      'שם מלא'      => $name,
      'טלפון'       => $phone,
      'אימייל'      => $email,
      'מהות הפנייה' => $msg,
      'עמוד מקור'   => $page,
    ),
  ));
  $ok = false; $relay_detail = 'wp_error';
  if (!is_wp_error($relay)) {
    $rd = json_decode(wp_remote_retrieve_body($relay), true);
    $ok = (isset($rd['success']) && (string) $rd['success'] === 'true');
    $relay_detail = 'code=' . wp_remote_retrieve_response_code($relay);
  } else {
    $relay_detail = $relay->get_error_message();
  }

  // 5) Backup: if FormSubmit failed, deliver via wp_mail so no confirmed lead is lost.
  if (!$ok) {
    $lines = "פנייה חדשה מהאתר\n--------------------\n";
    $lines .= "שם מלא: $name\nטלפון: $phone\n";
    if ($email) $lines .= "אימייל: $email\n";
    if ($msg)   $lines .= "מהות הפנייה: $msg\n";
    $lines .= "\nנשלח מהעמוד: $page";
    $headers = array('Content-Type: text/plain; charset=UTF-8');
    if ($email) $headers[] = 'Reply-To: ' . $email;
    $recipients = array_merge(array(OLSI_LEAD_TO), array_filter(array_map('trim', explode(',', OLSI_LEAD_CC))));
    $ok = wp_mail($recipients, $subject, $lines, $headers);
    $olsi_log($ok ? 'delivered-wpmail' : 'delivery-failed', 'relay:' . $relay_detail);
  } else {
    $olsi_log('delivered-formsubmit', $relay_detail);
  }

  return new WP_REST_Response(array('success' => $ok ? 'true' : 'false'), 200);
}

/* the page bodies are full custom HTML - render them verbatim (Elementor can still hook the_content) */
remove_filter('the_content', 'wpautop');
remove_filter('the_content', 'wptexturize');
remove_filter('the_content', 'convert_smilies');
remove_filter('the_excerpt', 'wpautop');

/* ---- content registry (auto-generated) ---- */
function olsi_manifest() {
  return %MANIFEST%;
}

/* provision all pages/posts from /content on theme activation
   (idempotent; OVERWRITES an existing slug with our new content and strips
   Elementor from it, so a re-skin over an existing Elementor site is clean) */
function olsi_provision() {
  $dir = get_template_directory() . '/content/';
  $front_id = 0;
  foreach (olsi_manifest() as $m) {
    $html = @file_get_contents($dir . $m['file']);
    if ($html === false) $html = '';
    $existing = get_page_by_path($m['slug'], OBJECT, $m['type']);
    if ($existing) {
      // overwrite the old (likely Elementor) page/post with our new design
      $id = $existing->ID;
      wp_update_post(array(
        'ID'           => $id,
        'post_title'   => $m['title'],
        'post_content' => $html,
        'post_status'  => 'publish',
      ));
      // neutralize Elementor so the_content renders our raw HTML, not the old build
      foreach (array('_elementor_edit_mode','_elementor_data','_elementor_version',
                     '_elementor_template_type','_elementor_page_settings',
                     '_elementor_controls_usage','_elementor_css') as $mk) {
        delete_post_meta($id, $mk);
      }
      update_post_meta($id, '_wp_page_template', 'default');
    } else {
      $id = wp_insert_post(array(
        'post_title'   => $m['title'],
        'post_name'    => $m['slug'],
        'post_status'  => 'publish',
        'post_type'    => $m['type'],
        'post_content' => $html,
        'comment_status' => 'closed',
      ));
    }
    if (!empty($m['front']) && $id && !is_wp_error($id)) $front_id = $id;
  }
  if ($front_id) {
    update_option('show_on_front', 'page');
    update_option('page_on_front', $front_id);
  }
  // pretty permalinks so /slug/ links resolve
  global $wp_rewrite;
  if (!get_option('permalink_structure')) {
    update_option('permalink_structure', '/%postname%/');
    $wp_rewrite->set_permalink_structure('/%postname%/');
  }
  flush_rewrite_rules();
}
add_action('after_switch_theme', 'olsi_provision');

/* ---- SEO: per-page <title> + meta description (with CTA), no plugin needed ---- */
function olsi_seo_map() {
  return %SEO%;
}
function olsi_seo_current() {
  // English (/en/) pages: defer to Yoast (which holds the English title/desc), so the
  // HE seo_map is never matched by an EN page's shared slug.
  if (function_exists('olsi_is_en') && olsi_is_en()) return null;
  $map = olsi_seo_map();
  if (is_front_page()) return isset($map['home']) ? $map['home'] : null;
  if (is_singular()) {
    $slug = get_post_field('post_name', get_queried_object_id());
    if ($slug && isset($map[$slug])) return $map[$slug];
  }
  return null;
}
add_filter('pre_get_document_title', function ($title) {
  $s = olsi_seo_current();
  return $s ? $s['t'] : $title;
}, 20);
add_action('wp_head', function () {
  // defer to a real SEO plugin if one is active
  if (defined('WPSEO_VERSION') || defined('RANK_MATH_VERSION')) return;
  $s = olsi_seo_current();
  if (!$s) return;
  echo "\n<meta name=\"description\" content=\"" . esc_attr($s['d']) . "\">\n";
  echo "<meta property=\"og:title\" content=\"" . esc_attr($s['t']) . "\">\n";
  echo "<meta property=\"og:description\" content=\"" . esc_attr($s['d']) . "\">\n";
}, 1);

/* ---- 301 redirects from the previous olsi.co.il URLs (no orphan pages) ---- */
function olsi_redirects() {
  return %REDIR%;
}
add_action('template_redirect', function () {
  if (is_admin()) return;
  $path = urldecode((string) parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH));
  if ($path === '' || $path === '/') return;
  $map = olsi_redirects();
  foreach (array($path, rtrim($path, '/'), rtrim($path, '/') . '/') as $cand) {
    if (isset($map[$cand])) {
      wp_redirect(home_url($map[$cand]), 301);
      exit;
    }
  }
}, 1);
%HELPERS%
"""
FUNCTIONS_PHP = (FUNCTIONS_PHP.replace("%MANIFEST%", MANIFEST_PHP)
                 .replace("%SEO%", SEO_PHP).replace("%REDIR%", REDIR_PHP)
                 .replace("%HELPERS%", HELPERS_PHP))

FRONT_PHP = """<?php get_header(); ?>
<?php while (have_posts()) : the_post(); the_content(); endwhile; ?>
<?php get_footer(); ?>
"""
PAGE_PHP = """<?php get_header(); ?>
<?php while (have_posts()) : the_post(); the_content(); endwhile; ?>
<?php get_footer(); ?>
"""
SINGLE_PHP = """<?php get_header(); ?>
<?php while (have_posts()) : the_post(); the_content(); endwhile; ?>
<?php get_footer(); ?>
"""
INDEX_PHP = """<?php get_header(); ?>
<?php if (have_posts()) : while (have_posts()) : the_post(); the_content(); endwhile; endif; ?>
<?php get_footer(); ?>
"""

write(os.path.join(THEME, "style.css"), STYLE_CSS)
write(os.path.join(THEME, "functions.php"), FUNCTIONS_PHP
      .replace("__OLSI_TURNSTILE_SECRET__", TURNSTILE_SECRET)
      .replace("__OLSI_LEAD_TO__", LEAD_TO)
      .replace("__OLSI_LEAD_CC__", LEAD_CC))
write(os.path.join(THEME, "header.php"), header_php)
write(os.path.join(THEME, "footer.php"), footer_php)
write(os.path.join(THEME, "front-page.php"), FRONT_PHP)
write(os.path.join(THEME, "page.php"), PAGE_PHP)
write(os.path.join(THEME, "single.php"), SINGLE_PHP)
write(os.path.join(THEME, "index.php"), INDEX_PHP)

# ---------- copy assets ------------------------------------------------------
dst_assets = os.path.join(THEME, "assets")
if os.path.isdir(dst_assets):
    shutil.rmtree(dst_assets)
shutil.copytree(os.path.join(SRC, "assets"), dst_assets)

# screenshot (optional)
shot = os.path.join(SRC, "_shots", "hero-buttons.png")
if os.path.isfile(shot):
    shutil.copyfile(shot, os.path.join(THEME, "screenshot.png"))

# ---------- README -----------------------------------------------------------
README = """# ערכת נושא: Olsi Systems (אולסי מערכות)

ערכת נושא וורדפרס מותאמת שמשכפלת את אתר אולסי מערכות (פיקסל-פרפקט), תואמת Elementor.

## התקנה (ללקוח)
1. בלוח הניהול: **מראה > ערכות נושא > הוסף חדש > העלה ערכת נושא** - העלו את `olsi-systems.zip` והפעילו.
2. בהפעלה הערכה **יוצרת אוטומטית** את כל העמודים/הפוסטים, מגדירה את דף הבית, ומפעילה קישורים יפים (Permalinks).
3. אם הקישורים לא עובדים מיד: **הגדרות > קישורים קבועים > שמירת שינויים** (לרענון).

## חשוב
- יש להשאיר את שם תיקיית הערכה **olsi-systems** (נתיבי תמונות תלויים בו).
- מיועד לוורדפרס בשורש הדומיין (כמו olsi.co.il).
- התוכן יושב בעמודים/פוסטים של וורדפרס וניתן לעריכה (גם ב-Elementor).
- הטופס שולח דרך FormSubmit ל-info@olsi.co.il (דורש אישור חד-פעמי בלחיצה על הקישור שיישלח במייל בפנייה הראשונה).

## SEO
כל עמוד מקבל כותרת ותיאור מטא מותאמים (כולל הנעה לפעולה), שנפלטים אוטומטית ב-<head> ללא צורך בתוסף. אם מותקן Yoast/RankMath - הם מקבלים עדיפות.

## הפניות 301 (מהאתר הישן)
הערכה כוללת הפניות 301 מכל כתובות olsi.co.il הישנות לעמודים החדשים (פועל אוטומטית כשהערכה פעילה - אין עמוד בלי הפניה). חלופה: קובץ `redirects.csv` לייבוא לתוסף **Redirection** (Tools > Import).

## עדכון תוכן (בזיק)
התוכן/SEO/הפניות נבנים אוטומטית מ-`_wp/` (seo_map.py, redirects_map.py, build_wp_theme.py). לעדכון: ערכו, הריצו מחדש, ושלחו ZIP מעודכן.
"""
write(os.path.join(THEME, "README.md"), README)

# ---- redirects.csv (Redirection plugin: source,target) ----
csv_lines = ["source,target"]
for _old, _new in REDIRECTS.items():
    csv_lines.append("%s,%s" % (_old, _new))
write(os.path.join(THEME, "redirects.csv"), "\n".join(csv_lines) + "\n")

# ---------- zip --------------------------------------------------------------
zip_path = os.path.join(DIST, SLUG + ".zip")
if os.path.exists(zip_path):
    os.remove(zip_path)
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(THEME):
        for fn in files:
            full = os.path.join(root, fn)
            arc = os.path.relpath(full, DIST)   # keep top folder olsi-systems/
            z.write(full, arc)

# ---------- report -----------------------------------------------------------
pages = sum(1 for m in manifest if m["type"] == "page")
posts = sum(1 for m in manifest if m["type"] == "post")
print("THEME:", THEME)
print("pages:", pages, " posts:", posts, " (front=home)")
print("zip:  ", zip_path, "(%.1f MB)" % (os.path.getsize(zip_path) / 1e6))
"""report manifest"""
for m in manifest:
    print("  %-5s %-26s %s" % (m["type"], m["slug"], m["title"]))
