<?php
/**
 * Plugin Name: Olsi - Contact Click Tracking
 * Description: Measures clicks on the quick-call and WhatsApp buttons (header, footer band, floating widget) across mobile and desktop. Sends a GA4/dataLayer `contact_click` event, keeps a first-party log, and emails a weekly report with traffic-source breakdown.
 * Version:     1.2.0
 * Author:      Bzik
 *
 * Must-use plugin: lives in wp-content/mu-plugins so it survives theme rebuilds
 * (the olsi-systems theme is regenerated + re-uploaded from build_wp_theme.py).
 *
 * PHP 7.4 target - no str_contains/match/?->/named args.
 */

if (!defined('ABSPATH')) exit;

define('OLSI_CLICKS_VER', '1.2.0');
define('OLSI_CLICKS_OPT', 'olsi_clicks');            // the log (autoload=false)
define('OLSI_CLICKS_RCPT', 'olsi_clicks_recipients'); // manual "send now" recipients
define('OLSI_CLICKS_WRCPT', 'olsi_clicks_weekly_recipients'); // weekly-report recipients
define('OLSI_CLICKS_MAX', 4000);                      // hard row cap
define('OLSI_CLICKS_DAYS', 120);                      // retention
define('OLSI_CLICKS_TZ', 'Asia/Jerusalem');

/* =========================================================================
   0) SMTP RELAY
   uPress blocks outbound port 25, so the local sendmail can never hand a
   message to a destination MX - wp_mail() reports success and the mail dies in
   the queue. We route every wp_mail() through an authenticated relay on 587
   (587 is open). Credentials live in the `olsi_smtp` option (NOT in this file),
   set once via the admin screen. With the option empty this whole block is a
   no-op, so the plugin is safe to ship before the relay is configured.
   ========================================================================= */

/** @return array|null host/port/user/pass/secure/from_email/from_name, or null when unconfigured. */
function olsi_smtp_config() {
    $c = get_option('olsi_smtp', array());
    if (!is_array($c) || empty($c['host']) || empty($c['user']) || empty($c['pass'])) return null;
    return array(
        'host'       => (string) $c['host'],
        'port'       => isset($c['port']) ? (int) $c['port'] : 587,
        'user'       => (string) $c['user'],
        'pass'       => (string) $c['pass'],
        'secure'     => isset($c['secure']) ? (string) $c['secure'] : 'tls',   // tls|ssl|''
        'from_email' => !empty($c['from_email']) ? (string) $c['from_email'] : 'no-reply@olsi.co.il',
        'from_name'  => isset($c['from_name']) ? (string) $c['from_name'] : 'אולסי מערכות',
    );
}

add_action('phpmailer_init', 'olsi_smtp_apply', 99);
function olsi_smtp_apply($phpmailer) {
    $c = olsi_smtp_config();
    if ($c === null) return;
    $phpmailer->isSMTP();
    $phpmailer->Host       = $c['host'];
    $phpmailer->Port       = $c['port'];
    $phpmailer->SMTPAuth   = true;
    $phpmailer->Username   = $c['user'];
    $phpmailer->Password   = $c['pass'];
    $phpmailer->SMTPSecure = $c['secure'];  // '' disables encryption
    if ($c['secure'] === '') $phpmailer->SMTPAutoTLS = false;
    // Envelope sender on our own domain so the relay's SPF/DKIM align with it.
    $phpmailer->Sender = $c['from_email'];
}

/** Force a consistent, aligned From when the relay is on (unless a caller set its own). */
function olsi_smtp_from_email($email) {
    $c = olsi_smtp_config();
    if ($c === null) return $email;
    // Let deliberate senders (e.g. the lead form's brand From) keep their address.
    if ($email && strpos($email, 'wordpress@') !== 0) return $email;
    return $c['from_email'];
}
function olsi_smtp_from_name($name) {
    $c = olsi_smtp_config();
    if ($c === null) return $name;
    if ($name && $name !== 'WordPress') return $name;
    return $c['from_name'];
}
add_filter('wp_mail_from', 'olsi_smtp_from_email', 99);
add_filter('wp_mail_from_name', 'olsi_smtp_from_name', 99);

/**
 * Report-mail headers. The From must be a sender Brevo accepts - an
 * unverified olsi.co.il sender is silently blocked after "queued OK", so we
 * follow the relay's configured from_email instead of hardcoding one.
 */
function olsi_clicks_mail_headers() {
    $cfg  = olsi_smtp_config();
    $from = ($cfg !== null) ? $cfg['from_email'] : 'no-reply@olsi.co.il';
    return array(
        'Content-Type: text/html; charset=UTF-8',
        'From: אולסי מערכות <' . $from . '>',
    );
}

/** Recipients default = the same inboxes that receive a lead from the contact form. */
function olsi_clicks_recipients() {
    $raw = get_option(OLSI_CLICKS_RCPT, '');
    if (!is_string($raw) || trim($raw) === '') {
        $raw = 'info@olsi.co.il,oren@olsi.co.il,bzik23@gmail.com';
    }
    $out = array();
    foreach (explode(',', $raw) as $e) {
        $e = trim($e);
        if ($e !== '' && is_email($e)) $out[] = $e;
    }
    return $out;
}

/* =========================================================================
   0b) GOOGLE ANALYTICS 4 (added 2026-07-26)
   The site previously ran only a dead UA property; this is the first live GA4
   tag. contact_click events from the tracker below flow into it automatically.
   ========================================================================= */

define('OLSI_GA4_ID', 'G-987SL9EG9X'); // ⚠️ לא להתבלבל עם G-4GYC6C0NEL שהוא של POSTYBELL.

add_action('wp_head', 'olsi_ga4_tag', 4);
function olsi_ga4_tag() {
    if (is_admin() || OLSI_GA4_ID === '') return;
    $id = OLSI_GA4_ID;
    echo '<script async src="https://www.googletagmanager.com/gtag/js?id=' . esc_attr($id) . '"></script>' . "\n";
    echo '<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag("js",new Date());gtag("config","' . esc_js($id) . '");</script>' . "\n";
}

/* =========================================================================
   1) FRONT-END TRACKER
   ========================================================================= */

