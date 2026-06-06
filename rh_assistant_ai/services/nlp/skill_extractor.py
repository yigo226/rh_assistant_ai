"""
Extraction des compétences.

Méthode :
- Recherche dans un dictionnaire de compétences.
"""

import json
from pathlib import Path


BASE_DIR = Path(__file__).parent
SKILLS_FILE = BASE_DIR / "data" / "skills.json"


def load_skills():
    """
    Charge le dictionnaire des compétences.
    """

    with open(SKILLS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def extract_skills(text: str):
    """
    Extrait les compétences présentes dans le CV.

    Args:
        text (str)

    Returns:
        list
    """

    skills_database = load_skills()

    found_skills = []

    text = text.lower()

    for skill in skills_database:

        if skill.lower() in text:
            found_skills.append(skill)

    return sorted(list(set(found_skills)))