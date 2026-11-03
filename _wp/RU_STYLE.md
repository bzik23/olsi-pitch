# OLSI Systems — Hebrew → Russian translation style guide

Authoritative reference for every Russian (`/ru/`) page of olsi.co.il. Keep
terminology and tone identical across all pages so the site reads as one
professional voice. Mirrors `EN_STYLE.md`; where the two differ, this file wins
for Russian.

## Golden rules
1. **Translate visible text only. Never alter HTML.** Keep every tag, attribute,
   class, id, SVG, `data-*`, and link target byte-for-byte. Only the human-readable
   text between tags (and `alt`, `title`, `placeholder`, `aria-label` values)
   changes. The tag count and the order of tags must be identical to the source.
2. **Do not touch links or asset paths.** Leave every `href`/`src` exactly as-is; a
   separate deterministic step rewrites internal links to the `/ru/` tree. Do not
   add, remove, or reorder any link.
3. **No dash characters. Ever.** Use a plain hyphen `-` (U+002D). NEVER use the em
   dash `—` (U+2014) or en dash `–` (U+2013), even though Russian typography
   normally prefers them. This is a locked client rule and the publisher REJECTS any
   file containing `—` or `–`.
4. **Zero Hebrew left behind.** No Hebrew characters may remain in the output
   (the publisher rejects any). Latin brand/tech names stay Latin (see below).
5. Natural, professional B2B marketing Russian - not a literal word-for-word gloss.
   Rework sentences so they read as if written by a native Russian copywriter, while
   keeping the same meaning, structure, and section order.
6. Tone: confident, warm, concrete. Address the reader as "вы / ваш бизнес / ваша
   команда" (lowercase "вы", standard for web marketing). Avoid hype and filler.
   Match the Hebrew's calm, expert register. Use "ё" where appropriate.
7. Keep numbers, years, phone numbers, prices, and proper nouns unchanged.

## Locked terms (never vary)
| Hebrew | Russian |
|---|---|
| אולסי מערכות | OLSI Systems (keep Latin; "OLSI" on second mention) |
| אורן לסמן | Oren Lassman (Latin, LOCKED) |
| בית תוכנה בוטיק | бутиковая софтверная студия |
| מאז 1995 / est. 1995 | с 1995 года / est. 1995 |
| מערכת / מערכת חכמה | система / умная система |
| מערכת מותאמת אישית | индивидуальная система / система под заказ |
| פיתוח תוכנה | разработка ПО / разработка программного обеспечения |
| פיתוח אפליקציה | разработка приложений |
| מערכת CRM / ניהול קשרי לקוחות | CRM-система / управление отношениями с клиентами |
| אפיון | требования / техническое задание (אפיון טכני = техническое задание) |
| שדרוג מאקסל | переход с Excel |
| שדרוג מאקסס | переход с Access |
| מערכת לניהול מלאים | система управления складом |
| אינטגרציות ו-API | интеграции и API |
| איסוף ועיבוד נתונים | сбор и обработка данных |
| סקרייפינג | парсинг (scraping) |
| ליווי טכני שוטף | постоянная техподдержка |
| לידים | лиды |
| מלאי | склад / остатки |
| ספקים | поставщики |
| הזמנות | заказы |
| מפעל | завод / производство |
| מלכ"ר / עמותה | некоммерческая организация / НКО |
| דוחות | отчёты |
| תהליך העבודה | то, как мы работаем / наш процесс |
| שיחת ייעוץ | консультация |
| הצעת מחיר | коммерческое предложение / смета |
| צרו קשר | Контакты |
| מידע מקצועי | Статьи (раздел блога/базы знаний) |
| פרויקטים / דוגמאות לפרויקטים | Проекты / примеры проектов |
| דף הבית | Главная |
| אודות | О нас |
| מדיניות פרטיות | Политика конфиденциальности |
| הצהרת נגישות | Заявление о доступности |

## Keep in Latin (do NOT transliterate)
Excel, Access, SQL Server, Python, CRM, API, Android, iOS, SaaS, Selenium, MES,
Gantt, OLSI Systems, Oren Lassman, WhatsApp, Waze.

## The 9-step process (use these exact labels)
1. Понимание потребностей клиента / первичная оценка
2. Техническое задание
3. Утверждение клиентом до начала разработки
4. Разработка
5. Тестирование (QA)
6. Бета-версия
7. Исправление замечаний
8. Развёртывание на продакшн
9. Запуск

## The 12 services (canonical Russian titles - match the nav)
Разработка ПО · Разработка приложений · Разработка CRM · Переход с Excel ·
Переход с Access · Управление складом · Индивидуальные системы ·
Интеграции и API · Сбор и обработка данных · Постоянная техподдержка ·
Разработка диаграммы Ганта · Разработка на Python

## Contact facts (unchanged)
Phone 09-8820511 · WhatsApp/mobile 050-553-4398 · info@olsi.co.il ·
Hadera offices, "Mul HaHof Village" (Unitowers), near the Olga interchange, Route 2.
Render the address in Russian: Хадера, комплекс "Mul HaHof Village" (башни
Unitowers), рядом с развязкой Ольга, шоссе 2 (Приморское шоссе).
