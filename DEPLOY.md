# 🚀 מדריך פריסה — 5 דקות

## שלב 1: יצירת ריפו חדש (1 דקה)

1. לך ל-https://github.com/new (כשאתה מחובר כ-**royecr**)
2. **Repository name:** `wsop-fantasy-2026`
3. **Visibility:** ✅ **Public** (חובה לתוכנית החינמית של GitHub Pages)
4. ❌ **אל תסמן** "Add a README" / "Add .gitignore" / "license" — נעלה את שלנו
5. לחץ **Create repository**

## שלב 2: העלאת הקבצים בגרירה (2-3 דקות)

1. בעמוד הריפו החדש, לחץ **uploading an existing file** (קישור באמצע העמוד)
2. גרור את **כל התוכן** של תיקיית `gh_deploy/` ישירות לאזור הגרירה:
   - `index.html`
   - `README.md`
   - `DEPLOY.md`
   - `requirements.txt`
   - תיקיית `data/` (עם 3 הקבצים שבתוכה)
   - תיקיית `scrapers/` (עם 5 קבצי Python)
   - תיקיית `.github/` (עם `workflows/scrape.yml` שבתוכה)
3. בתחתית, הוסף commit message: `Initial deployment 🚀`
4. לחץ **Commit changes**

> **🔍 חשוב:** וודא שתיקיית `.github/workflows/scrape.yml` עלתה — תיקיות מנקודה (`.github`) לפעמים מוסתרות ב-Finder/Explorer. אם לא רואה אותה ב-GitHub אחרי ההעלאה, תצטרך להעלות אותה בנפרד:
> - לחץ "Add file" → "Create new file"
> - שם הקובץ: `.github/workflows/scrape.yml` (חשוב לכתוב במלואו)
> - העתק את התוכן מהקובץ המקומי
> - Commit

## שלב 3: הפעלת GitHub Pages (30 שניות)

1. בעמוד הריפו, לחץ על **Settings** (למעלה מימין)
2. בתפריט בצד שמאל, לחץ **Pages**
3. תחת **Build and deployment**:
   - **Source:** `Deploy from a branch`
   - **Branch:** `main` / `(root)`
4. לחץ **Save**
5. המתן 1-2 דקות. ה-URL יופיע:
   **https://royecr.github.io/wsop-fantasy-2026/**

## שלב 4: בדיקת ה-Action (אופציונלי, 1 דקה)

1. לך ל-tab **Actions** בריפו
2. תראה את **WSOP Live Scrape**
3. בפעם הראשונה: לחץ **Run workflow** → **Run workflow** (כפתור ירוק)
4. המתן 30-60 שניות עד שיופיע ✓ ירוק
5. ה-Action יעדכן את `data/live_results.json` אוטומטית

## ✅ סיימת!

הדשבורד שלך חי ב:
🔗 **https://royecr.github.io/wsop-fantasy-2026/**

מעכשיו:
- 🕐 הסקרייפר רץ אוטומטית **כל שעה עגולה**
- 🔄 לחיצה על "רענן" בדשבורד טוענת את הנתונים האחרונים
- ⚡ לרענון מיידי: Actions tab → Run workflow → המתן 60 שניות → רענן

## 🆘 בעיות נפוצות

### "Page not found" אחרי שלב 3
- המתן עוד דקה — GitHub Pages לוקח לפעמים זמן לפרוס
- וודא שב-Pages settings הברנץ' הוא `main` ולא `master`

### Action נכשל בפעם הראשונה
- זה תקין אם WSOP.com עוד לא הציג טורנירים (לפני 26.5)
- ה-Action כותב JSON ריק תקין — הדשבורד יציג "אין אירועים עדיין"
- כשהאליפות תתחיל, הנתונים יזרמו אוטומטית

### לא רואים את `data/live_results.json`
- וודא שהעלאת את כל התיקיה `data/`
- שמות קבצים case-sensitive ב-GitHub Pages (`data/` ולא `Data/`)

### שינויים ל-roster/captain לא נשמרים
- הנתונים נשמרים ב-localStorage של הדפדפן (זה התקן)
- אם אתה משתמש בכמה דפדפנים/מכשירים — כל אחד צריך להגדיר בנפרד
- אופציית הגיבוי: לשונית הגדרות → "ייצא state" → שמור JSON

---

זמן כולל לפריסה: ~5 דקות. אחרי זה — לנצח. 🏆
