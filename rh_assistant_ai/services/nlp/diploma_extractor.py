"""
Extraction des diplômes.
"""

import json
from pathlib import Path


BASE_DIR = Path(__file__).parent
DIPLOMAS_FILE = BASE_DIR / "data" / "diplomas.json"


def load_diplomas():
    with open(DIPLOMAS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def extract_diplomas(text: str):

    diplomas = load_diplomas()

    text = text.lower()

    found = []

    for diploma in diplomas:

        if diploma.lower() in text:
            found.append(diploma)

    return sorted(list(set(found)))