# olsi.co.il - ביקורת ובניית מפת אתר (2026-06-30)

## תוצרים
- **מפת אתר XML נקייה**: `olsi/sitemap.xml` (37 URLים קנוניים, lastmod אמיתי מ-Yoast, priority/changefreq).
- **מפת אתר טקסט חיה (שיתוף)**: https://www.olsi.co.il/wp-content/uploads/2026/06/olsi-sitemap.txt
  (Media Library ID 3918; פורמט טקסט כי וורדפרס חוסם העלאת XML ל-Media Library).

## הסט הקנוני (37 URL, כולם מחזירים 200)
- בית: `/`
- 10 שירותים: software-development, app-development, crm-development, excel-upgrade, access-upgrade, inventory-system, custom-systems, integrations-api, data-processing, tech-support
- בלוג (ליסטינג): professional-info
- 8 case studies: case-study-{crm, olcrm, production, gantt, curtains, sales-site, selenium, toolpro}
- 16 פוסטים: 2026-software-development, access-development-2026, access-outsource-development, access-to-sql, automation-development-case-study, business-independence, custom-business-software, data-scraping, errors-system-can-solves, gantt-chart, legacy-system-modernization, python-developer, replace-excel, software-dev-high-tech, streamlining-processes, work-day-before-after
- משפטי: privacy-policy

## ממצאי ביקורת על הסייטמאפ החי (Yoast)
1. **הסייטמאפ של Yoast מכיל כ-55 URLים שמפנים 301** (slugs עבריים ישנים + כפילויות אנגלית כמו /landing/, /blog/, /about/, /expertise/, /website-systems-development/, /complex-app-development/, /businesses-software-building11111/, וקטגוריות/תגיות). כולם מפנים נכון ליעד קנוני (לפי redirects.csv), אבל **לא אמורים להופיע בסייטמאפ** - סייטמאפ צריך רק 200.
2. **באג**: `/accessibility-statement/` מחזיר **301 ל-/privacy/** (הדף החי שבור) למרות שמקושר בפוטר ומופיע ב-page-sitemap. הוצא מהסייטמאפ הנקי עד שיתוקן.
3. קטגוריית `uncategorized` ופוסט CRM כפול (`...-2`) קיימים עדיין.

## פתרון מומלץ לסייטמאפ הרשמי (/sitemap.xml) - דורש אישור
להוציא את הדפים/פוסטים המפנים (301) מסייטמאפ Yoast ע"י noindex (Yoast מחריג noindex מהסייטמאפ אוטומטית). פעולה לא-הרסנית, לא שוברת את ההפניות. לחלופין: לתקן את דף הנגישות שיחזור 200.
