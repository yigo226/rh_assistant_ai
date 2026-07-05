"""
Moteur d'Embeddings Vectoriels (Étape 2 de l'architecture modulaire V2.1.0)
Responsabilités :
- Charger l'instance unique du SentenceTransformer multilingue en RAM
- Générer les coordonnées vectorielles (embeddings) des textes soumis
"""

from sentence_transformers import SentenceTransformer

# Instance globale partagée (Lazy Loading)
_model_embedding_instance = None

def _get_embedding_model():
    """ Initialise le modèle de phrase multilingue uniquement au premier besoin. """
    global _model_embedding_instance
    if _model_embedding_instance is None:
        print("🤖 [IA EMBEDDING] Chargement du modèle de phrases multilingue en RAM...")
        # Modèle ultra-puissant pour le français, gère parfaitement la proximité sémantique
        _model_embedding_instance = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")
        print("✨ [IA EMBEDDING] Modèle sémantique prêt pour la vectorisation.")
    return _model_embedding_instance


def generer_embeddings(textes: list[str]):
    """
    Transforme une liste de chaînes de caractères en une matrice de vecteurs Numpy.
    Args:
        textes (list[str]): Liste de phrases ou mots à encoder.
    Returns:
        numpy.ndarray: Matrice de coordonnées vectorielles.
    """
    if not textes:
        return None
        
    model = _get_embedding_model()
    # Le modèle encode la liste de textes et génère les vecteurs numériques
    return model.encode(textes, show_progress_bar=False)


def generer_un_embedding(texte: str):
    """
    Transforme un texte unique en son vecteur sémantique.
    """
    if not texte or not texte.strip():
        return None
        
    model = _get_embedding_model()
    return model.encode(texte, show_progress_bar=False)
