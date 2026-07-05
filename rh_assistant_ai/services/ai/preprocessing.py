"""
Prétraitement NLP (Étape 1 de l'architecture modulaire V2.1.0)
Responsabilités :
- Nettoyage et normalisation du texte brut (CV ou Offre)
- Segmentation intelligente des phrases via spaCy (sans casser les termes comme Node.js)
"""

import re
import unicodedata
import spacy

# L'instance reste à None au démarrage pour respecter le Lazy Loading validé par le prof
_nlp_segmenter_instance = None

def _get_segmenter():
    """Charge le modèle de base français uniquement pour le découpage des phrases (très rapide)."""
    global _nlp_segmenter_instance
    if _nlp_segmenter_instance is None:
        # On désactive les composants lourds (ner, parser complet) pour ne garder que la segmentation
        _nlp_segmenter_instance = spacy.load("fr_core_news_lg", disable=["ner", "textcat"])
        # On s'assure que le découpeur de phrases (senter) est bien actif
        if not _nlp_segmenter_instance.has_pipe("senter"):
            _nlp_segmenter_instance.add_pipe("senter")
    return _nlp_segmenter_instance


def clean_text(text: str) -> str:
    """
    Nettoie le texte extrait d'un CV ou d'une offre (Conserve la casse et les accents).
    """
    if not text:
        return ""

    # Uniformiser les sauts de ligne
    text = re.sub(r"\r\n?", "\n", text)

    # Remplacer les puces de listes courantes dans les CV par des espaces
    text = re.sub(r"[•▪►■●◦]", " ", text)

    # Nettoyage des espaces et tabulations multiples
    text = re.sub(r"[ \t]+", " ", text)

    # Réduction des lignes vides consécutives
    text = re.sub(r"\n{2,}", "\n", text)

    return text.strip()


def normalize_text(text: str) -> str:
    """
    Normalise le texte pour les comparaisons sémantiques strictes (Minuscules et sans accents).
    """
    if not text:
        return ""

    text = text.lower()

    # Suppression des accents via la décomposition Unicode
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))

    # Suppression des espaces multiples restants
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def split_sentences_spacy(text: str) -> list[str]:
    """
    Découpe le texte en phrases de manière intelligente via l'IA de spaCy.
    Protège les expressions contenant des points comme 'Node.js' ou 'Bac+5'.
    """
    if not text or not text.strip():
        return []

    # Premier nettoyage rapide du texte
    texte_propre = clean_text(text)
    
    nlp = _get_segmenter()
    doc = nlp(texte_propre)
    
    # On extrait chaque phrase détectée par le réseau de neurones
    phrases = [str(sent).strip() for sent in doc.sents if str(sent).strip()]
    return phrases
