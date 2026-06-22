# -*- coding: utf-8 -*-
"""Add office address + Google map + Waze link under the footer "צרו קשר" column
across the live multi-page site (every *.html that shares assets/olsi.css).
Idempotent: skips files that already carry .footer-addr.
Handles two footer layouts:
  A) contact <ul> = tel / mailto / ישראל
  B) contact <ul> = tel / mailto / ישראל / privacy / accessibility (case studies)
Skips preview-dark-v1.html (standalone dark mockup, no shared assets)."""
import re, glob, os, urllib.parse

DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAT, LNG = "32.4414786", "34.8958675"   # מול החוף וילג' / Unitowers, חדרה

address = ('משרדי חברת אולסי מערכות בחדרה ממוקמים במתחם המסחרי והעסקים '
           '"מול החוף וילג\'" (במגדלי Unitowers), '
           'בסמוך למחלף אולגה על כביש 2 (כביש החוף).')

map_q   = urllib.parse.quote("מול החוף וילג' חדרה")
map_src = "https://maps.google.com/maps?q={}&hl=he&z=16&output=embed".format(map_q)
waze    = "https://waze.com/ul?ll={}%2C{}&navigate=yes".format(LAT, LNG)

waze_svg = ('<svg viewBox="0 0 24 24" width="16" height="16" fill="none" '
            'stroke="currentColor" stroke-width="1.9" stroke-linecap="round" '
            'stroke-linejoin="round" aria-hidden="true">'
            '<path d="M12 21s-6-5.3-6-10a6 6 0 0 1 12 0c0 4.7-6 10-6 10z"/>'
            '<circle cx="12" cy="11" r="2"/></svg>')

# Address + map + Waze. Sits as siblings of the <ul>, after the </ul>, before </div>.
FRAG = (
'      <p class="footer-addr">{addr}</p>\n'
'      <div class="footer-map">\n'
'        <iframe title="מפת המשרדים - מול החוף וילג\', חדרה" src="{src}" '
'width="100%" height="170" loading="lazy" '
'referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe>\n'
'      </div>\n'
'      <a class="footer-waze" href="{waze}" target="_blank" rel="noopener noreferrer">'
'{svg}<span>ניווט עם Waze</span></a>'
).format(addr=address, src=map_src, waze=waze, svg=waze_svg)

ISRAEL = r'\n[ \t]*<li><span class="footer-static">ישראל</span></li>'

# Layout A: ...mailto</li>  ישראל</li>  </ul></div>
patA = re.compile(ISRAEL + r'(\n[ \t]*</ul>)(\n[ \t]*</div>)')
# Layout B: ...ישראל</li>  <li>..</li> <li>..</li>  </ul></div>  (keep the extra lis)
patB = re.compile(ISRAEL + r'((?:\n[ \t]*<li>.*?</li>)+)(\n[ \t]*</ul>)(\n[ \t]*</div>)', re.S)

def fix(html):
    if 'class="footer-addr"' in html:
        return html, "already"
    new, n = patB.subn(lambda m: m.group(1) + m.group(2) + '\n' + FRAG + m.group(3), html)
    if n == 1:
        return new, "B"
    new, n = patA.subn(lambda m: m.group(1) + '\n' + FRAG + m.group(2), html)
    if n == 1:
        return new, "A"
    return html, "nomatch(%d)" % n

results = {}
for path in sorted(glob.glob(os.path.join(DIR, "*.html"))):
    name = os.path.basename(path)
    if name == "preview-dark-v1.html":
        results[name] = "skipped"; continue
    with open(path, encoding="utf-8") as f:
        html = f.read()
    new, status = fix(html)
    if status in ("A", "B"):
        with open(path, "w", encoding="utf-8") as f:
            f.write(new)
    results[name] = status

for name in sorted(results):
    print("  %-42s %s" % (name, results[name]))
print("done:", sum(s in ("A", "B") for s in results.values()), "changed,",
      sum(s == "already" for s in results.values()), "already")