add_action('wp_footer', 'olsi_clicks_script', 99);
function olsi_clicks_script() {
    if (is_admin()) return;
    $ajax = esc_js(admin_url('admin-ajax.php'));
    ?>
<script id="olsi-click-track">
(function () {
  var W = window, D = document;
  if (W.__olsiClickTrack) return;
  W.__olsiClickTrack = 1;

  var AJAX = '<?php echo $ajax; ?>';
  var last = { key: '', t: 0 };

  /* ---------- session source attribution ----------------------------------
     Captured once per session on the entry page, so a click that happens five
     pages later still reports the platform the visitor actually arrived from. */
  function hostOf(u) {
    try { return new URL(u, W.location.href).hostname.replace(/^www\./, ''); }
    catch (e) { return ''; }
  }
  function param(n) {
    try { return new URLSearchParams(W.location.search).get(n) || ''; }
    catch (e) { return ''; }
  }
  function sourceInit() {
    var stored = null;
    try { stored = JSON.parse(sessionStorage.getItem('olsi_src') || 'null'); } catch (e) {}

    var utmS = param('utm_source'), utmM = param('utm_medium'), utmC = param('utm_campaign');
    var gclid   = param('gclid') || param('wbraid') || param('gbraid');
    var fbclid  = param('fbclid');
    var msclkid = param('msclkid');
    var ttclid  = param('ttclid');
    var liclid  = param('li_fat_id');
    var ref     = hostOf(D.referrer);
    var self    = hostOf(W.location.href);
    if (ref === self) ref = '';

    var clickId = gclid ? 'gclid' : (fbclid ? 'fbclid' : (msclkid ? 'msclkid'
                : (ttclid ? 'ttclid' : (liclid ? 'liclid' : ''))));

    /* A new campaign/referrer mid-session overwrites the stored one; plain
       internal navigation (no referrer, no utm) keeps the original. */
    var fresh = utmS || clickId || ref;
    if (stored && !fresh) return stored;

    var src = {
      ref: ref, us: utmS, um: utmM, uc: utmC, ci: clickId,
      lp: W.location.pathname
    };
    try { sessionStorage.setItem('olsi_src', JSON.stringify(src)); } catch (e) {}
    return src;
  }
  var SRC = sourceInit();
  /* Cookie copy so a form submission (handled server-side over REST) can be
     attributed to the same session source. */
  try { D.cookie = 'olsi_src=' + encodeURIComponent(JSON.stringify(SRC)) + '; path=/; SameSite=Lax'; } catch (e) {}

  /* ---------- element helpers ---------- */
  function classOf(n) {
    var c = n.className;
    if (c && typeof c === 'object' && typeof c.baseVal === 'string') c = c.baseVal; // SVG
    return ' ' + (typeof c === 'string' ? c : '') + ' ';
  }
  function closestLink(node) {
    var n = node, hops = 0;
    while (n && n.nodeType === 1 && hops < 12) {
      if (n.tagName === 'A' && n.getAttribute('href')) return n;
      n = n.parentNode; hops++;
    }
    return null;
  }
  /* The floating WhatsApp widget (Click to Chat plugin) is a <div>, not a link. */
  function floatWidget(node) {
    var n = node, hops = 0;
    while (n && n.nodeType === 1 && hops < 12) {
      if (n.id === 'ht-ctc-chat' || classOf(n).indexOf(' ht-ctc ') > -1) return n;
      n = n.parentNode; hops++;
    }
    return null;
  }
  function placementOf(node) {
    var n = node, hops = 0, c;
    while (n && n.nodeType === 1 && hops < 18) {
      c = classOf(n);
      if (n.id === 'ht-ctc-chat' || c.indexOf(' ht-ctc ') > -1)   return 'float';
      if (c.indexOf(' footer-cta ') > -1 || n.id === 'lets-talk') return 'footer_form';
      if (c.indexOf(' site-header ') > -1)                        return 'header';
      if (c.indexOf(' contact-card ') > -1 || n.id === 'contact') return 'contact_section';
      if (c.indexOf(' thanks ') > -1)                             return 'thank_you';
      if (c.indexOf(' post-body ') > -1)                          return 'content';
      if (c.indexOf(' site-footer ') > -1)                        return 'footer';
      if (n.tagName === 'HEADER')                                 return 'header';
      if (n.tagName === 'FOOTER')                                 return 'footer';
      n = n.parentNode; hops++;
    }
    return 'other';
  }
  /* Which physical button - the header holds three variants that differ by device. */
  function buttonOf(el, kind) {
    var c = classOf(el);
    if (c.indexOf(' site-header__wa ') > -1)    return 'header_whatsapp';
    if (c.indexOf(' site-header__call ') > -1)  return 'header_call_icon';   // mobile round icon
    if (c.indexOf(' site-header__phone ') > -1) return 'header_phone_text';  // desktop number
    if (c.indexOf(' btn--whatsapp ') > -1)      return 'cta_whatsapp';
    if (c.indexOf(' btn--primary ') > -1 && kind === 'phone') return 'cta_call';
    if (c.indexOf(' ht-ctc ') > -1)             return 'float_whatsapp';
    return '';
  }

  var TEL = /^tel:/i;
  var WA  = /(wa\.me|api\.whatsapp\.com|web\.whatsapp\.com|whatsapp:)/i;

  function send(kind, placement, button, target) {
    var now = (new Date()).getTime();
    var key = kind + '|' + placement + '|' + button;
    if (key === last.key && now - last.t < 1500) return;   // double-fire guard
    last = { key: key, t: now };

    var device = W.innerWidth <= 767 ? 'mobile' : 'desktop';
    var path   = W.location.pathname;

    /* --- GA4 / GTM --------------------------------------------------------
       Pushed to dataLayer for the existing GTM container, and to gtag() if a
       GA4 tag is present. Once a GA4 property is connected (Site Kit or GTM)
       the events start flowing with no further change here. */
    var ev = {
      method:      kind,        // whatsapp | phone
      placement:   placement,   // header | footer_form | footer | float | ...
      button:      button,
      device_type: device,
      page_path:   path,
      site_lang:   (path === '/en' || path.indexOf('/en/') === 0) ? 'en' : 'he'
    };
    try {
      W.dataLayer = W.dataLayer || [];
      W.dataLayer.push({
        event: 'contact_click',
        method: ev.method, placement: ev.placement, button: ev.button,
        device_type: ev.device_type, page_path: ev.page_path, site_lang: ev.site_lang
      });
    } catch (e) {}
    try { if (typeof W.gtag === 'function') W.gtag('event', 'contact_click', ev); } catch (e) {}

    /* --- first-party log -------------------------------------------------- */
    try {
      var b = [];
      function add(k, v) { b.push(encodeURIComponent(k) + '=' + encodeURIComponent(v == null ? '' : v)); }
      add('action', 'olsi_click');
      add('k',  kind);
      add('pl', placement);
      add('lb', button);
      add('d',  device);
      add('u',  path);
      add('ti', D.title);
      add('tg', target || '');
      add('ref', SRC.ref); add('us', SRC.us); add('um', SRC.um);
      add('uc', SRC.uc);   add('ci', SRC.ci); add('lp', SRC.lp);
      var body = b.join('&');
      var type = 'application/x-www-form-urlencoded;charset=UTF-8';
      if (navigator.sendBeacon) {
        navigator.sendBeacon(AJAX, new Blob([body], { type: type }));
      } else {
        fetch(AJAX, { method: 'POST', keepalive: true, headers: { 'Content-Type': type }, body: body });
      }
    } catch (e) {}
  }

  function handle(e) {
    var t = e.target;
    if (!t || t.nodeType !== 1) t = t && t.parentNode;
    if (!t) return;

    var a = closestLink(t);
    if (a) {
      var href = a.getAttribute('href') || '';
      if (TEL.test(href)) { send('phone', placementOf(a), buttonOf(a, 'phone'), href.replace(TEL, '')); return; }
      if (WA.test(href))  { send('whatsapp', placementOf(a), buttonOf(a, 'whatsapp'), ''); return; }
      return;
    }
    var f = floatWidget(t);
    if (f) send('whatsapp', 'float', 'float_whatsapp', '');
  }

  D.addEventListener('click', handle, true);
  D.addEventListener('auxclick', handle, true);
  D.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar') handle(e);
  }, true);

  /* A confirmed form lead reaches the thank-you page only after a successful,
     Turnstile-verified submission - fire the GA4 lead event there. */
  try {
    var tp = W.location.pathname.replace(/\/+$/, '');
    if (/\/thank-you$/.test(tp)) {
      var tl = (tp.indexOf('/en/') === 0 || tp === '/en/thank-you') ? 'en' : 'he';
      W.dataLayer = W.dataLayer || [];
      W.dataLayer.push({ event: 'generate_lead', method: 'contact_form', site_lang: tl });
      if (typeof W.gtag === 'function') W.gtag('event', 'generate_lead', { method: 'contact_form', site_lang: tl });
    }
  } catch (e) {}
})();
</script>
    <?php
}

/* =========================================================================
   2) COLLECTOR
   ========================================================================= */

add_action('wp_ajax_olsi_click', 'olsi_clicks_collect');
add_action('wp_ajax_nopriv_olsi_click', 'olsi_clicks_collect');

function olsi_clicks_collect() {
    $post = wp_unslash($_POST);
    $get = function ($k, $max = 190) use ($post) {
        $v = isset($post[$k]) ? (string) $post[$k] : '';
        $v = sanitize_text_field($v);
        return function_exists('mb_substr') ? mb_substr($v, 0, $max) : substr($v, 0, $max);
    };

    $kind = $get('k', 12);
    if ($kind !== 'whatsapp' && $kind !== 'phone') {
        wp_send_json_error(array('bad' => 'kind'));
    }

    $ua = isset($_SERVER['HTTP_USER_AGENT']) ? (string) $_SERVER['HTTP_USER_AGENT'] : '';
    if (olsi_clicks_is_bot($ua)) wp_send_json_success(array('ok' => 0, 'bot' => 1));

    $ref = strtolower($get('ref', 90));
    $us  = strtolower($get('us', 60));
    $um  = strtolower($get('um', 60));
    $ci  = $get('ci', 12);

    $row = array(
        't'    => time(),
        'k'    => $kind,
        'pl'   => $get('pl', 24),
        'lb'   => $get('lb', 32),
        'd'    => ($get('d', 10) === 'mobile') ? 'mobile' : 'desktop',
        'u'    => $get('u', 160),
        'ti'   => $get('ti', 140),
        'plat' => olsi_clicks_platform($ref, $us, $um, $ci),
        'ref'  => $ref,
        'us'   => $us,
        'um'   => $um,
        'uc'   => $get('uc', 60),
        'lp'   => $get('lp', 160),
        'v'    => olsi_clicks_visitor($ua),   // rotating hash, never a raw IP
        'adm'  => (is_user_logged_in() && current_user_can('manage_options')) ? 1 : 0,
    );

    $log = get_option(OLSI_CLICKS_OPT, array());
    if (!is_array($log)) $log = array();

    // Server-side dedupe: same visitor + same button within 120s counts once.
    $cut = $row['t'] - 120;
    for ($i = count($log) - 1; $i >= 0; $i--) {
        if (!isset($log[$i]['t']) || $log[$i]['t'] < $cut) break;
        if ($log[$i]['v'] === $row['v'] && $log[$i]['k'] === $row['k'] && $log[$i]['pl'] === $row['pl']) {
            wp_send_json_success(array('ok' => 0, 'dup' => 1));
        }
    }

    $log[] = $row;
    $log = olsi_clicks_prune($log);
    update_option(OLSI_CLICKS_OPT, $log, false);

    wp_send_json_success(array('ok' => 1));
}

