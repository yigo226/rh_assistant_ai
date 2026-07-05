"""
Service d'Extraction Spécifique GLiNER (Étape 6 de l'architecture modulaire V2.1.0)
Responsabilités :
- Initialiser le modèle Zero-Shot GLiNER via Lazy Loading
- Extraire de façon étanche les diplômes et les intitulés de postes passés
"""

from gliner import GLiNER

# Instance globale (Lazy Loading validé par le professeur)
_gliner_model_instance = None

def _get_gliner():
    """Initialise le modèle GLiNER uniquement au moment du besoin."""
    global _gliner_model_instance
    if _gliner_model_instance is None:
        print("🤖 [IA GLINER] Chargement du modèle de Token Classification Zero-Shot...")
        # Modèle ultra-léger (200 Mo), rapide et redoutable pour filtrer le contexte
        _gliner_model_instance = GLiNER.from_pretrained("urchade/gliner_base-v2.1")
        print("✨ [IA GLINER] Modèle d'extraction structurelle prêt.")
    return _gliner_model_instance


def extraire_structures_gliner(texte_brut: str) -> tuple[list[str], list[str]]:
    """
    Analyse le texte et extrait uniquement les Diplômes et les Postes/Métiers.
    Returns:
        tuple: (liste_diplomes, liste_experiences)
    """
    if not texte_brut or not texte_brut.strip():
        return [], []

    model = _get_gliner()
    
    # 🟢 GUIDAGE ZÉRO-SHOT : On demande uniquement les étiquettes administratives
    labels = ["diplôme", "certification", "intitulé de poste", "métier"]
    
    predictions = model.predict_entities(texte_brut, labels)
    
    brut_diplomes = []
    brut_experiences = []

    for entite in predictions:
        label = entite.get("label")
        valeur = entite.get("text", "").strip()
        
        if len(valeur) < 2:
            continue
            
        if label in ["diplôme", "certification"]:
            brut_diplomes.add(valeur) if hasattr(brut_diplomes, 'add') else brut_diplomes.append(valeur)
        elif label in ["intitulé de poste", "métier"]:
            brut_experiences.add(valeur) if hasattr(brut_experiences, 'add') else brut_experiences.append(valeur)

    return list(set(brut_diplomes)), list(set(brut_experiences))
