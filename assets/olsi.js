// 0. Force scroll-to-top on load - don't restore a remembered scroll position.
if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
window.addEventListener('pageshow', () => { if (!location.hash) window.scrollTo(0, 0); });

// 0b. WhatsApp buttons. The number is kept out of the page source (scrapers were
//     harvesting it from the wa.me links) - the markup carries it reversed + base64
//     and the real link is built only on a genuine interaction with the button.
(function() {
  const arm = a => {
    let num = '';
    try { num = atob(a.getAttribute('data-wa')).split('').reverse().join(''); } catch (e) { return; }
    a.href = 'https://wa.me/' + num + '?text=' + encodeURIComponent(a.getAttribute('data-wa-text') || '');
    a.target = '_blank';
    a.rel = 'noopener';
    a.removeAttribute('data-wa');
  };
  ['pointerdown', 'touchstart', 'mouseover', 'focusin', 'click'].forEach(type => {
    document.addEventListener(type, e => {
      if (!e.isTrusted || !e.target.closest) return;
      const a = e.target.closest('a[data-wa]');
      if (a) arm(a);
    }, { capture: true, passive: true });
  });
})();

// 1. Header transparency on scroll
const siteHeader = document.querySelector('.site-header');
const onScroll = () => siteHeader.classList.toggle('scrolled', window.scrollY > 10);
window.addEventListener('scroll', onScroll, { passive: true });
onScroll();

// 2. Mobile hamburger menu
(function() {
  const header = document.querySelector('.site-header');
  const btn = document.getElementById('hamburger');
  const backdrop = document.getElementById('menu-backdrop');
  const nav = document.getElementById('site-nav');
  if (!btn || !header) return;
  function close() {
    header.classList.remove('menu-open');
    btn.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  }
  function toggle() {
    const isOpen = header.classList.toggle('menu-open');
    btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    document.body.style.overflow = isOpen ? 'hidden' : '';
  }
  btn.addEventListener('click', toggle);
  if (backdrop) backdrop.addEventListener('click', close);
  // close the mobile menu when a real nav link is tapped - but NOT the
  // services-dropdown trigger (that toggles its own accordion instead).
  if (nav) nav.querySelectorAll('a:not(.nav-dropdown__trigger)').forEach(a => a.addEventListener('click', close));
  window.addEventListener('keydown', e => { if (e.key === 'Escape') close(); });
  window.addEventListener('resize', () => { if (window.innerWidth > 1024) close(); });
})();

// 3. IntersectionObserver scroll reveal, with reduced-motion guard
if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  // threshold:0 reveals as soon as any part of the element enters the viewport.
  // A larger threshold (e.g. 0.15) never fires for elements taller than the
  // viewport - 15% of a long article body exceeds the screen height - leaving
  // the whole post-body stuck at opacity:0. threshold:0 keeps the scroll-in
  // effect (via the -40px bottom margin) while guaranteeing tall blocks reveal.
  const io = new IntersectionObserver(entries => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); io.unobserve(e.target); } });
  }, { threshold: 0, rootMargin: '0px 0px -40px 0px' });
  document.querySelectorAll('[data-anim]').forEach(el => io.observe(el));
} else {
  document.querySelectorAll('[data-anim]').forEach(el => el.classList.add('visible'));
}