function olsi_clicks_prune($log) {
    $floor = time() - (OLSI_CLICKS_DAYS * DAY_IN_SECONDS);
    $out = array();
    foreach ($log as $r) {
        if (isset($r['t']) && $r['t'] >= $floor) $out[] = $r;
    }
    if (count($out) > OLSI_CLICKS_MAX) $out = array_slice($out, -OLSI_CLICKS_MAX);
    return array_values($out);
}

/** Per-visitor-per-day hash. No raw IP is ever stored. */
function olsi_clicks_visitor($ua) {
    $ip = '';
    foreach (array('HTTP_CF_CONNECTING_IP', 'HTTP_X_FORWARDED_FOR', 'REMOTE_ADDR') as $k) {
        if (!empty($_SERVER[$k])) {
            $ip = trim(explode(',', (string) $_SERVER[$k])[0]);
            break;
        }
    }
    return substr(md5($ip . '|' . $ua . '|' . gmdate('Y-m-d') . '|' . AUTH_SALT), 0, 12);
}

function olsi_clicks_is_bot($ua) {
    if ($ua === '') return true;
    $ua = strtolower($ua);
    $needles = array('bot', 'crawl', 'spider', 'slurp', 'headless', 'phantom', 'python-requests',
                     'curl/', 'wget', 'facebookexternalhit', 'preview', 'monitor', 'pingdom',
                     'gtmetrix', 'lighthouse', 'ahrefs', 'semrush', 'dataprovider', 'scrapy');
    foreach ($needles as $n) {
        if (strpos($ua, $n) !== false) return true;
    }
    return false;
}

/* =========================================================================
   3) TRAFFIC-SOURCE CLASSIFICATION
   ========================================================================= */

function olsi_clicks_platform($ref, $us, $um, $ci) {
    $paid = ($um === 'cpc' || $um === 'ppc' || $um === 'paid' || $um === 'paidsearch' || $um === 'paid_social');

    // 1) Ad click-ids are unambiguous.
    if ($ci === 'gclid')   return 'google_ads';
    if ($ci === 'fbclid')  return 'facebook';
    if ($ci === 'msclkid') return 'bing_ads';
    if ($ci === 'ttclid')  return 'tiktok';
    if ($ci === 'liclid')  return 'linkedin';

    // 2) Explicit utm_source wins over referrer.
    if ($us !== '') {
        $map = array(
            'google' => $paid ? 'google_ads' : 'google_organic',
            'bing'   => $paid ? 'bing_ads' : 'bing_organic',
            'facebook' => 'facebook', 'fb' => 'facebook', 'meta' => 'facebook',
            'instagram' => 'instagram', 'ig' => 'instagram',
            'linkedin' => 'linkedin', 'whatsapp' => 'whatsapp',
            'youtube' => 'youtube', 'tiktok' => 'tiktok', 'telegram' => 'telegram',
            'twitter' => 'twitter', 'x' => 'twitter',
            'newsletter' => 'email', 'email' => 'email', 'mail' => 'email',
        );
        if (isset($map[$us])) return $map[$us];
        if ($um === 'email' || $um === 'newsletter') return 'email';
        return 'campaign:' . $us;
    }

    // 3) Fall back to the referring host.
    if ($ref === '') return 'direct';
    $hosts = array(
        'google.'    => $paid ? 'google_ads' : 'google_organic',
        'bing.'      => 'bing_organic',
        'duckduckgo' => 'duckduckgo',
        'yahoo.'     => 'yahoo',
        'yandex.'    => 'yandex',
        'facebook.'  => 'facebook',
        'fb.'        => 'facebook',
        'instagram.' => 'instagram',
        'linkedin.'  => 'linkedin',
        'lnkd.in'    => 'linkedin',
        'whatsapp.'  => 'whatsapp',
        'youtube.'   => 'youtube',
        'youtu.be'   => 'youtube',
        'tiktok.'    => 'tiktok',
        't.co'       => 'twitter',
        'twitter.'   => 'twitter',
        'x.com'      => 'twitter',
        't.me'       => 'telegram',
        'telegram.'  => 'telegram',
        'chatgpt.com'  => 'ai_chatgpt',
        'openai.com'   => 'ai_chatgpt',
        'perplexity.'  => 'ai_perplexity',
        'claude.ai'    => 'ai_claude',
        'gemini.google' => 'ai_gemini',
    );
    foreach ($hosts as $needle => $platform) {
        if (strpos($ref, $needle) !== false) return $platform;
    }
    return 'referral:' . $ref;
}

/** לבקשת זיו: גוגל אורגני + ישיר מוצגים כשורה אחת בפילוחי הפלטפורמה. */
function olsi_clicks_merge_direct_organic($tally) {
    $g = isset($tally['google_organic']) ? $tally['google_organic'] : 0;
    $d = isset($tally['direct']) ? $tally['direct'] : 0;
    if ($g + $d > 0) {
        unset($tally['google_organic'], $tally['direct']);
        $tally['google_direct'] = $g + $d;
        arsort($tally);
    }
    return $tally;
}

/** תווית פלטפורמה לשורה בודדת בטבלאות הפירוט - גם שם מאוחד. */
function olsi_clicks_platform_row_label($p) {
    if ($p === 'direct' || $p === 'google_organic') return 'חיפוש אורגני בגוגל / ישיר';
    return olsi_clicks_platform_label($p);
}

/** Hebrew label for a platform key. */
function olsi_clicks_platform_label($p) {
    $labels = array(
        'google_direct' => 'חיפוש אורגני / כניסה ישירה',
        'direct' => 'כניסה ישירה', 'google_organic' => 'גוגל - חיפוש אורגני',
        'google_ads' => 'גוגל - קמפיין ממומן', 'bing_organic' => 'Bing - אורגני',
        'bing_ads' => 'Bing - ממומן', 'duckduckgo' => 'DuckDuckGo', 'yahoo' => 'Yahoo',
        'yandex' => 'Yandex', 'facebook' => 'פייסבוק', 'instagram' => 'אינסטגרם',
        'linkedin' => 'לינקדאין', 'whatsapp' => 'וואטסאפ', 'youtube' => 'יוטיוב',
        'tiktok' => 'טיקטוק', 'twitter' => 'X / טוויטר', 'telegram' => 'טלגרם',
        'email' => 'דיוור / מייל', 'ai_chatgpt' => 'ChatGPT', 'ai_perplexity' => 'Perplexity',
        'ai_claude' => 'Claude', 'ai_gemini' => 'Gemini',
    );
    if (isset($labels[$p])) return $labels[$p];
    if (strpos($p, 'referral:') === 0) return 'אתר מפנה - ' . substr($p, 9);
    if (strpos($p, 'campaign:') === 0) return 'קמפיין - ' . substr($p, 9);
    return $p;
}

function olsi_clicks_placement_label($p) {
    $labels = array(
        'header' => 'הדר', 'footer_form' => 'בלוק יצירת קשר', 'footer' => 'פוטר',
        'float' => 'כפתור צף', 'contact_section' => 'אזור צרו קשר', 'content' => 'גוף המאמר',
        'thank_you' => 'עמוד תודה', 'other' => 'אחר',
    );
    return isset($labels[$p]) ? $labels[$p] : $p;
}

function olsi_clicks_button_label($b) {
    $labels = array(
        'header_whatsapp'   => 'וואטסאפ בהדר',
        'header_call_icon'  => 'חיוג מהיר בהדר (נייד)',
        'header_phone_text' => 'מספר בהדר (דסקטופ)',
        'cta_whatsapp'      => 'וואטסאפ בבלוק יצירת קשר',
        'cta_call'          => 'חייגו עכשיו',
        'float_whatsapp'    => 'וואטסאפ צף',
        'form'              => 'טופס יצירת קשר',
    );
    if ($b === '') return 'קישור טלפון';
    return isset($labels[$b]) ? $labels[$b] : $b;
}

