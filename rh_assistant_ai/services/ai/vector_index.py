"""
Index de Recherche Vectorielle FAISS (Étape 4 de l'architecture modulaire V2.1.0)
Responsabilités :
- Instancier l'index mathématique de Meta (FAISS)
- Effectuer la recherche géométrique par Similarité Cosinus des Top-K compétences les plus proches
"""

import os
import faiss
import numpy as np
from services.ai.esco_service import charger_competences_esco, charger_ou_creer_embeddings_esco
from services.ai.embedding import generer_un_embedding

INDEX_PATH = "./nlp/data/esco/faiss.index"
_index_faiss_instance = None

def _initialiser_index_vectoriel():
    """ Construit ou charge l'index de recherche rapide FAISS en RAM. """
    global _index_faiss_instance
    if _index_faiss_instance is not None:
        return _index_faiss_instance

    # Récupération des données calculées
    vecteurs = charger_ou_creer_embeddings_esco()
    
    if vecteurs is None:
        return None

    dimension = vecteurs.shape[1]  # Dimension du modèle mpnet (généralement 768)

    if os.path.exists(INDEX_PATH):
        print("🔍 [VECTOR INDEX] Chargement de l'index géométrique FAISS pré-construit...")
        _index_faiss_instance = faiss.read_index(INDEX_PATH)
    else:
        print("🔨 [VECTOR INDEX] Construction de la structure de recherche spatiale FAISS...")
        # IndexFlatIP calcule le produit scalaire (équivalent Similarité Cosinus si normalisé)
        index = faiss.IndexFlatIP(dimension)
        
        # Normalisation L2 des vecteurs pour garantir un calcul de similarité cosinus exact
        faiss.normalize_L2(vecteurs)
        index.add(vecteurs)
        
        # Sauvegarde sur le disque
        faiss.write_index(index, INDEX_PATH)
        _index_faiss_instance = index
        print("✨ [VECTOR INDEX] Structure spatiale FAISS sauvegardée avec succès.")

    return _index_faiss_instance


def rechercher_competences_proches(phrase_texte, top_k=2, seuil_score=0.55):
    """
    Prend une phrase, génère son vecteur, interroge FAISS,
    et renvoie les compétences officielles ESCO qui s'en rapprochent.
    """
    index = _initialiser_index_vectoriel()
    competences_globales = charger_competences_esco()

    if index is None or not competences_globales:
        return []

    # 1. Vectorisation de la phrase utilisateur
    vecteur_phrase = generer_un_embedding(phrase_texte)
    if vecteur_phrase is None:
        return []

    # Ajustement de la dimension pour FAISS (doit être un tableau 2D)
    vecteur_phrase = np.expand_dims(vecteur_phrase, axis=0)
    faiss.normalize_L2(vecteur_phrase)

    # 2. Recherche spatiale des K plus proches voisins
    scores, index_trouves = index.search(vecteur_phrase, top_k)

    resultats = []
    # 3. Filtrage par seuil de pertinence pour éviter les mauvais choix
    for score, idx in zip(scores[0], index_trouves[0]):
        if idx != -1 and score >= seuil_score:
            resultats.append({
                "competence_officielle": competences_globales[idx],
                "score_proximite": float(score)
            })

    return resultats