// 4. Clients logo slider - shows N logos at once (5 desktop / 3 tablet / 2 mobile)
//    and auto-advances ONE logo every 2.5s, looping infinitely. The whole set is
//    cloned once so the visible window is always full as it wraps around; on a
//    boundary we jump invisibly (clone view == real view) before the next step.
//    Pauses on hover, while the section is off-screen, and while the tab is hidden.
(function() {
  const viewport = document.querySelector('.logos__viewport');
  const track = document.getElementById('logos-track');
  const prev  = document.getElementById('logos-prev');
  const next  = document.getElementById('logos-next');
  const band  = document.querySelector('.logos');
  if (!track) return;

  const reducedMq = window.matchMedia('(prefers-reduced-motion: reduce)');
  const count = track.children.length;          // number of real logos (7)
  if (count < 2) return;

  // Clone the full set once -> window stays full through the wrap-around.
  Array.from(track.children).forEach(tile => track.appendChild(tile.cloneNode(true)));

  let index = 0;
  let step  = 0;
  let timer = null;
  let paused = false;
  let inView = false;

  // step = distance between adjacent tiles (tile width + gap), measured live so
  // it survives responsive breakpoint changes.
  function measure() {
    const tiles = track.children;
    step = tiles.length > 1
      ? Math.abs(tiles[1].offsetLeft - tiles[0].offsetLeft)
      : tiles[0].offsetWidth;
  }
  function place(animate) {
    track.classList.toggle('is-instant', !animate);
    track.style.transform = 'translateX(' + (-index * step) + 'px)';
  }
  function nextSlide() {
    if (index >= count) { index = 0; place(false); void track.offsetWidth; }
    index += 1; place(true);
  }
  function prevSlide() {
    if (index <= 0) { index = count; place(false); void track.offsetWidth; }
    index -= 1; place(true);
  }

  function start() {
    stop();
    if (paused || !inView || reducedMq.matches) return;
    timer = setInterval(nextSlide, 2500);
  }
  function stop() { if (timer) { clearInterval(timer); timer = null; } }

  if (prev) prev.addEventListener('click', prevSlide);
  if (next) next.addEventListener('click', nextSlide);

  if (viewport) {
    viewport.addEventListener('mouseenter', () => { paused = true;  stop();  });
    viewport.addEventListener('mouseleave', () => { paused = false; start(); });
  }
  document.addEventListener('visibilitychange', () => { document.hidden ? stop() : start(); });
  window.addEventListener('resize', () => { measure(); place(false); });

  // Only auto-advance while the logos band is on screen.
  if (band && 'IntersectionObserver' in window) {
    new IntersectionObserver((entries) => {
      inView = entries[0].isIntersecting;
      if (inView) start(); else stop();
    }, { threshold: 0.2 }).observe(band);
  } else {
    inView = true;
  }

  measure();
  place(false);
  window.addEventListener('load', () => { measure(); place(false); });
  start();
})();

// 4b. Mobile-only one-card slider, shared by the "process steps" and "sample projects"
//     sections. Below 767px the cards become a carousel: side arrows for manual nav
//     plus an autoplay that advances one card every 1.5s and loops forever. The full
//     set is cloned once (like the logos band) so the wrap-around is seamless; the
//     clones are torn down again if the viewport grows back to the desktop layout.
//     Pauses while touched, off-screen, or on a hidden tab, and respects reduced-motion.
function initMobileCardSlider(opts) {
  const track  = document.querySelector(opts.track);
  const slider = document.querySelector(opts.slider);
  if (!track || !slider) return;
  const prev = slider.querySelector(opts.prev);
  const next = slider.querySelector(opts.next);
  const band = (opts.band && document.querySelector(opts.band)) || slider;
  const cloneClass = opts.cloneClass;
  const interval = opts.interval || 1500;

  const reducedMq = window.matchMedia('(prefers-reduced-motion: reduce)');
  const mobileMq  = window.matchMedia('(max-width: 767px)');
  const realCards = Array.from(track.children);
  const count = realCards.length;
  if (count < 2) return;

  let active = false;   // carousel engaged (mobile only)
  let index  = 0;
  let step   = 0;       // px between adjacent cards (= viewport width)
  let timer  = null;
  let paused = false;   // visitor is touching the slider
  let inView = true;

  function measure() {
    const c = track.children;
    step = c.length > 1 ? Math.abs(c[1].offsetLeft - c[0].offsetLeft) : c[0].offsetWidth;
  }
  function place(animate) {
    track.classList.toggle('is-instant', !animate);
    track.style.transform = 'translateX(' + (-index * step) + 'px)';
  }
  function nextSlide() {
    if (index >= count) { index = 0; place(false); void track.offsetWidth; }
    index += 1; place(true);
  }
  function prevSlide() {
    if (index <= 0) { index = count; place(false); void track.offsetWidth; }
    index -= 1; place(true);
  }

  function start() {
    stop();
    if (!active || paused || !inView || reducedMq.matches) return;
    timer = setInterval(nextSlide, interval);
  }
  function stop() { if (timer) { clearInterval(timer); timer = null; } }

  function engage() {
    if (active) return;
    active = true;
    realCards.forEach(card => {
      const c = card.cloneNode(true);
      c.setAttribute('aria-hidden', 'true');
      c.classList.add(cloneClass);
      track.appendChild(c);
    });
    index = 0;
    measure();
    place(false);
    start();
  }
  function disengage() {
    if (!active) return;
    active = false;
    stop();
    track.querySelectorAll('.' + cloneClass).forEach(c => c.remove());
    track.classList.remove('is-instant');
    track.style.transform = '';
    index = 0;
  }
  function sync() { mobileMq.matches ? engage() : disengage(); }

  // manual nav restarts the autoplay clock so it doesn't jump right after a tap
  if (prev) prev.addEventListener('click', () => { if (active) { prevSlide(); start(); } });
  if (next) next.addEventListener('click', () => { if (active) { nextSlide(); start(); } });

  // pause while the visitor is actively touching a card
  slider.addEventListener('pointerdown', () => { paused = true;  stop();  });
  window.addEventListener('pointerup',   () => { paused = false; start(); });

  document.addEventListener('visibilitychange', () => { document.hidden ? stop() : start(); });
  window.addEventListener('resize', () => { sync(); if (active) { measure(); place(false); } });
  if (mobileMq.addEventListener) mobileMq.addEventListener('change', sync);
  else if (mobileMq.addListener) mobileMq.addListener(sync);

  if ('IntersectionObserver' in window) {
    new IntersectionObserver(entries => {
      inView = entries[0].isIntersecting;
      inView ? start() : stop();
    }, { threshold: 0.2 }).observe(band);
  }

  sync();
}