function olsi_clicks_kind_label($k) {
    if ($k === 'whatsapp') return 'וואטסאפ';
    if ($k === 'form') return 'טופס';
    return 'חיוג';
}

/* =========================================================================
   4) SUMMARY EMAIL
   The scheduled daily email was discontinued 2026-08-02 (client request) -
   the weekly report below is the only scheduled mail. The manual "send now"
   button on the admin screen still uses olsi_clicks_send_summary().
   ========================================================================= */

add_action('init', 'olsi_clicks_schedule');
function olsi_clicks_schedule() {
    if (wp_next_scheduled('olsi_clicks_daily')) {
        wp_clear_scheduled_hook('olsi_clicks_daily');
    }
}

function olsi_clicks_send_summary($hours = 24, $include_admin = false) {
    $rows  = olsi_clicks_window($hours, $include_admin);
    $to    = olsi_clicks_recipients();
    if (empty($to)) return false;

    $tz    = new DateTimeZone(OLSI_CLICKS_TZ);
    $now   = new DateTime('now', $tz);
    $title = 'סיכום לחיצות יצירת קשר - אולסי מערכות - ' . $now->format('d/m/Y');

    $html    = olsi_clicks_email_html($rows, $hours, $now);
    return wp_mail($to, $title, $html, olsi_clicks_mail_headers());
}

function olsi_clicks_window($hours, $include_admin) {
    $log = get_option(OLSI_CLICKS_OPT, array());
    if (!is_array($log)) return array();
    $from = time() - ($hours * HOUR_IN_SECONDS);
    $out = array();
    foreach ($log as $r) {
        if (!isset($r['t']) || $r['t'] < $from) continue;
        if (!$include_admin && !empty($r['adm'])) continue;   // ignore our own testing
        $out[] = $r;
    }
    return $out;
}

function olsi_clicks_tally($rows, $key) {
    $t = array();
    foreach ($rows as $r) {
        $v = isset($r[$key]) && $r[$key] !== '' ? $r[$key] : '-';
        if (!isset($t[$v])) $t[$v] = 0;
        $t[$v]++;
    }
    arsort($t);
    return $t;
}

function olsi_clicks_email_html($rows, $hours, DateTime $now) {
    $total = count($rows);
    $wa = 0; $ph = 0; $fm = 0; $mob = 0;
    foreach ($rows as $r) {
        if ($r['k'] === 'whatsapp') $wa++; elseif ($r['k'] === 'form') $fm++; else $ph++;
        if ($r['d'] === 'mobile') $mob++;
    }
    $desk = $total - $mob;

    $E = 'esc_html';
    // Gmail strips a document-level dir attribute, so every block repeats dir="rtl".
    // Keep this to the attribute ONLY - each element appends its own single style=""
    // (two style attributes on one tag and the browser drops the second).
    $R = ' dir="rtl"';

    $h  = '<div' . $R . ' style="direction:rtl;text-align:right;background:#FAF6FD;padding:24px 12px;font-family:Arial,Helvetica,sans-serif;color:#1A1226;">';
    $h .= '<div' . $R . ' style="direction:rtl;text-align:right;max-width:680px;margin:0 auto;background:#ffffff;border-radius:16px;overflow:hidden;border:1px solid #EFE6F7;">';

    // header band
    $h .= '<div' . $R . ' style="direction:rtl;text-align:right;background:linear-gradient(120deg,#9333EA,#DB2777,#E0457B);padding:22px 24px;color:#fff;">';
    $h .= '<div style="font-size:19px;font-weight:700;">סיכום לחיצות יצירת קשר</div>';
    $h .= '<div style="font-size:13px;opacity:.92;margin-top:4px;">אולסי מערכות &#183; ' . $E($now->format('d/m/Y')) . ' &#183; ' . (int) $hours . ' השעות האחרונות</div>';
    $h .= '</div>';

    $h .= '<div' . $R . ' style="direction:rtl;text-align:right;padding:22px 24px;">';

    // stat cards
    $card = function ($label, $value, $color) {
        return '<td dir="rtl" align="center" style="direction:rtl;width:25%;padding:14px 8px;background:#FAF5FF;border-radius:12px;">'
             . '<div style="font-size:28px;font-weight:700;color:' . $color . ';line-height:1;">' . (int) $value . '</div>'
             . '<div style="font-size:12px;color:#5C5470;margin-top:6px;">' . $label . '</div></td>';
    };
    $h .= '<table dir="rtl" role="presentation" width="100%" cellpadding="0" cellspacing="6" style="direction:rtl;border-collapse:separate;"><tr>';
    $h .= $card('סה&quot;כ פניות', $total, '#9333EA');
    $h .= $card('וואטסאפ', $wa, '#1FA855');
    $h .= $card('חיוג', $ph, '#C2185B');
    $h .= $card('טפסים', $fm, '#8a6d3b');
    $h .= '</tr></table>';

    $sec = function ($t) use ($R) {
        return '<div' . $R . ' style="direction:rtl;text-align:right;font-size:15px;font-weight:700;margin:22px 0 8px;color:#1A1226;">' . $t . '</div>';
    };
    $bars = function ($tally, $total, $labeller = null) use ($R) {
        if (empty($tally)) return '<div' . $R . ' style="direction:rtl;text-align:right;color:#8A8299;font-size:13px;">אין נתונים</div>';
        $out = '<table dir="rtl" role="presentation" width="100%" cellpadding="0" cellspacing="0" style="direction:rtl;border-collapse:collapse;font-size:13px;">';
        foreach ($tally as $k => $n) {
            $label = $labeller ? call_user_func($labeller, $k) : $k;
            $pct   = $total > 0 ? round($n * 100 / $total) : 0;
            $out .= '<tr dir="rtl" style="direction:rtl;">'
                  . '<td dir="rtl" style="direction:rtl;text-align:right;padding:6px 0;color:#3C3450;">' . esc_html($label) . '</td>'
                  . '<td dir="rtl" style="direction:rtl;text-align:left;padding:6px 0;white-space:nowrap;color:#5C5470;">'
                  . '<span style="display:inline-block;height:8px;width:' . max(6, (int) round($pct * 1.7)) . 'px;background:linear-gradient(90deg,#9333EA,#DB2777);border-radius:4px;vertical-align:middle;margin-left:8px;"></span>'
                  . '<b style="color:#1A1226;">' . (int) $n . '</b> (' . $pct . '%)</td></tr>';
        }
        return $out . '</table>';
    };

    // device
    $h .= $sec('פילוח לפי מכשיר');
    $h .= $bars(array('נייד' => $mob, 'דסקטופ' => $desk), $total);

    // platform - the "where did they come from" breakdown
    $h .= $sec('מאיזו פלטפורמה הגיעו');
    $h .= $bars(olsi_clicks_merge_direct_organic(olsi_clicks_tally($rows, 'plat')), $total, 'olsi_clicks_platform_label');

    // button + placement
    $h .= $sec('לפי כפתור');
    $h .= $bars(olsi_clicks_tally($rows, 'lb'), $total, 'olsi_clicks_button_label');

    $h .= $sec('לפי מיקום בעמוד');
    $h .= $bars(olsi_clicks_tally($rows, 'pl'), $total, 'olsi_clicks_placement_label');

    // top pages
    $pages = olsi_clicks_tally($rows, 'u');
    $pages = array_slice($pages, 0, 8, true);
    $h .= $sec('העמודים המובילים');
    $h .= $bars($pages, $total);

    // detail table
    $h .= $sec('פירוט (' . min(60, $total) . ' אחרונות)');
    if ($total === 0) {
        $h .= '<div' . $R . ' style="direction:rtl;text-align:right;color:#8A8299;font-size:13px;">לא נרשמו לחיצות בטווח הזה.</div>';
    } else {
        $recent = array_slice($rows, -60);
        $recent = array_reverse($recent);
        $h .= '<table dir="rtl" role="presentation" width="100%" cellpadding="0" cellspacing="0" style="direction:rtl;border-collapse:collapse;font-size:12px;">';
        $h .= '<tr dir="rtl" style="direction:rtl;background:#FAF5FF;">'
            . '<th dir="rtl" style="direction:rtl;text-align:right;padding:7px 6px;color:#5C5470;">שעה</th>'
            . '<th dir="rtl" style="direction:rtl;text-align:right;padding:7px 6px;color:#5C5470;">כפתור</th>'
            . '<th dir="rtl" style="direction:rtl;text-align:right;padding:7px 6px;color:#5C5470;">מכשיר</th>'
            . '<th dir="rtl" style="direction:rtl;text-align:right;padding:7px 6px;color:#5C5470;">פלטפורמה</th>'
            . '<th dir="rtl" style="direction:rtl;text-align:right;padding:7px 6px;color:#5C5470;">עמוד</th></tr>';
        $tz = new DateTimeZone(OLSI_CLICKS_TZ);
        foreach ($recent as $r) {
            $d = new DateTime('@' . $r['t']);
            $d->setTimezone($tz);
            $dot = ($r['k'] === 'whatsapp') ? '#1FA855' : (($r['k'] === 'form') ? '#8a6d3b' : '#C2185B');
            $h .= '<tr dir="rtl" style="direction:rtl;border-top:1px solid #F0EAF7;">'
                . '<td dir="rtl" style="direction:rtl;text-align:right;padding:7px 6px;color:#5C5470;white-space:nowrap;">' . esc_html($d->format('d/m H:i')) . '</td>'
                . '<td dir="rtl" style="direction:rtl;text-align:right;padding:7px 6px;">'
                . '<span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:' . $dot . ';margin-left:6px;"></span>'
                . esc_html(olsi_clicks_button_label(isset($r['lb']) ? $r['lb'] : '')) . '</td>'
                . '<td dir="rtl" style="direction:rtl;text-align:right;padding:7px 6px;color:#5C5470;">' . ($r['d'] === 'mobile' ? 'נייד' : 'דסקטופ') . '</td>'
                . '<td dir="rtl" style="direction:rtl;text-align:right;padding:7px 6px;color:#5C5470;">' . esc_html(olsi_clicks_platform_row_label(isset($r['plat']) ? $r['plat'] : '-')) . '</td>'
                . '<td dir="rtl" style="direction:rtl;text-align:right;padding:7px 6px;color:#5C5470;">' . esc_html($r['u']) . '</td></tr>';
        }
        $h .= '</table>';
    }

    $h .= '<div' . $R . ' style="direction:rtl;text-align:right;margin-top:20px;padding-top:14px;border-top:1px solid #F0EAF7;font-size:11px;color:#8A8299;line-height:1.7;">';
    $h .= 'לחיצה על כפתור מעידה על כוונת פנייה - היא אינה ליד מאושר. לחיצות של משתמשים מחוברים כמנהלי האתר אינן נכללות בסיכום.<br>';
    $h .= 'הדוח המלא: לוח הבקרה של וורדפרס &#8592; כלים &#8592; פניות מכפתורים.';
    $h .= '</div>';

    $h .= '</div></div></div>';
    return $h;
}

