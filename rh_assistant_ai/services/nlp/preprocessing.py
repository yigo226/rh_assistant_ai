"""
Prétraitement NLP

Responsabilités :
- Nettoyage du texte
- Suppression des caractères inutiles
- Normalisation
- Préparation pour les extracteurs
"""

import re


def clean_text(text: str) -> str:
    """
    Nettoie le texte brut extrait du CV.

    Args:
        text (str): texte brut

    Returns:
        str: texte nettoyé
    """

    # Suppression des retours multiples
    text = re.sub(r"\n+", "\n", text)

    # Suppression des espaces multiples
    text = re.sub(r"\s+", " ", text)

    # Suppression caractères spéciaux inutiles
    text = re.sub(r"[•▪►■]", " ", text)

    return text.strip()


def normalize_text(text: str) -> str:
    #Met le texte en minuscules
    return text.lower()