initMobileCardSlider({ track: '.process__track', slider: '.process__slider',
  prev: '#process-prev', next: '#process-next', band: '.process',
  cloneClass: 'proc-card--clone', interval: 1500 });
initMobileCardSlider({ track: '.work__list', slider: '.work__slider',
  prev: '#work-prev', next: '#work-next', band: '.work',
  cloneClass: 'work-card--clone', interval: 1500 });

// 5. Services dropdown.
//    Desktop: opens on hover / keyboard focus (pure CSS).
//    Mobile + touch: tapping the "שירותים" trigger toggles an accordion.
(function() {
  const dd = document.getElementById('nav-services');
  if (!dd) return;
  const trigger = dd.querySelector('.nav-dropdown__trigger');
  if (!trigger) return;
  const mq = window.matchMedia('(max-width: 1024px)');

  trigger.addEventListener('click', e => {
    if (mq.matches) { e.preventDefault(); dd.classList.toggle('open'); }
  });
  // Close the (desktop click-fallback) panel when clicking outside it.
  document.addEventListener('click', e => { if (!dd.contains(e.target)) dd.classList.remove('open'); });
  // Reset accordion state when crossing the mobile/desktop boundary.
  mq.addEventListener?.('change', () => dd.classList.remove('open'));
})();

// 6. Count-up stats - numbers tick up from 0 to their target the first time the
//    stats band scrolls into view. Parses the authored text so "30+" keeps its "+".
(function() {
  const nums = document.querySelectorAll('.stat__num');
  if (!nums.length) return;

  const items = Array.from(nums).map(el => {
    const raw = el.textContent.trim();
    const m = raw.match(/^(\D*)(\d[\d,]*)(\D*)$/);   // prefix, digits, suffix
    if (!m) return null;
    return { el, raw, prefix: m[1], suffix: m[3], target: parseInt(m[2].replace(/,/g, ''), 10) };
  }).filter(Boolean);
  if (!items.length) return;

  // Respect reduced-motion: leave the authored values untouched, no animation.
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const fmt = n => n.toLocaleString('en-US');
  items.forEach(it => { it.el.textContent = it.prefix + '0' + it.suffix; });

  let done = false;
  function run() {
    if (done) return;
    done = true;
    const dur = 1600, start = performance.now();
    function frame(now) {
      const t = Math.min(1, (now - start) / dur);
      const e = 1 - Math.pow(1 - t, 3);             // easeOutCubic
      items.forEach(it => { it.el.textContent = it.prefix + fmt(Math.round(it.target * e)) + it.suffix; });
      if (t < 1) requestAnimationFrame(frame);
      else items.forEach(it => { it.el.textContent = it.raw; });  // snap to exact authored value
    }
    requestAnimationFrame(frame);
  }

  const band = document.querySelector('.stats') || items[0].el.closest('.section');
  if ('IntersectionObserver' in window && band) {
    const io = new IntersectionObserver((entries, obs) => {
      entries.forEach(en => { if (en.isIntersecting) { run(); obs.disconnect(); } });
    }, { threshold: 0.4 });
    io.observe(band);
  } else {
    run();
  }
})();