/* =========================================================================
   4b) FORM-LEAD LOGGING + WEEKLY REPORT (Sunday 07:30, Ziv only)
   The contact form is handled by the theme's REST endpoint /olsi/v1/contact,
   which appends a stage entry to the `olsi_contact_log` option on every
   attempt. A `delivered-*` stage means a real, verified lead - we piggyback on
   that option write, so the theme needs no changes and rebuilds can't break it.
   ========================================================================= */

function olsi_clicks_weekly_recipients() {
    $raw = get_option(OLSI_CLICKS_WRCPT, '');
    if (!is_string($raw) || trim($raw) === '') $raw = 'bzik23@gmail.com,oren@olsi.co.il,info@olsi.co.il,chen@youlead.co.il';
    $out = array();
    foreach (explode(',', $raw) as $e) {
        $e = trim($e);
        if ($e !== '' && is_email($e)) $out[] = $e;
    }
    return $out;
}

add_action('updated_option', 'olsi_clicks_on_contact_log', 10, 3);
function olsi_clicks_on_contact_log($option, $old, $new) {
    if ($option !== 'olsi_contact_log' || !is_array($new) || empty($new)) return;
    $last = end($new);
    if (!is_array($last) || !isset($last['stage']) || strpos((string) $last['stage'], 'delivered') !== 0) return;
    olsi_clicks_log_form_row();
}

function olsi_clicks_log_form_row() {
    $ua = isset($_SERVER['HTTP_USER_AGENT']) ? (string) $_SERVER['HTTP_USER_AGENT'] : '';
    if (olsi_clicks_is_bot($ua)) return;

    $vis = olsi_clicks_visitor($ua);
    $log = get_option(OLSI_CLICKS_OPT, array());
    if (!is_array($log)) $log = array();

    $now = time();
    $cut = $now - 120;
    for ($i = count($log) - 1; $i >= 0; $i--) {
        if (!isset($log[$i]['t']) || $log[$i]['t'] < $cut) break;
        if ($log[$i]['v'] === $vis && isset($log[$i]['k']) && $log[$i]['k'] === 'form') return;
    }

    // The submitting page: the form posts a hidden "עמוד מקור" field (PHP mangles
    // the space to an underscore), with the REST referer as fallback.
    $page = '';
    if (isset($_POST['עמוד_מקור'])) {
        $page = sanitize_text_field(wp_unslash((string) $_POST['עמוד_מקור']));
    }
    if ($page === '' && isset($_SERVER['HTTP_REFERER'])) {
        $page = (string) wp_unslash($_SERVER['HTTP_REFERER']);
    }
    $path = (string) wp_parse_url($page, PHP_URL_PATH);
    if ($path === '') $path = '/';

    // Session source from the cookie copy the tracker script writes.
    $ref = ''; $us = ''; $um = ''; $uc = ''; $ci = ''; $lp = '';
    if (isset($_COOKIE['olsi_src'])) {
        $c = json_decode(stripslashes((string) $_COOKIE['olsi_src']), true);
        if (is_array($c)) {
            $ref = isset($c['ref']) ? strtolower((string) $c['ref']) : '';
            $us  = isset($c['us']) ? strtolower((string) $c['us']) : '';
            $um  = isset($c['um']) ? strtolower((string) $c['um']) : '';
            $uc  = isset($c['uc']) ? (string) $c['uc'] : '';
            $ci  = isset($c['ci']) ? (string) $c['ci'] : '';
            $lp  = isset($c['lp']) ? (string) $c['lp'] : '';
        }
    }
    $plat = ($ref === '' && $us === '' && $ci === '' && !isset($_COOKIE['olsi_src'])) ? 'unknown' : olsi_clicks_platform($ref, $us, $um, $ci);

    $log[] = array(
        't'    => $now,
        'k'    => 'form',
        'pl'   => 'footer_form',
        'lb'   => 'form',
        'd'    => preg_match('/Mobi|iPhone|Android/i', $ua) ? 'mobile' : 'desktop',
        'u'    => function_exists('mb_substr') ? mb_substr($path, 0, 160) : substr($path, 0, 160),
        'ti'   => '',
        'plat' => $plat,
        'ref'  => $ref,
        'us'   => $us,
        'um'   => $um,
        'uc'   => $uc,
        'lp'   => $lp,
        'v'    => $vis,
        'adm'  => (is_user_logged_in() && current_user_can('manage_options')) ? 1 : 0,
    );
    $log = olsi_clicks_prune($log);
    update_option(OLSI_CLICKS_OPT, $log, false);
}

/* ---- one-time upgrade: backfill delivered leads from olsi_contact_log ---- */

add_action('init', 'olsi_clicks_upgrade', 4);
function olsi_clicks_upgrade() {
    if (get_option('olsi_clicks_ver') === OLSI_CLICKS_VER) return;

    $log = get_option(OLSI_CLICKS_OPT, array());
    if (!is_array($log)) $log = array();
    $has_form = false;
    foreach ($log as $r) {
        if (isset($r['k']) && $r['k'] === 'form') { $has_form = true; break; }
    }
    if (!$has_form) {
        // olsi_contact_log keeps the last 25 attempts; t = current_time('mysql')
        // and the site timezone is UTC, so parse the stamp as UTC.
        $cl = get_option('olsi_contact_log', array());
        if (is_array($cl)) {
            $n = 0;
            foreach ($cl as $e) {
                if (!is_array($e) || !isset($e['stage'], $e['t'])) continue;
                if (strpos((string) $e['stage'], 'delivered') !== 0) continue;
                $ts = strtotime($e['t'] . ' UTC');
                if (!$ts) continue;
                $n++;
                $log[] = array(
                    't' => $ts, 'k' => 'form', 'pl' => 'footer_form', 'lb' => 'form',
                    'd' => 'desktop', 'u' => '/', 'ti' => '', 'plat' => 'unknown',
                    'ref' => '', 'us' => '', 'um' => '', 'uc' => '', 'lp' => '',
                    'v' => substr(md5('ocl|' . $e['t'] . '|' . $n), 0, 12), 'adm' => 0,
                );
            }
            if ($n > 0) {
                usort($log, 'olsi_clicks_sort_by_t');
                update_option(OLSI_CLICKS_OPT, olsi_clicks_prune($log), false);
            }
        }
    }

    // (Re)schedule the weekly report.
    $ts = wp_next_scheduled('olsi_clicks_weekly');
    while ($ts) {
        wp_unschedule_event($ts, 'olsi_clicks_weekly');
        $ts = wp_next_scheduled('olsi_clicks_weekly');
    }
    olsi_clicks_schedule_weekly();
    update_option('olsi_clicks_ver', OLSI_CLICKS_VER, false);
}

