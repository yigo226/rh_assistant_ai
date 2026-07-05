from .file_service import clean_text, extract_skills, extract_diplomas, extract_experience

# ============================================================
#  ANALYSEUR AVEC DICTIONNAIRE 
# ============================================================
def analyseur_texte_extrait(text):
    """
    Analyse le texte brut, extrait les entités sémantiques 
    et retourne un dictionnaire structuré avec des clés en français.
    """
    # Nettoyage initial du texte
    texte_propre = clean_text(text)
    
    # Extraction NLP via vos modules dédiés
    liste_competences = extract_skills(texte_propre)
    liste_diplomes = extract_diplomas(texte_propre)
    liste_experiences = extract_experience(texte_propre)

    #  Clés renommées en français pour s'aligner sur les modèles SQL
    return {
        "competences": list(liste_competences) if liste_competences else [],
        "diplomes": list(liste_diplomes) if liste_diplomes else [],
        "experiences": list(liste_experiences) if liste_experiences else []
    }
