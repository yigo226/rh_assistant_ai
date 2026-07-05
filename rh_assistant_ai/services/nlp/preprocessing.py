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


# services/
# │
# ├── ai/
# │   ├── __init__.py
# │   ├── analyseur.py          # Point d'entrée principal
# │   ├── preprocessing.py      # Nettoyage et segmentation
# │   ├── embedding.py          # SentenceTransformer
# │   ├── esco_service.py       # Chargement des compétences ESCO
# │   ├── vector_index.py       # Construction et recherche FAISS
# │   ├── normalizer.py         # Déduplication / normalisation
# │   └── gliner_service.py     # Diplômes, métiers...
# │
# ├── cv_service.py
# ├── offre_service.py
# └── ...