function olsi_clicks_sort_by_t($a, $b) {
    $ta = isset($a['t']) ? (int) $a['t'] : 0;
    $tb = isset($b['t']) ? (int) $b['t'] : 0;
    if ($ta === $tb) return 0;
    return ($ta < $tb) ? -1 : 1;
}

/* ---- weekly schedule: Sunday 07:30 Israel time ---- */

add_filter('cron_schedules', 'olsi_clicks_cron_weekly');
function olsi_clicks_cron_weekly($schedules) {
    if (!isset($schedules['weekly'])) {
        $schedules['weekly'] = array('interval' => WEEK_IN_SECONDS, 'display' => 'פעם בשבוע');
    }
    return $schedules;
}

add_action('init', 'olsi_clicks_schedule_weekly');
function olsi_clicks_schedule_weekly() {
    if (wp_next_scheduled('olsi_clicks_weekly')) return;
    $tz   = new DateTimeZone(OLSI_CLICKS_TZ);
    $now  = new DateTime('now', $tz);
    $next = new DateTime($now->format('Y-m-d') . ' 07:30:00', $tz);
    if ('0' !== $now->format('w') || $next->getTimestamp() <= $now->getTimestamp()) {
        $next->modify('next sunday');
        $next = new DateTime($next->format('Y-m-d') . ' 07:30:00', $tz);
    }
    wp_schedule_event($next->getTimestamp(), 'weekly', 'olsi_clicks_weekly');
}

add_action('olsi_clicks_weekly', 'olsi_clicks_send_weekly');

/** Weekly report: the finished calendar week (Sunday-Saturday) + comparison. */
function olsi_clicks_send_weekly() {
    $to = olsi_clicks_weekly_recipients();
    if (empty($to)) return false;

    $tz    = new DateTimeZone(OLSI_CLICKS_TZ);
    $end   = new DateTime('today 00:00', $tz);
    $start = clone $end;
    $start->modify('-7 days');
    $prev_start = clone $start;
    $prev_start->modify('-7 days');

    $rows = olsi_clicks_window_range($start->getTimestamp(), $end->getTimestamp());
    $prev = count(olsi_clicks_window_range($prev_start->getTimestamp(), $start->getTimestamp()));

    $last = clone $end;
    $last->modify('-1 day');
    $range = $start->format('d/m/Y') . ' עד ' . $last->format('d/m/Y');

    $subject = 'אולסי מערכות | סיכום שבועי - פניות מהאתר (' . count($rows) . ')';
    $html    = olsi_clicks_weekly_email_html($rows, $range, $prev);
    return wp_mail($to, $subject, $html, olsi_clicks_mail_headers());
}

function olsi_clicks_window_range($from, $to) {
    $log = get_option(OLSI_CLICKS_OPT, array());
    if (!is_array($log)) return array();
    $out = array();
    foreach ($log as $r) {
        if (!isset($r['t']) || $r['t'] < $from || $r['t'] >= $to) continue;
        if (!empty($r['adm'])) continue;
        $out[] = $r;
    }
    return $out;
}

