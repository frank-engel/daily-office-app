"""
Maps SBL-style book abbreviations (as used in the lectionary JSON) to
KJVA_books.id values in web.sqlite.

Book IDs are fixed by the KJVA.db source (scrollmapper/bible_databases).
OT: 1-39, Apocrypha: 40-53, NT: 54-80.
"""

# SBL abbrev / common variant -> KJVA book id
BOOK_MAP: dict[str, int] = {
    # Old Testament
    "Gen": 1,
    "Exod": 2,  "Exo": 2,
    "Lev": 3,
    "Num": 4,   "Numb": 4,
    "Deut": 5,  "Deu": 5,
    "Josh": 6,  "Jos": 6,
    "Judg": 7,  "Jdg": 7,
    "Ruth": 8,  "Rut": 8,
    "1 Sam": 9,  "1Sam": 9,  "1 Kgdms": 9,
    "2 Sam": 10, "2Sam": 10, "2 Kgdms": 10,
    "1 Kgs": 11, "1Kgs": 11, "1 Kings": 11,
    "2 Kgs": 12, "2Kgs": 12, "2 Kings": 12,
    "1 Chr": 13, "1Chr": 13, "1 Chron": 13,
    "2 Chr": 14, "2Chr": 14, "2 Chron": 14,
    "Ezra": 15, "Ezr": 15,
    "Neh": 16,
    "Esth": 17, "Est": 17,
    "Job": 18,
    "Ps": 19,   "Pss": 19, "Psalm": 19, "Psalms": 19,
    "Prov": 20, "Pro": 20,
    "Eccl": 21, "Qoh": 21,
    "Song": 22, "Cant": 22, "Song of Sol": 22,
    "Isa": 23,
    "Jer": 24,
    "Lam": 25,
    "Ezek": 26, "Eze": 26,
    "Dan": 27,
    "Hos": 28,
    "Joel": 29, "Joe": 29,
    "Amos": 30, "Amo": 30,
    "Obad": 31, "Oba": 31,
    "Jonah": 32, "Jon": 32,
    "Mic": 33,
    "Nah": 34,
    "Hab": 35,
    "Zeph": 36, "Zep": 36,
    "Hag": 37,
    "Zech": 38, "Zec": 38,
    "Mal": 39,
    # Apocrypha / Deuterocanonical
    "1 Esd": 40, "1Esd": 40, "1 Esdr": 40,
    "2 Esd": 41, "2Esd": 41, "2 Esdr": 41,
    "Tob": 42,
    "Jdt": 43,  "Judith": 43,
    "Add Esth": 44,
    "Wis": 45,  "Wisd": 45, "Wisdom": 45,
    "Sir": 46,  "Ecclus": 46, "Sirach": 46,
    "Bar": 47,
    "1 Macc": 52, "1Macc": 52,
    "2 Macc": 53, "2Macc": 53,
    # New Testament
    "Matt": 54, "Mat": 54,
    "Mark": 55, "Mar": 55,
    "Luke": 56, "Luk": 56,
    "John": 57, "Joh": 57,
    "Acts": 58, "Act": 58,
    "Rom": 59,
    "1 Cor": 60, "1Cor": 60,
    "2 Cor": 61, "2Cor": 61,
    "Gal": 62,
    "Eph": 63,
    "Phil": 64, "Php": 64,
    "Col": 65,
    "1 Thess": 66, "1Thess": 66,
    "2 Thess": 67, "2Thess": 67,
    "1 Tim": 68,  "1Tim": 68,
    "2 Tim": 69,  "2Tim": 69,
    "Titus": 70, "Tit": 70,
    "Phlm": 71, "Philem": 71,
    "Heb": 72,
    "Jas": 73,  "Jam": 73,
    "1 Pet": 74, "1Pet": 74,
    "2 Pet": 75, "2Pet": 75,
    "1 John": 76, "1John": 76,
    "2 John": 77, "2John": 77,
    "3 John": 78, "3John": 78,
    "Jude": 79,
    "Rev": 80,  "Apoc": 80,
}


def book_id(abbrev: str) -> int | None:
    """Return KJVA book_id for *abbrev*, or None if unknown."""
    return BOOK_MAP.get(abbrev)
