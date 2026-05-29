# Anglican Daily Office

A personal liturgical practice app and API serving the **Book of Common Prayer 1979** Daily
Office for any calendar date.

## What it provides

- **Lectionary assignments** — accurate readings and psalm numbers for every day of the
  liturgical year: Advent through Proper 29, all major feasts, and the full Easter cycle
- **Holy day interrupt** — fixed-calendar saints' days (St. Andrew, St. Stephen, etc.) take
  precedence over ordinary weekday readings per BCP rubrics; Principal Feasts always win ties
- **Bible text** — full verse text from the King James Version with Apocrypha, including all
  Deuterocanonical books required by the Anglican lectionary (Sirach, Wisdom, Tobit, etc.)
- **Collect of the Day** — traditional and contemporary forms for every season and principal feast
- **Full Office text** — complete rendered Morning and Evening Prayer with canticles, versicles,
  opening sentences, suffrages A & B, fixed prayers, and Apostles' Creed (Rite II)
- **Calendar engine** — Easter computed by the Gregorian Computus algorithm; all moveable
  feasts, Advent, and Season-after-Pentecost Propers derived from it
- **Habit log** — persistent morning/evening completion tracking with a 30-day grid

## Getting started

- [Setup and installation](setup.md)
- [API reference](api/index.md)
- [Architecture overview](architecture.md)

## Project status

| Phase | Status | Scope |
|---|---|---|
| 1 — Foundation | ✅ Complete | Easter algorithm, calendar math, project structure |
| 2 — Lectionary Engine | ✅ Complete | Liturgical calendar, loader, resolver, lectionary API |
| 3 — Bible Database | ✅ Complete | KJVA SQLite, reference parser, Bible + psalm APIs |
| 4 — Frontend | ✅ Complete | Jinja2/HTMX templates, Morning/Evening Prayer tabs |
| 5 — Habits | ✅ Complete | Habit log, CRUD API, 30-day completion grid |
| 6 — Collects | ✅ Complete | Collect of the Day, traditional/contemporary toggle |
| 7 — Android | ✅ Complete | WebView APK, `adb reverse` setup |
| 8 — Full Office Text | ✅ Complete | Canticles, versicles, suffrages, full service API |
| 9 — Polish | ✅ Complete | Holy day interrupt logic, global error pages, edge case tests |