function olsi_clicks_weekly_email_html($rows, $range, $prev_total) {
    $total = count($rows);
    $wa = 0; $ph = 0; $fm = 0; $mob = 0;
    $by_day = array();
    $tz = new DateTimeZone(OLSI_CLICKS_TZ);
    foreach ($rows as $r) {
        if ($r['k'] === 'whatsapp') $wa++; elseif ($r['k'] === 'form') $fm++; else $ph++;
        if ($r['d'] === 'mobile') $mob++;
        $d = new DateTime('@' . $r['t']);
        $d->setTimezone($tz);
        $dk = $d->format('Y-m-d');
        $by_day[$dk] = isset($by_day[$dk]) ? $by_day[$dk] + 1 : 1;
    }
    $desk = $total - $mob;
    ksort($by_day);

    $R = ' dir="rtl"';
    $h  = '<div' . $R . ' style="direction:rtl;text-align:right;background:#FAF6FD;padding:24px 12px;font-family:Arial,Helvetica,sans-serif;color:#1A1226;">';
    $h .= '<div' . $R . ' style="direction:rtl;text-align:right;max-width:680px;margin:0 auto;background:#ffffff;border-radius:16px;overflow:hidden;border:1px solid #EFE6F7;">';

    $h .= '<div' . $R . ' style="direction:rtl;text-align:right;background:linear-gradient(120deg,#9333EA,#DB2777,#E0457B);padding:22px 24px;color:#fff;">';
    $h .= '<div style="font-size:19px;font-weight:700;">סיכום שבועי - פניות מהאתר</div>';
    $h .= '<div style="font-size:13px;opacity:.92;margin-top:4px;">אולסי מערכות &#183; וואטסאפ, חיוג וטפסים &#183; ' . esc_html($range) . '</div>';
    $h .= '</div>';

    $h .= '<div' . $R . ' style="direction:rtl;text-align:right;padding:22px 24px;">';

    $card = function ($label, $value, $color) {
        return '<td dir="rtl" align="center" style="direction:rtl;width:25%;padding:14px 8px;background:#FAF5FF;border-radius:12px;">'
             . '<div style="font-size:28px;font-weight:700;color:' . $color . ';line-height:1;">' . (int) $value . '</div>'
             . '<div style="font-size:12px;color:#5C5470;margin-top:6px;">' . $label . '</div></td>';
    };
    $h .= '<table dir="rtl" role="presentation" width="100%" cellpadding="0" cellspacing="6" style="direction:rtl;border-collapse:separate;"><tr>';
    $h .= $card('סה&quot;כ פניות', $total, '#9333EA');
    $h .= $card('וואטסאפ', $wa, '#1FA855');
    $h .= $card('חיוג', $ph, '#C2185B');
    $h .= $card('טפסים', $fm, '#8a6d3b');
    $h .= '</tr></table>';

    if ($prev_total > 0) {
        $diff  = $total - $prev_total;
        $pct   = round(abs($diff) * 100 / $prev_total);
        $color = ($diff >= 0) ? '#1a8917' : '#b32d2e';
        $arrow = ($diff >= 0) ? '&#9650;' : '&#9660;';
        $word  = ($diff >= 0) ? 'עלייה' : 'ירידה';
        $cmp   = (0 === $diff)
            ? 'ללא שינוי לעומת השבוע הקודם (' . (int) $prev_total . ')'
            : $arrow . ' ' . $word . ' של ' . $pct . '% לעומת השבוע הקודם (' . (int) $prev_total . ')';
        $h .= '<div' . $R . ' style="direction:rtl;text-align:right;font-size:13px;font-weight:700;color:' . $color . ';margin-top:10px;">' . $cmp . '</div>';
    } else {
        $h .= '<div' . $R . ' style="direction:rtl;text-align:right;font-size:13px;color:#8A8299;margin-top:10px;">אין נתוני השוואה לשבוע הקודם</div>';
    }

    $sec = function ($t) use ($R) {
        return '<div' . $R . ' style="direction:rtl;text-align:right;font-size:15px;font-weight:700;margin:22px 0 8px;color:#1A1226;">' . $t . '</div>';
    };
    $bars = function ($tally, $total, $labeller = null) use ($R) {
        if (empty($tally)) return '<div' . $R . ' style="direction:rtl;text-align:right;color:#8A8299;font-size:13px;">אין נתונים</div>';
        $out = '<table dir="rtl" role="presentation" width="100%" cellpadding="0" cellspacing="0" style="direction:rtl;border-collapse:collapse;font-size:13px;">';
        foreach ($tally as $k => $n) {
            $label = $labeller ? call_user_func($labeller, $k) : $k;
            $pct   = $total > 0 ? round($n * 100 / $total) : 0;
            $out .= '<tr dir="rtl" style="direction:rtl;">'
                  . '<td dir="rtl" style="direction:rtl;text-align:right;padding:6px 0;color:#3C3450;">' . esc_html($label) . '</td>'
                  . '<td dir="rtl" style="direction:rtl;text-align:left;padding:6px 0;white-space:nowrap;color:#5C5470;">'
                  . '<span style="display:inline-block;height:8px;width:' . max(6, (int) round($pct * 1.7)) . 'px;background:linear-gradient(90deg,#9333EA,#DB2777);border-radius:4px;vertical-align:middle;margin-left:8px;"></span>'
                  . '<b style="color:#1A1226;">' . (int) $n . '</b> (' . $pct . '%)</td></tr>';
        }
        return $out . '</table>';
    };

    if ($total > 0) {
        // daily breakdown
        $names = array('ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת');
        $days = array();
        foreach ($by_day as $dk => $n) {
            $d = new DateTime($dk, $tz);
            $days['יום ' . $names[(int) $d->format('w')] . ', ' . $d->format('d/m')] = $n;
        }
        $h .= $sec('פילוח יומי');
        $h .= $bars($days, max($by_day));

        $h .= $sec('פילוח לפי מכשיר');
        $h .= $bars(array('נייד' => $mob, 'דסקטופ' => $desk), $total);

        $h .= $sec('מאיזו פלטפורמה הגיעו');
        $h .= $bars(olsi_clicks_merge_direct_organic(olsi_clicks_tally($rows, 'plat')), $total, 'olsi_clicks_platform_label');

        $h .= $sec('לפי כפתור');
        $h .= $bars(olsi_clicks_tally($rows, 'lb'), $total, 'olsi_clicks_button_label');

        $pages = olsi_clicks_tally($rows, 'u');
        $pages = array_slice($pages, 0, 8, true);
        $h .= $sec('העמודים המובילים');
        $h .= $bars($pages, $total);

        // detail table
        $h .= $sec('פירוט הפניות האחרונות (' . min(60, $total) . ')');
        $recent = array_slice($rows, -60);
        $recent = array_reverse($recent);
        $h .= '<table dir="rtl" role="presentation" width="100%" cellpadding="0" cellspacing="0" style="direction:rtl;border-collapse:collapse;font-size:12px;">';
        $h .= '<tr dir="rtl" style="direction:rtl;background:#FAF5FF;">'
            . '<th dir="rtl" style="direction:rtl;text-align:right;padding:7px 6px;color:#5C5470;">מתי</th>'
            . '<th dir="rtl" style="direction:rtl;text-align:right;padding:7px 6px;color:#5C5470;">ערוץ</th>'
            . '<th dir="rtl" style="direction:rtl;text-align:right;padding:7px 6px;color:#5C5470;">מכשיר</th>'
            . '<th dir="rtl" style="direction:rtl;text-align:right;padding:7px 6px;color:#5C5470;">פלטפורמה</th>'
            . '<th dir="rtl" style="direction:rtl;text-align:right;padding:7px 6px;color:#5C5470;">עמוד</th></tr>';
        foreach ($recent as $r) {
            $d = new DateTime('@' . $r['t']);
            $d->setTimezone($tz);
            $dot = ($r['k'] === 'whatsapp') ? '#1FA855' : (($r['k'] === 'form') ? '#8a6d3b' : '#C2185B');
            $h .= '<tr dir="rtl" style="direction:rtl;border-top:1px solid #F0EAF7;">'
                . '<td dir="rtl" style="direction:rtl;text-align:right;padding:7px 6px;color:#5C5470;white-space:nowrap;">' . esc_html($d->format('d/m H:i')) . '</td>'
                . '<td dir="rtl" style="direction:rtl;text-align:right;padding:7px 6px;">'
                . '<span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:' . $dot . ';margin-left:6px;"></span>'
                . esc_html(olsi_clicks_kind_label($r['k'])) . '</td>'
                . '<td dir="rtl" style="direction:rtl;text-align:right;padding:7px 6px;color:#5C5470;">' . ($r['d'] === 'mobile' ? 'נייד' : 'דסקטופ') . '</td>'
                . '<td dir="rtl" style="direction:rtl;text-align:right;padding:7px 6px;color:#5C5470;">' . esc_html(olsi_clicks_platform_row_label(isset($r['plat']) ? $r['plat'] : '-')) . '</td>'
                . '<td dir="rtl" style="direction:rtl;text-align:right;padding:7px 6px;color:#5C5470;">' . esc_html($r['u']) . '</td></tr>';
        }
        $h .= '</table>';
    } else {
        $h .= '<div' . $R . ' style="direction:rtl;text-align:right;color:#8A8299;font-size:13px;margin-top:16px;">לא נרשמו פניות בשבוע הזה.</div>';
    }

    $h .= '<div' . $R . ' style="direction:rtl;text-align:right;margin-top:20px;padding-top:14px;border-top:1px solid #F0EAF7;font-size:11px;color:#8A8299;line-height:1.7;">';
    $h .= 'לחיצה על כפתור וואטסאפ או חיוג מעידה על כוונת פנייה - היא אינה ליד מאושר. "טופס" = שליחת טופס יצירת קשר שאומתה ונמסרה. פניות של מנהלי האתר אינן נכללות.<br>';
    $h .= 'הדוח נשלח אוטומטית בכל יום ראשון בשעה 07:30 ומסכם את השבוע שהסתיים (ראשון עד שבת).';
    $h .= '</div>';

    $h .= '</div></div></div>';
    return $h;
}

/* =========================================================================
   5) ADMIN SCREEN - Tools -> "פניות מכפתורים"
   ========================================================================= */

add_action('admin_menu', 'olsi_clicks_menu');
function olsi_clicks_menu() {
    add_management_page('פניות מכפתורים', 'פניות מכפתורים', 'manage_options', 'olsi-clicks', 'olsi_clicks_admin');
}

