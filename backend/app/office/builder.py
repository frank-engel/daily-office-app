"""
Assemble the ordered block list for a complete Morning or Evening Prayer service
(BCP 1979, Rite II).

Each block is a plain dict with a 'type' key.  Psalm and lesson blocks carry only
their references at this stage; the API layer expands them to full verse text.
"""
from datetime import date

from app.calendar.liturgical_year import liturgical_context, MONTH_ABBREVS
from app.collects.resolver import resolve_collect
from app.lectionary.loader import HOLY_DAY_INDEX
from app.lectionary.resolver import resolve_office
from app.office.canticle_resolver import resolve_canticles
from app.office.loader import CANTICLES, FIXED_TEXTS, OPENING_SENTENCES


# ── Text normalisation ────────────────────────────────────────────────────────

def _text(val) -> str:
    """Return val as a plain string; joins list entries with newlines."""
    if isinstance(val, list):
        return "\n".join(str(v) for v in val)
    return val or ""


# ── Feast detection ───────────────────────────────────────────────────────────

def _is_major_feast(d: date, lit_ctx: dict) -> bool:
    """True for principal feasts: fixed-calendar holy days plus Easter Sunday."""
    month_day = f"{MONTH_ABBREVS[d.month]} {d.day}"
    if month_day in HOLY_DAY_INDEX:
        return True
    season = lit_ctx.get("season", "")
    week = lit_ctx.get("week", "")
    day = lit_ctx.get("day", "")
    if season == "Easter" and day == "Sunday" and week == "Easter Week":
        return True
    return False


# ── Opening sentence selection ────────────────────────────────────────────────

# Map liturgical_context season/week values to opening_sentences.json keys.
# "Pentecost" season covers Trinity Sunday plus the Season after Pentecost —
# both lack a dedicated BCP opening sentence, so fall back to "At any Time".
def _opening_sentence_key(lit_ctx: dict) -> str:
    season = lit_ctx.get("season", "")
    week = lit_ctx.get("week", "")
    title = lit_ctx.get("title") or ""

    if season == "Lent":
        return "Holy Week" if week == "Holy Week" else "Lent"
    if season == "Pentecost":
        if "Trinity" in title or (week == "" and lit_ctx.get("day") == "Sunday"):
            return "Trinity Sunday"
        return "At any Time"
    # Seasons that map directly: Advent, Christmas, Epiphany, Easter
    return season if season in OPENING_SENTENCES else "At any Time"


def _opening_sentence(lit_ctx: dict) -> dict | None:
    key = _opening_sentence_key(lit_ctx)
    bucket = OPENING_SENTENCES.get(key) or OPENING_SENTENCES.get("At any Time")
    if not bucket:
        return None
    sentences = bucket.get("sentences", [])
    return sentences[0] if sentences else None


# ── Weekday morning collect key ───────────────────────────────────────────────

# BCP 1979 pp. 98-99: one fixed collect per day of the week for Morning Prayer.
_MORNING_COLLECT_BY_DOW = {
    0: "collect_for_renewal_of_life",  # Monday
    1: "collect_for_peace",            # Tuesday
    2: "collect_for_grace",            # Wednesday
    3: "collect_for_guidance",         # Thursday
    4: "collect_for_fridays",          # Friday
    5: "collect_for_saturdays",        # Saturday
    6: "collect_for_sundays_morning",  # Sunday
}


# ── Canticle block helper ─────────────────────────────────────────────────────

def _canticle_block(canticle_id: int | str, label: str | None = None) -> dict:
    data = CANTICLES.get(str(canticle_id), {})
    return {
        "type": "canticle",
        "label": label,
        "number": str(canticle_id),
        "name": data.get("name", f"Canticle {canticle_id}"),
        "aka": data.get("aka"),
        "source": data.get("source"),
        "lines": data.get("lines", []),
        "gloria": data.get("gloria", False),
        "bcp_page": data.get("bcp_page"),
        "instruction": data.get("instruction"),
    }


# ── Main builder ──────────────────────────────────────────────────────────────

