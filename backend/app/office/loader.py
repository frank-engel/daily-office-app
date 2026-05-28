"""Load office data files (canticles, opening sentences, fixed texts) at startup."""
import json
from pathlib import Path

_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "office"

CANTICLES: dict = {}
OPENING_SENTENCES: dict = {}
FIXED_TEXTS: dict = {}


def load_office_texts() -> None:
    CANTICLES.clear()
    OPENING_SENTENCES.clear()
    FIXED_TEXTS.clear()

    with open(_DATA_DIR / "canticles.json", encoding="utf-8") as f:
        data = json.load(f)
    CANTICLES.update({k: v for k, v in data.items() if not k.startswith("_")})

    with open(_DATA_DIR / "opening_sentences.json", encoding="utf-8") as f:
        data = json.load(f)
    OPENING_SENTENCES.update({k: v for k, v in data.items() if not k.startswith("_")})

    with open(_DATA_DIR / "fixed_texts.json", encoding="utf-8") as f:
        data = json.load(f)
    FIXED_TEXTS.update({k: v for k, v in data.items() if not k.startswith("_")})