function olsi_clicks_admin() {
    if (!current_user_can('manage_options')) return;
    $notice = '';

    if (isset($_POST['olsi_clicks_save']) && check_admin_referer('olsi_clicks')) {
        update_option(OLSI_CLICKS_RCPT, sanitize_text_field(wp_unslash($_POST['recipients'])));
        $notice = 'הנמענים נשמרו.';
    }
    if (isset($_POST['olsi_clicks_send']) && check_admin_referer('olsi_clicks')) {
        $hours = max(1, min(720, (int) $_POST['hours']));
        $ok = olsi_clicks_send_summary($hours, false);
        $notice = $ok ? 'הסיכום נשלח אל: ' . implode(', ', olsi_clicks_recipients()) : 'שליחת המייל נכשלה.';
    }
    if (isset($_POST['olsi_clicks_wsave']) && check_admin_referer('olsi_clicks')) {
        update_option(OLSI_CLICKS_WRCPT, sanitize_text_field(wp_unslash($_POST['weekly_recipients'])));
        $notice = 'נמעני הדוח השבועי נשמרו.';
    }
    if (isset($_POST['olsi_clicks_wsend']) && check_admin_referer('olsi_clicks')) {
        $ok = olsi_clicks_send_weekly();
        $notice = $ok ? 'הדוח השבועי נשלח אל: ' . implode(', ', olsi_clicks_weekly_recipients()) : 'שליחת הדוח השבועי נכשלה.';
    }
    if (isset($_POST['olsi_smtp_save']) && check_admin_referer('olsi_clicks')) {
        $cur = get_option('olsi_smtp', array());
        if (!is_array($cur)) $cur = array();
        $pass = trim((string) wp_unslash($_POST['smtp_pass']));
        $cfg = array(
            'host'       => sanitize_text_field(wp_unslash($_POST['smtp_host'])),
            'port'       => max(1, min(65535, (int) $_POST['smtp_port'])),
            'user'       => sanitize_text_field(wp_unslash($_POST['smtp_user'])),
            // Leaving the password field blank keeps the stored one (never echoed back).
            'pass'       => $pass !== '' ? $pass : (isset($cur['pass']) ? $cur['pass'] : ''),
            'secure'     => in_array($_POST['smtp_secure'], array('tls', 'ssl', ''), true) ? $_POST['smtp_secure'] : 'tls',
            'from_email' => sanitize_email(wp_unslash($_POST['smtp_from_email'])),
            'from_name'  => sanitize_text_field(wp_unslash($_POST['smtp_from_name'])),
        );
        update_option('olsi_smtp', $cfg, false);
        $notice = 'הגדרות ה-SMTP נשמרו.';
    }
    if (isset($_POST['olsi_smtp_test']) && check_admin_referer('olsi_clicks')) {
        $to = sanitize_email(wp_unslash($_POST['smtp_test_to']));
        if (!$to) $to = get_option('admin_email');
        $body = '<div dir="rtl" style="direction:rtl;text-align:right;font-family:Arial;">'
              . '<h2 style="color:#9333EA;">בדיקת מסירה - אולסי מערכות</h2>'
              . '<p>אם קיבלת את המייל הזה, רילאי ה-SMTP עובד והדוח השבועי יגיע.</p></div>';
        $ok = wp_mail($to, 'בדיקת SMTP - אולסי מערכות', $body, array('Content-Type: text/html; charset=UTF-8'));
        $notice = $ok ? 'מייל בדיקה נשלח אל ' . $to . ' (בדוק גם ספאם).' : 'שליחת מייל הבדיקה נכשלה.';
    }

    $log  = get_option(OLSI_CLICKS_OPT, array());
    if (!is_array($log)) $log = array();
    $rows = array_reverse(array_slice($log, -300));
    $tz   = new DateTimeZone(OLSI_CLICKS_TZ);

    echo '<div class="wrap"><h1>פניות מכפתורים</h1>';
    if ($notice) echo '<div class="notice notice-success"><p>' . esc_html($notice) . '</p></div>';

    echo '<p>מדידת לחיצות על כפתורי החיוג המהיר והוואטסאפ בכל עמודי האתר (הדר, בלוק יצירת קשר, פוטר והכפתור הצף), בנייד ובדסקטופ.</p>';

    $nextw = wp_next_scheduled('olsi_clicks_weekly');
    if ($nextw) {
        $dw = new DateTime('@' . $nextw);
        $dw->setTimezone($tz);
        echo '<p><strong>הדוח השבועי הבא (' . esc_html(implode(', ', olsi_clicks_weekly_recipients())) . '):</strong> ' . esc_html($dw->format('d/m/Y H:i')) . ' (שעון ישראל)</p>';
    }

    echo '<form method="post" style="margin:18px 0;padding:14px;background:#fff;border:1px solid #ccd0d4;max-width:760px;">';
    wp_nonce_field('olsi_clicks');
    echo '<p><label><strong>נמענים לשליחה ידנית ("שלח עכשיו")</strong> (מופרדים בפסיק)<br>';
    echo '<input type="text" name="recipients" style="width:100%;max-width:560px;" value="' . esc_attr(implode(',', olsi_clicks_recipients())) . '"></label></p>';
    echo '<p><button class="button button-primary" name="olsi_clicks_save" value="1">שמירה</button></p>';
    echo '<hr><p><label>שלח סיכום עכשיו עבור <input type="number" name="hours" value="24" min="1" max="720" style="width:80px;"> השעות האחרונות</label> ';
    echo '<button class="button" name="olsi_clicks_send" value="1">שלח עכשיו</button></p>';
    echo '<hr><p><label><strong>נמעני הדוח השבועי</strong> (ראשון 07:30, מופרדים בפסיק)<br>';
    echo '<input type="text" name="weekly_recipients" style="width:100%;max-width:560px;" value="' . esc_attr(implode(',', olsi_clicks_weekly_recipients())) . '"></label></p>';
    echo '<p><button class="button" name="olsi_clicks_wsave" value="1">שמירת נמעני הדוח השבועי</button> ';
    echo '<button class="button" name="olsi_clicks_wsend" value="1">שלח דוח שבועי עכשיו (שבוע קודם)</button></p>';
    echo '</form>';

    // ---- SMTP relay settings (port 25 is blocked on this host) ----
    $smtp = get_option('olsi_smtp', array());
    if (!is_array($smtp)) $smtp = array();
    $active = olsi_smtp_config() !== null;
    echo '<form method="post" style="margin:18px 0;padding:14px;background:#fff;border:1px solid #ccd0d4;max-width:760px;">';
    wp_nonce_field('olsi_clicks');
    echo '<h2 style="margin-top:0;">שרת דואר יוצא (SMTP)</h2>';
    echo '<p style="color:#646970;">השרת חוסם שליחת דואר ישירה, לכן הדיווח נשלח דרך רילאי SMTP. סטטוס: '
       . ($active ? '<strong style="color:#1a8917;">פעיל</strong>' : '<strong style="color:#b32d2e;">לא מוגדר</strong>') . '</p>';
    $row = function ($label, $field) {
        echo '<tr><th scope="row" style="text-align:right;width:150px;">' . esc_html($label) . '</th><td>' . $field . '</td></tr>';
    };
    echo '<table class="form-table"><tbody>';
    $row('שרת (Host)', '<input type="text" name="smtp_host" style="width:320px;" value="' . esc_attr(isset($smtp['host']) ? $smtp['host'] : 'smtp-relay.brevo.com') . '">');
    $row('פורט', '<input type="number" name="smtp_port" style="width:90px;" value="' . esc_attr(isset($smtp['port']) ? $smtp['port'] : 587) . '"> <span style="color:#646970;">587 = TLS</span>');
    $row('הצפנה', '<select name="smtp_secure"><option value="tls"' . selected(isset($smtp['secure']) ? $smtp['secure'] : 'tls', 'tls', false) . '>TLS</option><option value="ssl"' . selected(isset($smtp['secure']) ? $smtp['secure'] : '', 'ssl', false) . '>SSL</option><option value=""' . selected(isset($smtp['secure']) ? $smtp['secure'] : 'tls', '', false) . '>ללא</option></select>');
    $row('שם משתמש', '<input type="text" name="smtp_user" style="width:320px;" value="' . esc_attr(isset($smtp['user']) ? $smtp['user'] : '') . '">');
    $row('סיסמה / מפתח', '<input type="password" name="smtp_pass" style="width:320px;" autocomplete="new-password" placeholder="' . (empty($smtp['pass']) ? 'הדבק כאן את מפתח ה-SMTP' : '•••••• (שמור - השאר ריק כדי לא לשנות)') . '">');
    $row('כתובת שולח', '<input type="email" name="smtp_from_email" style="width:320px;" value="' . esc_attr(isset($smtp['from_email']) ? $smtp['from_email'] : 'no-reply@olsi.co.il') . '">');
    $row('שם שולח', '<input type="text" name="smtp_from_name" style="width:320px;" value="' . esc_attr(isset($smtp['from_name']) ? $smtp['from_name'] : 'אולסי מערכות') . '">');
    echo '</tbody></table>';
    echo '<p><button class="button button-primary" name="olsi_smtp_save" value="1">שמירת SMTP</button></p>';
    echo '<hr><p><label>שלח מייל בדיקה אל <input type="email" name="smtp_test_to" style="width:280px;" value="' . esc_attr(get_option('admin_email')) . '"></label> ';
    echo '<button class="button" name="olsi_smtp_test" value="1">שלח בדיקה</button></p>';
    echo '</form>';

    echo '<p><strong>סה"כ רשומות בלוג:</strong> ' . count($log) . ' (נשמרות ' . OLSI_CLICKS_DAYS . ' יום)</p>';

    echo '<table class="widefat striped"><thead><tr>';
    foreach (array('מועד', 'סוג', 'כפתור', 'מיקום', 'מכשיר', 'פלטפורמה', 'מפנה', 'עמוד', 'מנהל') as $th) {
        echo '<th>' . esc_html($th) . '</th>';
    }
    echo '</tr></thead><tbody>';
    if (empty($rows)) {
        echo '<tr><td colspan="9">עדיין לא נרשמו לחיצות.</td></tr>';
    }
    foreach ($rows as $r) {
        $d = new DateTime('@' . $r['t']);
        $d->setTimezone($tz);
        echo '<tr>';
        echo '<td>' . esc_html($d->format('d/m/Y H:i:s')) . '</td>';
        echo '<td>' . esc_html(olsi_clicks_kind_label($r['k'])) . '</td>';
        echo '<td>' . esc_html(olsi_clicks_button_label(isset($r['lb']) ? $r['lb'] : '')) . '</td>';
        echo '<td>' . esc_html(olsi_clicks_placement_label($r['pl'])) . '</td>';
        echo '<td>' . ($r['d'] === 'mobile' ? 'נייד' : 'דסקטופ') . '</td>';
        echo '<td>' . esc_html(olsi_clicks_platform_label(isset($r['plat']) ? $r['plat'] : '-')) . '</td>';
        echo '<td>' . esc_html(isset($r['ref']) && $r['ref'] !== '' ? $r['ref'] : '-') . '</td>';
        echo '<td>' . esc_html($r['u']) . '</td>';
        echo '<td>' . (!empty($r['adm']) ? 'כן' : '') . '</td>';
        echo '</tr>';
    }
    echo '</tbody></table></div>';
}
