# GET /api/office/{date}

Return the complete BCP 1979 Daily Office lectionary for a given calendar date,
including psalm assignments, full verse text for all lessons, and the Collect of the Day.

## Request

```
GET /api/office/{date}
```

### Path parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `date` | string | Yes | Calendar date in `YYYY-MM-DD` format |

### Examples

```
GET /api/office/2026-05-24
GET /api/office/2024-12-01
GET /api/office/2026-04-05
```

## Response

HTTP 200 with an `OfficeResponse` object.

### Response schema

```json
{
  "date": "2026-05-24",
  "title": "The Seventh Sunday of Easter",
  "season": "Easter",
  "week": "Week of 7 Easter",
  "cycle": 2,
  "collect": {
    "title": "Seventh Sunday of Easter",
    "preface": "Preface of the Ascension",
    "traditional": "O God, the King of glory...",
    "contemporary": "O God, the King of glory..."
  },
  "psalms": {
    "morning": [
      {
        "psalm": 24,
        "verses": [
          { "psalm": 24, "verse": 1, "text": "The earth is the Lord's, and the fulness thereof..." }
        ]
      }
    ],
    "evening": [ "..." ]
  },
  "morning_lessons": {
    "first": {
      "reference": "Ezek 39:21–29",
      "verses": [
        { "book": "Ezek", "chapter": 39, "verse": 21, "text": "..." }
      ]
    },
    "second": { "reference": "Rev 22:1–9", "verses": [ "..." ] },
    "gospel": { "reference": "Luke 9:18–27", "verses": [ "..." ] }
  },
  "evening_lessons": {
    "first": { "reference": "Ezek 47:1–12", "verses": [ "..." ] },
    "second": { "reference": "John 14:1–14", "verses": [ "..." ] }
  },
  "reflection": null
}
```

### Fields

| Field | Type | Description |
|---|---|---|
| `date` | string | ISO 8601 date |
| `title` | string \| null | Feast or Sunday name, if applicable |
| `season` | string | Liturgical season (e.g. `"Easter"`, `"Advent"`, `"Epiphany"`) |
| `week` | string | Week name as used in the lectionary JSON |
| `cycle` | integer | Year cycle: `1` (Year One) or `2` (Year Two) |
| `collect` | object \| null | Collect of the Day — `title`, `preface`, `traditional`, `contemporary` |
| `psalms.morning` | array | Morning psalm entries, each with `psalm` number and `verses` |
| `psalms.evening` | array | Evening psalm entries |
| `morning_lessons` | object | Morning lesson slots: `first`, `second`, `gospel` (gospel not always present) |
| `evening_lessons` | object | Evening lesson slots: `first`, `second` |
| `reflection` | null | Reserved for future AI reflection feature |

Each lesson entry:

| Field | Type | Description |
|---|---|---|
| `reference` | string \| null | Raw lectionary reference string |
| `verses` | array | Verse objects: `book`, `chapter`, `verse`, `text` |

## Error responses

| Status | Condition |
|---|---|
| 404 | No lectionary entry for this date. This is expected for Season-after-Pentecost weekdays that have no assigned readings in the BCP cycle. |
| 422 | Date is not in `YYYY-MM-DD` format |

## Notes

### Holy day interrupt

Fixed-calendar feasts (e.g. St. Andrew on Nov 30, St. Thomas on Dec 21) take precedence
over the ordinary weekday lectionary when they coincide. Principal Feasts (Easter Week,
Pentecost, Trinity Sunday, Holy Week) are never displaced by a fixed feast.

### Lectionary year cycle

The BCP 1979 Daily Office lectionary runs on a two-year cycle:

- **Year One** — begins the First Sunday of Advent preceding an odd calendar year
- **Year Two** — begins the First Sunday of Advent preceding an even calendar year

### Psalm assignments

Some dates have multiple psalms for a single office. Each is returned as a separate entry
in the array (not concatenated). Saturday psalm overrides in the Christmas season (the
`notes` field for Dec 29) are applied automatically.

### Lesson slots

Most days have `first` and `second` lessons; Sundays typically also have a `gospel` lesson.
The lesson keys match the raw lectionary data — do not assume all three are always present.

### Apocryphal readings

The BCP 1979 lectionary assigns Deuterocanonical readings on many weekdays and some
Sundays. These are fully supported: Sirach, Wisdom, Tobit, Judith, Baruch, 1–2 Maccabees,
and 1–2 Esdras all resolve to verse text.