// 7. CTA contact form -> WordPress endpoint (/wp-json/olsi/v1/contact), which
//    validates the Cloudflare Turnstile token SERVER-SIDE and only then relays the
//    lead to FormSubmit (with a wp_mail backup). No recipient emails or FormSubmit
//    endpoint live in the page source, and a lead is delivered only when Cloudflare
//    confirms a real visitor. Stamps which page the lead came from, then redirects
//    to the thank-you page. On any failure it surfaces an inline error (call/WhatsApp
//    remain available above) instead of exposing a mailto with the addresses.
(function() {
  const form = document.querySelector('.cta-form');
  if (!form) return;
  const seg      = location.pathname.split('/')[1];
  const LANG     = (seg === 'en' || seg === 'ru') ? seg : 'he';
  const LP       = LANG === 'he' ? '' : '/' + LANG;   // language path prefix
  const ENDPOINT = window.OLSI_CONTACT_ENDPOINT || 'https://www.olsi.co.il/wp-json/olsi/v1/contact';
  const THANKS   = LP + '/thank-you/';
  const pageField = document.getElementById('cf-page');
  const errBox   = form.querySelector('.cta-form__err');

  const showErr = () => { if (errBox) errBox.style.display = ''; };
  const hideErr = () => { if (errBox) errBox.style.display = 'none'; };
  const resetTurnstile = () => { try { if (window.turnstile) window.turnstile.reset(); } catch (e) {} };

  // Consent checkbox is required, but its <input> is visually hidden (opacity:0), so the
  // browser's native "please check this box" bubble can't anchor to it - we validate it
  // ourselves and show a message right next to the checkbox instead.
  const consent    = form.querySelector('.cta-consent input[type="checkbox"]');
  const consentErr = form.querySelector('.cta-consent__err');
  if (consent) consent.addEventListener('change', function() {
    if (this.checked && consentErr) consentErr.style.display = 'none';
  });

  form.addEventListener('submit', function(e) {
    e.preventDefault();                     // fires only after HTML5 validation passes
    hideErr();

    // Consent gate: the privacy checkbox must be ticked before anything is sent.
    if (consent && !consent.checked) {
      if (consentErr) consentErr.style.display = '';
      try { consent.focus(); } catch (err) {}
      (consentErr || consent).scrollIntoView({ behavior: 'smooth', block: 'center' });
      return;
    }
    if (consentErr) consentErr.style.display = 'none';

    if (pageField) pageField.value = document.title + ' - ' + location.href;

    // Require a Turnstile token. If the widget loaded but hasn't resolved yet, ask the
    // visitor to try again in a moment rather than firing a request bound to be rejected.
    const tokenField = form.elements['cf-turnstile-response'];
    const token = (tokenField && tokenField.value) || '';
    if (typeof window.turnstile !== 'undefined' && !token) {
      showErr();
      return;
    }

    const btn = form.querySelector('.cta-form__submit');
    const label = btn ? btn.innerHTML : '';
    if (btn) { btn.disabled = true; btn.textContent = LANG === 'en' ? 'Sending...' : (LANG === 'ru' ? 'Отправка...' : 'שולח...'); }

    fetch(ENDPOINT, {
      method: 'POST',
      credentials: 'omit',   // send NO WordPress auth cookies -> the request is treated as anonymous,
                             // which avoids WP REST's cookie-nonce rejection for logged-in admins.
                             // Turnstile (verified server-side) is the security here, not a session.
      headers: { 'Accept': 'application/json' },
      body: new FormData(form)
    })
      .then(r => r.json().catch(() => null))
      .then(data => {
        // The endpoint returns {"success":"true"} ONLY after Turnstile passed AND the
        // lead was delivered. Anything else means nothing reached the inbox - so we must
        // NOT send the visitor to the thank-you page. Reset the widget and show the error.
        if (data && String(data.success) === 'true') {
          window.location.href = THANKS;
        } else {
          if (btn) { btn.disabled = false; btn.innerHTML = label; }
          resetTurnstile();
          showErr();
        }
      })
      .catch(() => {
        if (btn) { btn.disabled = false; btn.innerHTML = label; }
        resetTurnstile();
        showErr();
      });
  });
})();

// 8. Open links in a new tab - every link on the site EXCEPT the top menu (the
//    site header). Same-page anchors (#section) and non-navigational protocols
//    (tel:/mailto:/etc.) are skipped on purpose: opening a scroll-anchor or a
//    phone/mail link in a blank tab would just create an empty, broken tab.
//    Links that already declare their own target (e.g. the WhatsApp buttons)
//    are left untouched.
(function() {
  const header = document.querySelector('.site-header');
  document.querySelectorAll('a[href]').forEach(a => {
    if (header && header.contains(a)) return;          // top menu stays in-page
    if (a.hasAttribute('target')) return;              // respect existing target
    const href = (a.getAttribute('href') || '').trim();
    if (href === '' || href[0] === '#') return;        // same-page anchor
    if (/^(tel:|mailto:|sms:|javascript:|whatsapp:)/i.test(href)) return;
    a.target = '_blank';
    a.rel = (a.rel ? a.rel + ' ' : '') + 'noopener noreferrer';
  });
})();