def build_office(d: date, time_of_day: str, suffrages_form: str = "A") -> list[dict]:
    """
    Return ordered blocks for a full Morning or Evening Prayer service.

    Psalm and lesson blocks have type 'psalm_ref' / 'lesson_ref' and carry only
    references; call _expand_blocks() in the API layer to hydrate verse text.

    suffrages_form: "A" or "B"
    """
    lit_ctx = liturgical_context(d) or {}
    season = lit_ctx.get("season", "")
    week = lit_ctx.get("week", "")
    is_lent = season == "Lent"
    is_easter_week = week == "Easter Week"
    is_feast = _is_major_feast(d, lit_ctx)

    office_data = resolve_office(d)
    collect_raw = resolve_collect(d, lit_ctx)
    canticle_ids = resolve_canticles(d, time_of_day, lit_ctx, is_feast)

    blocks: list[dict] = []

    # ── Service heading ───────────────────────────────────────────────────────
    service_name = "Morning Prayer" if time_of_day == "morning" else "Evening Prayer"
    blocks.append({"type": "heading", "level": 1, "text": service_name})
    blocks.append({"type": "rubric", "text": "Rite II"})

    # ── Opening sentence ──────────────────────────────────────────────────────
    sentence = _opening_sentence(lit_ctx)
    if sentence:
        blocks.append({
            "type": "sentence",
            "label": "Opening Sentence",
            "reference": sentence.get("reference", ""),
            "text": _text(sentence.get("text", "")),
        })

    # ── Confession of Sin ─────────────────────────────────────────────────────
    confession = FIXED_TEXTS.get("confession_of_sin", {})
    blocks.append({
        "type": "confession",
        "label": "Confession of Sin",
        "rubric": _text(confession.get("rubric", "")),
        "invitation": _text(confession.get("invitation", "")),
        "rubric_2": _text(confession.get("rubric_2", "")),
        "confession": _text(confession.get("confession", "")),
        "rubric_3": _text(confession.get("rubric_3", "")),
        "absolution": _text(confession.get("absolution", "")),
        "bcp_page": confession.get("bcp_page"),
    })

    # ── Opening versicles (preces) ────────────────────────────────────────────
    if time_of_day == "morning":
        opening_v = FIXED_TEXTS.get("opening_versicle_morning", {})
    else:
        opening_v = FIXED_TEXTS.get("opening_versicle_evening", {})

    gloria = FIXED_TEXTS.get("gloria_patri", {})

    preces_pairs = [
        {"leader": opening_v.get("leader", ""), "response": opening_v.get("response", "")},
        {"leader": gloria.get("leader", ""),    "response": gloria.get("response", "")},
    ]
    if not is_lent:
        alleluia_key = "alleluia_versicle" if time_of_day == "morning" else "alleluia_evening"
        al = FIXED_TEXTS.get(alleluia_key, {})
        preces_pairs.append({
            "leader": al.get("leader", "Praise to the Lord!"),
            "response": al.get("response", "The Lord's Name be praised."),
        })

    blocks.append({"type": "versicle", "pairs": preces_pairs})

    # ── Invitatory — Morning Prayer only ─────────────────────────────────────
    if time_of_day == "morning":
        if is_easter_week:
            inv_data = CANTICLES.get("easter_anthems", {})
            inv_key = "easter_anthems"
        else:
            inv_data = CANTICLES.get("venite", {})
            inv_key = "venite"
        blocks.append({
            "type": "canticle",
            "label": "Invitatory",
            "number": inv_key,
            "name": inv_data.get("name", "Venite"),
            "aka": inv_data.get("aka"),
            "source": inv_data.get("source"),
            "lines": inv_data.get("lines", []),
            "gloria": inv_data.get("gloria", False),
            "bcp_page": inv_data.get("bcp_page"),
            "instruction": inv_data.get("instruction"),
        })

    # ── Psalms ────────────────────────────────────────────────────────────────
    psalm_count = len(office_data["psalms"].get(time_of_day, [])) if office_data else 0
    blocks.append({"type": "heading", "level": 2,
                   "text": "The Psalm" + ("s" if psalm_count != 1 else "")})
    if office_data:
        for token in office_data["psalms"].get(time_of_day, []):
            blocks.append({"type": "psalm_ref", "token": token})
    else:
        blocks.append({"type": "rubric", "text": "No psalm appointed for this day."})

    # ── Lessons and canticles ─────────────────────────────────────────────────
    if office_data:
        lessons_raw = office_data[f"{time_of_day}_lessons"]
        lesson_refs = [
            (k, lessons_raw[k])
            for k in ("first", "second", "gospel")
            if lessons_raw.get(k)
        ]

        after_ot_id = canticle_ids["after_ot"]
        after_nt_id = canticle_ids["after_nt"]

        for idx, (pos_key, ref) in enumerate(lesson_refs[:2]):
            blocks.append({"type": "heading", "level": 2,
                           "text": "The First Lesson" if idx == 0 else "The Second Lesson"})
            blocks.append({"type": "lesson_ref", "position": pos_key, "reference": ref})
            blocks.append({"type": "rubric", "text": "The Word of the Lord."})

            canticle_id = after_ot_id if idx == 0 else after_nt_id
            blocks.append(_canticle_block(canticle_id))

    # ── Apostles' Creed ───────────────────────────────────────────────────────
    creed = FIXED_TEXTS.get("apostles_creed", {})
    blocks.append({
        "type": "text",
        "label": "The Apostles' Creed",
        "rubric": _text(creed.get("rubric", "Officiant and People together, all standing")),
        "text": _text(creed.get("text", "")),
        "bcp_page": creed.get("bcp_page"),
    })

    # ── The Prayers ───────────────────────────────────────────────────────────
    blocks.append({"type": "heading", "level": 2, "text": "The Prayers"})

    lbwy = FIXED_TEXTS.get("lords_be_with_you", {})
    blocks.append({
        "type": "versicle",
        "pairs": [
            {"leader": lbwy.get("leader", "The Lord be with you."),
             "response": lbwy.get("response", "And also with you.")},
            {"leader": "Let us pray.", "response": None},
        ],
    })

    lp = FIXED_TEXTS.get("lords_prayer", {})
    blocks.append({
        "type": "text",
        "label": "The Lord's Prayer",
        "rubric": _text(lp.get("rubric", "")),
        "intro": _text(lp.get("intro", "")),
        "rubric_2": _text(lp.get("rubric_2", "")),
        "text": _text(lp.get("text", "")),
        "bcp_page": lp.get("bcp_page"),
    })

    suf_key = f"suffrages_{suffrages_form.lower()}"
    suf = FIXED_TEXTS.get(suf_key, {})
    blocks.append({
        "type": "suffrages",
        "form": suffrages_form,
        "label": suf.get("label", f"Suffrages {suffrages_form}"),
        "rubric": suf.get("rubric", ""),
        "pairs": suf.get("pairs", []),
        "bcp_page": suf.get("bcp_page"),
    })

    # Collect of the Day
    if collect_raw:
        blocks.append({
            "type": "collect",
            "label": "The Collect of the Day",
            "contemporary": _text(collect_raw.get("contemporary", "")),
            "traditional": _text(collect_raw.get("traditional", "")) or None,
            "preface": collect_raw.get("preface"),
        })

    # Standing collect for the day (day-specific for morning; evening collect if present)
    if time_of_day == "morning":
        extra_key = _MORNING_COLLECT_BY_DOW.get(d.weekday(), "collect_for_renewal_of_life")
    else:
        extra_key = "collect_for_evening"
    extra = FIXED_TEXTS.get(extra_key)
    if extra:
        blocks.append({
            "type": "collect",
            "label": extra.get("label", ""),
            "contemporary": _text(extra.get("text", "")),
            "traditional": None,
            "bcp_page": extra.get("bcp_page"),
        })

    # Prayer for Mission — use grace/guidance collects as available; silently skip if absent
    mission_key = "collect_for_grace" if time_of_day == "morning" else None
    mission = FIXED_TEXTS.get(mission_key) if mission_key else None
    if mission:
        blocks.append({
            "type": "collect",
            "label": mission.get("label", "A Prayer for Mission"),
            "contemporary": _text(mission.get("text", "")),
            "traditional": None,
            "bcp_page": mission.get("bcp_page"),
        })

    # General Thanksgiving
    thanks = FIXED_TEXTS.get("general_thanksgiving", {})
    blocks.append({
        "type": "text",
        "label": thanks.get("label", "The General Thanksgiving"),
        "rubric": _text(thanks.get("rubric", "Officiant and People")),
        "text": _text(thanks.get("text", "")),
        "bcp_page": thanks.get("bcp_page"),
    })

    # Prayer of St. Chrysostom
    chrys = FIXED_TEXTS.get("prayer_of_chrysostom", {})
    blocks.append({
        "type": "text",
        "label": chrys.get("label", "A Prayer of St. Chrysostom"),
        "rubric": "",
        "text": _text(chrys.get("text", "")),
        "bcp_page": chrys.get("bcp_page"),
    })

    # Evening only: Phos Hilaron (optional evening hymn)
    if time_of_day == "evening":
        phos = FIXED_TEXTS.get("phos_hilaron", {})
        blocks.append({
            "type": "canticle",
            "label": "An Evening Hymn",
            "number": "phos_hilaron",
            "name": phos.get("name", "O Gracious Light"),
            "aka": phos.get("aka"),
            "source": None,
            "lines": phos.get("lines", []),
            "gloria": False,
            "bcp_page": phos.get("bcp_page"),
            "instruction": phos.get("rubric"),
        })

    # Closing versicle
    closing = FIXED_TEXTS.get("closing", {})
    blocks.append({
        "type": "versicle",
        "pairs": [
            {"leader": closing.get("leader", "Let us bless the Lord."),
             "response": closing.get("response", "Thanks be to God.")},
        ],
    })

    # Grace / benediction
    grace = FIXED_TEXTS.get("grace", {})
    blocks.append({
        "type": "text",
        "label": "",
        "rubric": "",
        "text": _text(grace.get("text", "")),
        "bcp_page": grace.get("bcp_page"),
    })

    return blocks
