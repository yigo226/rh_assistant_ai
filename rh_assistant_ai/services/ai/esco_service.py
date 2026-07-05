"""
Service Référentiel ESCO (Étape 3 de l'architecture modulaire V2.1.0)
Responsabilités :
- Charger la liste des compétences françaises officielles depuis le CSV
- Générer et sauvegarder les vecteurs sémantiques des compétences (skills_embeddings.npy)
  pour éviter de recalculer les 13 400 lignes à chaque démarrage.
"""

import os
import numpy as np
import pandas as pd
from services.ai.embedding import generer_embeddings

CSV_PATH = "./nlp/data/esco/skills_fr.csv"
EMBEDDINGS_PATH = "./nlp/data/esco/skills_embeddings.npy"

_liste_competences_cache = None

def charger_competences_esco():
    """
    Charge la liste brute des chaînes de caractères des compétences ESCO en RAM.
    Utilise un cache local pour ne lire le fichier CSV qu'une seule fois.
    """
    global _liste_competences_cache
    if _liste_competences_cache is not None:
        return _liste_competences_cache

    if not os.path.exists(CSV_PATH):
        print(f"⚠️ Référentiel introuvable à l'adresse : {CSV_PATH}. Lancez d'abord le téléchargement.")
        return []

    print("📄 [ESCO SERVICE] Lecture du dictionnaire officiel ESCO...")
    df = pd.read_csv(CSV_PATH, encoding="utf-8")
    _liste_competences_cache = df["skill_name"].dropna().astype(str).tolist()
    return _liste_competences_cache


def charger_ou_creer_embeddings_esco():
    """
    Vérifie si le fichier binaire des vecteurs existe déjà.
    Si non, il calcule les vecteurs des 13 000 lignes (opération unique de ~1 min) et sauvegarde.
    """
    competences = charger_competences_esco()
    if not competences:
        return None

    if os.path.exists(EMBEDDINGS_PATH):
        print("💾 [ESCO SERVICE] Vecteurs ESCO trouvés sur le disque. Chargement binaire ultra-rapide...")
        return np.load(EMBEDDINGS_PATH)

    print("🧠 [ESCO SERVICE] Première initialisation : Calcul des vecteurs pour les 13 000 compétences...")
    print("⏳ (Cette opération unique peut prendre entre 30 secondes et 2 minutes selon votre machine...)")
    
    # Appel à notre brique d'embedding centralisée
    matrices_vecteurs = generer_embeddings(competences)
    
    # Sauvegarde sur le disque pour les prochains lancements
    os.makedirs(os.path.dirname(EMBEDDINGS_PATH), exist_ok=True)
    np.save(EMBEDDINGS_PATH, matrices_vecteurs)
    print("✨ [ESCO SERVICE] Calcul achevé. Vecteurs enregistrés définitivement sur le disque.")
    
    return matrices_vecteurs
