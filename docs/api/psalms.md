# GET /api/psalms/{numbers}

Return the full text of one or more psalms by number.

## Request

```
GET /api/psalms/{numbers}
```

### Path parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `numbers` | string | Yes | Single psalm number, or comma-separated list |

### Examples

```
GET /api/psalms/23
GET /api/psalms/146,147
GET /api/psalms/111,112,113
```

## Response

HTTP 200 with a dict keyed by psalm number string, each value a `PsalmEntry` object.

### Response schema

```json
{
  "23": {
    "psalm": 23,
    "verses": [
      { "psalm": 23, "verse": 1, "text": "The Lord is my shepherd; I shall not want." },
      { "psalm": 23, "verse": 2, "text": "He maketh me to lie down in green pastures..." }
    ]
  }
}
```

For multiple psalms:

```json
{
  "146": { "psalm": 146, "verses": [ ... ] },
  "147": { "psalm": 147, "verses": [ ... ] }
}
```

### Fields

The response is a `dict[str, PsalmEntry]` where each key is the psalm number as a string.

Each `PsalmEntry`:

| Field | Type | Description |
|---|---|---|
| `psalm` | integer | Psalm number (1–150) |
| `verses` | array | Ordered list of verse objects |

Each verse object:

| Field | Type | Description |
|---|---|---|
| `psalm` | integer | Psalm number (repeated for convenience) |
| `verse` | integer | Verse number |
| `text` | string | Verse text (KJVA) |

## Error responses

| Status | Condition |
|---|---|
| 422 | No numbers provided, or a non-integer value in the list |

## Notes

Psalm text is returned in canonical verse order. Verses are never merged or split —
each DB verse is one entry. The header verse ("A Psalm of David") is verse 0 in
some traditions; this database follows the canonical numbering where verse 1 is the
first text verse.

Use this endpoint to pre-fetch multiple psalms in a single request — preferred over
calling `/api/office/{date}` solely for psalm text when you already know the numbers.
