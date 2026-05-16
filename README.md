# 🏆 ליגת פנטזי WSOP 2026 — Dashboard

דשבורד חי לליגת הפנטזי הישראלית של ה-WSOP 2026, עם רענון אוטומטי כל שעה דרך GitHub Actions.

🔗 **כתובת הדשבורד (אחרי הפריסה):** https://royecr.github.io/wsop-fantasy-2026/

## ✨ מה זה כולל?

- **230 שחקנים** מאוחדים מ-Perplexity + ChatGPT + טבלת המאסטר, עם PVS, Value Index, Captain Score, ו-12 מטריקות נוספות
- **עורך נבחרת חכם** עם אכיפת חוקים: תקציב $200M, מינ/מקס לפי קטגוריה, קפטן/טריפל-קפטן, 4 ספסל
- **שיטת ניקוד רשמית** מוטמעת (4 טבלאות: עד $9,999, מעל $10K עם 6 מדרגות, Main Event, $25K HU)
- **רענון אוטומטי** כל שעה דרך GitHub Actions — שואב מ-WSOP.com, PokerNews, Hendon Mob
- **גרפים מקיפים** — PVS vs מחיר, השוואת מודלים, היסטוגרמת ציונים, ערך לפי קטגוריה
- **Monte Carlo simulation** של 250 ריצות לחיזוי נקודות עתידיות
- **עיצוב WSOP קלאסי** — זהב/שחור/אדום, RTL מלא

## 📁 מבנה הפרויקט

```
.
├── index.html                       # הדשבורד (HTML עצמאי)
├── data/
│   ├── players.json                 # 230 שחקנים (סטטי)
│   ├── live_results.json            # מתעדכן אוטומטית כל שעה
│   └── last_update.json             # metadata של הסקרייפ האחרון
├── scrapers/
│   ├── wsop_scraper.py              # שואב מ-WSOP.com
│   ├── pokernews_scraper.py         # שואב מ-PokerNews
│   ├── name_matcher.py              # התאמת שמות עברית↔אנגלית
│   ├── compute_points.py            # מחשב נקודות לפי השיטה הרשמית
│   └── build_live_results.py        # מצרף הכל ל-live_results.json
├── .github/workflows/
│   └── scrape.yml                   # cron כל שעה + manual trigger
├── requirements.txt
├── README.md                        # קובץ זה
└── DEPLOY.md                        # מדריך פריסה (3 לחיצות)
```

## 🚀 פריסה ראשונית

ראה **[DEPLOY.md](DEPLOY.md)** למדריך 3 לחיצות מלא.

## ⚡ רענון מיידי (force refresh)

הסקרייפר רץ אוטומטית בכל שעה עגולה. לרענון מיידי:
1. לך ל-`Actions` בריפו
2. בחר `WSOP Live Scrape`
3. לחץ `Run workflow` → `Run workflow`
4. המתן 30-90 שניות
5. רענן את הדשבורד

## 🔧 שינוי תדירות הסקרייפ

ערוך את `.github/workflows/scrape.yml`:
```yaml
schedule:
  - cron: '0 * * * *'   # כל שעה (ברירת מחדל)
  # - cron: '*/30 * * * *' # כל 30 דקות
  # - cron: '0 */2 * * *'  # כל שעתיים
```

## 🐛 פתרון תקלות

**הדשבורד לא נטען נתונים חיים:**
- וודא ש-GitHub Pages פעיל (Settings → Pages → Source: main / root)
- בדוק שהקובץ `data/live_results.json` קיים בריפו
- פתח Console בדפדפן (F12) ובדוק שגיאות fetch

**ה-Action נכשל:**
- לך ל-Actions tab → לחץ על ה-run האחרון → קרא את הלוג
- אם WSOP.com שינו את ה-HTML, ה-scrapers צריכים עדכון
- אפשר תמיד לערוך את `scrapers/wsop_scraper.py` ולעשות push

**שמות שחקנים לא מותאמים:**
- בדוק את `scrapers/name_matcher.py`
- אפשר להוסיף מיפויים ידניים

## 📜 חוקי הליגה (תזכורת)

- תקציב $200M לעד 15 שחקנים בהרכב
- 4 שחקני ספסל (לא בתקציב, פעולה אחת לכל אחד למשך שבוע)
- מינ' 1 מקס' 5 שחקנים מכל קטגוריה (ישראלים עד 4)
- קפטן: ×2 נקודות
- טריפל קפטן: ×3 לשבוע אחד בלבד בעונה
- 4 חלונות חילופים בעונה, 48 שעות בין חילופים
- רק טורנירי WSOP לייב עם צמיד נכללים

## 🛠 פיתוח מקומי

```bash
git clone https://github.com/royecr/wsop-fantasy-2026.git
cd wsop-fantasy-2026
pip install -r requirements.txt
cd scrapers
python build_live_results.py     # מריץ סקרייפ מקומית
cd ..
python -m http.server 8000        # פותח את הדשבורד
# פתח http://localhost:8000 בדפדפן
```

## 📄 רישיון

לשימוש אישי ולקבוצת הליגה. ה-data נשאב מאתרים ציבוריים בכבוד (rate-limited, robots-friendly).

---

נבנה ע"י קלוד — עוזר AI של Anthropic — בעבודה משותפת עם Roye.