// 9. Accessibility widget (תפריט נגישות). A floating button (bottom-left)
//    opens a panel of accessibility adjustments: text size,
//    high contrast, grayscale, link/heading highlight, readable font, text
//    spacing, big cursor and stop-animations. Choices persist in localStorage
//    and are re-applied on every page. The whole widget is injected here so it
//    lives on every page that loads olsi.js - no per-page markup needed.
(function() {
  var KEY = 'olsi-a11y';
  var FONT_MIN = -2, FONT_MAX = 5;            // -20% .. +50% in 10% steps
  var html = document.documentElement;

  // feature toggles: storage key -> <html> class + label + icon
  var TOGGLES = [
    { k: 'contrast',  cls: 'a11y-contrast',  label: 'ניגודיות גבוהה',
      icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 3a9 9 0 0 1 0 18z" fill="currentColor" stroke="none"/></svg>' },
    { k: 'grayscale', cls: 'a11y-grayscale', label: 'גווני אפור',
      icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" aria-hidden="true"><path d="M12 3c3.2 4 5.5 7 5.5 10A5.5 5.5 0 0 1 6.5 13c0-3 2.3-6 5.5-10z"/><path d="M12 3c3.2 4 5.5 7 5.5 10a5.5 5.5 0 0 1-5.5 5.5z" fill="currentColor" stroke="none" opacity=".4"/></svg>' },
    { k: 'links',     cls: 'a11y-links',     label: 'הדגשת קישורים',
      icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M9.5 14.5a4 4 0 0 0 5.7 0l2.3-2.3a4 4 0 1 0-5.7-5.7l-1.1 1.1"/><path d="M14.5 9.5a4 4 0 0 0-5.7 0l-2.3 2.3a4 4 0 1 0 5.7 5.7l1.1-1.1"/></svg>' },
    { k: 'headings',  cls: 'a11y-headings',  label: 'הדגשת כותרות',
      icon: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><text x="12" y="18" text-anchor="middle" font-size="18" font-weight="800" font-family="Arial,sans-serif">H</text></svg>' },
    { k: 'readable',  cls: 'a11y-readable',  label: 'גופן קריא',
      icon: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><text x="12" y="17" text-anchor="middle" font-size="13" font-weight="800" font-family="Arial,sans-serif">Aa</text></svg>' },
    { k: 'spacing',   cls: 'a11y-spacing',   label: 'ריווח שורות',
      icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 6h11M9 12h11M9 18h11"/><path d="M4 5v14M2.4 7 4 5l1.6 2M2.4 17 4 19l1.6-2"/></svg>' },
    { k: 'bigCursor', cls: 'a11y-bigcursor', label: 'סמן גדול',
      icon: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M5 3l13 6.5-5.6 1.8-1.9 5.7z"/></svg>' },
    { k: 'noMotion',  cls: 'a11y-no-motion', label: 'עצירת אנימציות',
      icon: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg>' }
  ];

  var A11Y_ICON = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2c1.1 0 2 .9 2 2s-.9 2-2 2-2-.9-2-2 .9-2 2-2zm9 7h-6v13h-2v-6h-2v6H9V9H3V7h18v2z"/></svg>';

  // ---- state ----
  function load() {
    var s = { font: 0 };
    TOGGLES.forEach(function(t) { s[t.k] = false; });
    try {
      var raw = JSON.parse(localStorage.getItem(KEY) || '{}');
      if (typeof raw.font === 'number') s.font = Math.max(FONT_MIN, Math.min(FONT_MAX, raw.font));
      TOGGLES.forEach(function(t) { if (raw[t.k]) s[t.k] = true; });
    } catch (e) {}
    return s;
  }
  var state = load();

  function fontPct() { return Math.round((1 + state.font * 0.1) * 100); }

  // apply state to the document (classes + root font-size). Called early so a
  // refresh keeps the chosen settings with minimal flash.
  function applyDoc() {
    html.style.fontSize = state.font ? (16 * (1 + state.font * 0.1)) + 'px' : '';
    TOGGLES.forEach(function(t) { html.classList.toggle(t.cls, !!state[t.k]); });
  }
  function persist() {
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {}
  }
  applyDoc();   // <-- run before the UI exists

  // ---- build the UI ----
  var stmtLink = document.querySelector('a[href*="accessibility-statement"]');
  var stmtHref = stmtLink ? stmtLink.getAttribute('href') : 'accessibility-statement.html';

  var fab = document.createElement('button');
  fab.type = 'button';
  fab.className = 'a11y-fab';
  fab.setAttribute('aria-label', 'פתיחת תפריט נגישות');
  fab.setAttribute('aria-haspopup', 'dialog');
  fab.setAttribute('aria-expanded', 'false');
  fab.setAttribute('aria-controls', 'a11y-panel');
  fab.innerHTML = A11Y_ICON;

  var panel = document.createElement('div');
  panel.className = 'a11y-panel';
  panel.id = 'a11y-panel';
  panel.setAttribute('role', 'dialog');
  panel.setAttribute('aria-modal', 'false');
  panel.setAttribute('aria-label', 'תפריט נגישות');

  var togglesHtml = TOGGLES.map(function(t) {
    return '<button type="button" class="a11y-toggle" data-a11y="' + t.k + '" aria-pressed="false">' +
             t.icon + '<span>' + t.label + '</span></button>';
  }).join('');

  panel.innerHTML =
    '<div class="a11y-panel__head">' +
      '<span class="a11y-panel__title">' + A11Y_ICON + 'תפריט נגישות</span>' +
      '<button type="button" class="a11y-close" aria-label="סגירת תפריט הנגישות">' +
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>' +
      '</button>' +
    '</div>' +
    '<div class="a11y-fontrow">' +
      '<button type="button" class="a11y-fontrow__btn" data-a11y-font="-1" aria-label="הקטנת גודל הטקסט">A<span>−</span></button>' +
      '<span class="a11y-fontrow__lvl" aria-live="polite">100%</span>' +
      '<button type="button" class="a11y-fontrow__btn" data-a11y-font="1" aria-label="הגדלת גודל הטקסט">A<span>+</span></button>' +
    '</div>' +
    '<div class="a11y-grid">' + togglesHtml + '</div>' +
    '<div class="a11y-panel__foot">' +
      '<button type="button" class="a11y-reset">' +
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 4v4h4"/></svg>' +
        'איפוס הגדרות נגישות</button>' +
      '<a class="a11y-statement" href="' + stmtHref + '">להצהרת הנגישות המלאה</a>' +
    '</div>';

  document.body.appendChild(panel);
  document.body.appendChild(fab);

  var lvlEl = panel.querySelector('.a11y-fontrow__lvl');

  // reflect current state in the controls
  function syncUI() {
    lvlEl.textContent = fontPct() + '%';
    TOGGLES.forEach(function(t) {
      var btn = panel.querySelector('[data-a11y="' + t.k + '"]');
      if (btn) btn.setAttribute('aria-pressed', state[t.k] ? 'true' : 'false');
    });
  }
  syncUI();

  // ---- open / close ----
  var isOpen = false;
  function open() {
    isOpen = true;
    panel.classList.add('open');
    fab.setAttribute('aria-expanded', 'true');
    var first = panel.querySelector('.a11y-fontrow__btn');
    if (first) first.focus();
  }
  function close(returnFocus) {
    isOpen = false;
    panel.classList.remove('open');
    fab.setAttribute('aria-expanded', 'false');
    if (returnFocus) fab.focus();
  }
  fab.addEventListener('click', function() { isOpen ? close(true) : open(); });
  panel.querySelector('.a11y-close').addEventListener('click', function() { close(true); });
  document.addEventListener('keydown', function(e) { if (e.key === 'Escape' && isOpen) close(true); });
  document.addEventListener('click', function(e) {
    if (isOpen && !panel.contains(e.target) && !fab.contains(e.target)) close(false);
  });

  // ---- controls ----
  panel.querySelectorAll('[data-a11y-font]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var step = parseInt(btn.getAttribute('data-a11y-font'), 10);
      state.font = Math.max(FONT_MIN, Math.min(FONT_MAX, state.font + step));
      applyDoc(); persist(); syncUI();
    });
  });
  panel.querySelectorAll('[data-a11y]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var k = btn.getAttribute('data-a11y');
      state[k] = !state[k];
      applyDoc(); persist(); syncUI();
    });
  });
  panel.querySelector('.a11y-reset').addEventListener('click', function() {
    state = { font: 0 };
    TOGGLES.forEach(function(t) { state[t.k] = false; });
    applyDoc(); persist(); syncUI();
  });
})();
