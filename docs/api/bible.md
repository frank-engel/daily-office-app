# GET /api/bible/{reference}

Return verse text for any BCP lectionary Bible reference string.

## Request

```
GET /api/bible/{reference}
```

The `reference` path segment is treated as a catch-all (`{reference:path}`) so slashes
and other URL-safe characters are preserved.

### Path parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `reference` | string | Yes | BCP-style Bible reference (see formats below) |

### Supported reference formats

Both ASCII hyphen (`-`) and Unicode en-dash (`–`) are accepted as range separators
and treated identically. The internal data uses en-dashes, but you never need to type one.

| Format | Example |
|---|---|
| Simple range | `Isa 1:1-9` |
| Multi-range, same chapter | `Isa 5:8-12, 18-23` |
| Semicolon-separated sections | `Gal 3:23-29; 4:4-7` |
| Letter-suffixed verse (stripped) | `2 Pet 2:1-10a` |
| Cross-chapter range | `Luke 20:41-21:4` |
| Parenthetical optional suffix | `John 17:1-11(12-26)` |
| Parenthetical optional prefix | `Isa 42:(1-9)10-17` |

Parenthetical sections are always stripped; only the non-parenthetical portion is returned.

### Book abbreviations

SBL-style abbreviations are used throughout. Common examples:

| Abbreviation | Book |
|---|---|
| `Gen`, `Exod`, `Lev`, `Num`, `Deut` | Pentateuch |
| `Isa`, `Jer`, `Ezek`, `Dan` | Major Prophets |
| `Ps` / `Pss` | Psalms |
| `Matt`, `Mark`, `Luke`, `John` | Gospels |
| `Acts`, `Rom`, `1 Cor`, `2 Cor` | NT letters |
| `Rev` | Revelation |
| `Sir` / `Ecclus` | Sirach / Ecclesiasticus |
| `Wis` | Wisdom of Solomon |
| `Tob`, `Jdt`, `Bar` | Tobit, Judith, Baruch |
| `1 Macc`, `2 Macc` | Maccabees |
| `1 Esd`, `2 Esd` | Esdras |

### Examples

```
GET /api/bible/Isa 1:1–9
GET /api/bible/Gal 3:23–29; 4:4–7
GET /api/bible/Sir 1:1–10
```

## Response

HTTP 200 with a `BibleResponse` object.

### Response schema

```json
{
  "reference": "Isa 1:1–9",
  "verses": [
    { "book": "Isa", "chapter": 1, "verse": 1, "text": "The vision of Isaiah..." },
    { "book": "Isa", "chapter": 1, "verse": 2, "text": "Hear, O heavens..." }
  ]
}
```

### Fields

| Field | Type | Description |
|---|---|---|
| `reference` | string | The reference string as requested |
| `verses` | array | Ordered list of verse objects |

Each verse object:

| Field | Type | Description |
|---|---|---|
| `book` | string | SBL abbreviation |
| `chapter` | integer | Chapter number |
| `verse` | integer | Verse number |
| `text` | string | Verse text (KJVA) |

## Error responses

| Status | Condition |
|---|---|
| 404 | Reference string could not be parsed, or no verses were found in the database |
