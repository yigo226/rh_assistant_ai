"""
Extraction des expériences professionnelles.

Version MVP :
- Détection du nombre d'années.
"""

import re


def extract_experience(text: str):
    """
    Recherche des expressions du type :

    - 2 ans d'expérience
    - 5 years experience

    Returns:
        list
    """

    patterns = [

        r"(\d+)\s+ans",

        r"(\d+)\s+an",

        r"(\d+)\s+years"
    ]

    experiences = []

    for pattern in patterns:

        matches = re.findall(pattern, text.lower())

        experiences.extend(matches)

    return experiences