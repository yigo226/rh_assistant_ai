"""
Chef d'Orchestre du Pipeline IA (Étape 7 de l'architecture modulaire V2.1.0)
Responsabilités :
- Recevoir le texte brut d'un document (CV ou Offre d'emploi)
- Coordonner le pipeline complet : Prétraitement ➔ GLiNER ➔ Vectorisation ESCO ➔ Normalisation
- Retourner le dictionnaire final structuré en français pour l'ORM SQLAlchemy
"""

# from services.ai.preprocessing import clean_text, split_sentences_spacy
# from services.ai.gliner_service import extraire_structures_gliner
# from services.ai.vector_index import rechercher_competences_proches
# from services.ai.normalizer import harmoniser_et_dedupliquer

# def analyseur_texte_extrait(texte_brut: str) -> dict:
#     """
#     Fonction maîtresse unifiée. Conserve la signature exacte attendue par votre 
#     application pour ne casser aucune route existante (offre_service / cv_service).
#     """
#     print("\n🚀 [PIPELINE IA] Démarrage de l'analyse structurelle modulaire...")
#     if not texte_brut or not texte_brut.strip():
#         return {"competences": [], "diplomes": [], "experiences": []}

#     # ÉTAPE 1 : Nettoyage initial du texte
#     texte_nettoye = clean_text(texte_brut)

#     # ÉTAPE 2 : Extraction isolée des Diplômes et des Métiers via GLiNER
#     print("🧠 [PIPELINE IA] Étape A : Extraction des structures administratives (GLiNER)...")
#     liste_diplomes, liste_experiences = extraire_structures_gliner(texte_nettoye)

#     # ÉTAPE 3 : Découpage intelligent par phrase avec spaCy pour les compétences
#     print("📝 [PIPELINE IA] Étape B : Segmentation grammaticale des phrases (spaCy)...")
#     phrases = split_sentences_spacy(texte_nettoye)

#     # ÉTAPE 4 : Recherche sémantique vectorielle de chaque phrase dans le référentiel ESCO
#     print(f"🔍 [PIPELINE IA] Étape C : Recherche vectorielle sémantique dans les 13 000 compétences ESCO (FAISS)...")
#     liste_competences_brutes = []
    
#     for phrase in phrases:
#         # On extrait les 2 compétences ESCO les plus proches de cette phrase
#         matchs_esco = rechercher_competences_proches(phrase, top_k=2, seuil_score=0.58)
#         for match in matchs_esco:
#             liste_competences_brutes.append(match["competence_officielle"])

#     # ÉTAPE 5 : Fusion et normalisation stricte contre les doublons
#     print("🧹 [PIPELINE IA] Étape D : Consolidation, déduplication et normalisation des critères...")
#     competences_finales = harmoniser_et_dedupliquer(liste_competences_brutes)
#     diplomes_finals = harmoniser_et_dedupliquer(liste_diplomes)
#     experiences_finales = [e.capitalize() for e in liste_experiences if len(e) > 3][:10]

#     print("✨ [PIPELINE IA] Analyse achevée avec succès. Transmission des données.")
    
#     # Retourne le format exact exigé par l'ORM
#     return {
#         "competences": competences_finales,
#         "diplomes": diplomes_finals,
#         "experiences": experiences_finales
#     }
import re
from .file_service import clean_text
import os
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, logging
from .file_service import clean_text, extract_skills, extract_diplomas, extract_experience

# Force Hugging Face à n'afficher que les erreurs critiques
logging.set_verbosity_error()

# Instances globales (initialisées à None)
_flan_model_instance = None
_flan_tokenizer_instance = None

def _get_flan_t5():
    """Initialise le modèle FLAN-T5 et son tokenizer uniquement au premier appel."""
    global _flan_model_instance, _flan_tokenizer_instance
    
    if _flan_model_instance is None or _flan_tokenizer_instance is None:
        print("🤖 [IA FLAN-T5] Chargement initial du modèle Text-to-Text...")
        
        model_name = "google/flan-t5-base"
        
        # Chargement simultané des deux composants obligatoires
        _flan_tokenizer_instance = AutoTokenizer.from_pretrained(model_name)
        _flan_model_instance = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        
        print("✨ [IA FLAN-T5] Modèle d'extraction textuelle prêt en mémoire.")
        
    return _flan_tokenizer_instance, _flan_model_instance



# Instances globales pour le Lazy Loading
_gliner_model_instance = None

def _get_gliner():
    """Initialise le modèle GLiNER uniquement au moment du besoin."""
    global _gliner_model_instance
    if _gliner_model_instance is None:
        print("🤖 [IA GLINER] Chargement du modèle de Token Classification Zero-Shot...")
        from gliner import GLiNER
        _gliner_model_instance = GLiNER.from_pretrained("urchade/gliner_multi-v2.1")
        print("✨ [IA GLINER] Modèle d'extraction structurelle prêt.")
    return _gliner_model_instance

def analyseur_texte_extrait(text):
    """
    Analyse le texte brut, extrait les entités sémantiques 
    et retourne un dictionnaire structuré avec des clés en français.
    """
    model = _get_get_gliner() if '_get_get_gliner' in globals() else _get_gliner()
    
    # 1. DÉCOUPAGE CHIRURGICAL POUR GLINER (Évite le bug de troncature à 384 tokens)
    # On découpe le texte par ligne ou par point pour envoyer des petits morceaux à l'IA
    phrases = [p.strip() for p in re.split(r'[\n\.]', text) if p.strip()]
    
    labels = ["compétence technique"]
    toutes_les_entites = []
    
    # L'IA analyse chaque ligne séparément et accumule les résultats
    for phrase in phrases:
        entities = model.predict_entities(phrase, labels, threshold=0.3)
        toutes_les_entites.extend(entities)
    
    # Récupération et nettoyage des textes extraits par GLiNER
    competences_brutes = [ent["text"] for ent in toutes_les_entites]
    
    # Élimination des doublons et uniformisation en minuscules
    competences_propres = list(set([c.strip().lower() for c in competences_brutes if len(c.strip()) > 1]))
    competences_propres.sort()

    # 2. VOS FONCTIONS QUI MARCHENT DÉJÀ (Inchangées)
    text_nettoye = clean_text(text)
    liste_diplomes = extract_diplomas(text_nettoye)
    liste_experiences = extract_experience(text_nettoye)
    
    print(f"🧠 [PIPELINE IA] Compétences extraites : {competences_propres}")
    print(f"🧠 [PIPELINE IA] Diplômes extraits : {liste_diplomes}")
    print(f"🧠 [PIPELINE IA] Expériences extraits : {liste_experiences}")
    
    return {
        "competences": list(competences_propres) if competences_propres else [],
        "diplomes": list(liste_diplomes) if liste_diplomes else [],
        "experiences": list(liste_experiences) if liste_experiences else []
    }


# def analyseur_texte_extrait(texte_brut):
#     """
#     Analyse le texte brut, extrait les compétences professionnelles 
#     et retourne un dictionnaire structuré avec des clés en français.
#     """
#     # Appel de la fonction de Lazy Loading pour récupérer les instances uniques
#     tokenizer, model = _get_flan_t5()
    
#     # Nettoyage initial du texte
#     text = clean_text(texte_brut)
#     liste_diplomes = extract_diplomas(text)
#     liste_experiences = extract_experience(text)
    
#     prompt = (
#         "Task: Extract professional skills from the text. Return ONLY a comma-separated list.\n\n"
#         "Text: Developed RESTful APIs using Python and Django, deployed on AWS EC2.\n"
#         "Skills: Python, Django, AWS\n\n"
#         "Text: Looking for a developer with experience in React, Node.js and Tailwind CSS.\n"
#         "Skills: React, Node.js, Tailwind CSS\n\n"
#         f"Text: {text}\n"
#         "Skills:"
#     )
    
#     inputs = tokenizer(prompt, return_tensors="pt")
    
#     outputs = model.generate(
#         **inputs, 
#         max_new_tokens=40,       
#         num_beams=2,             
#         repetition_penalty=2.5,  
#         length_penalty=0.5,      
#         early_stopping=True
#     )
    
#     resultat_brut = tokenizer.decode(outputs, skip_special_tokens=True)
    
#     # Nettoyage
#     texte_propre = str(resultat_brut)
#     lignes = texte_propre.split("\n")
#     premiere_ligne = lignes[0] if lignes else texte_propre
    
#     phrases = premiere_ligne.split(".")
#     resultat_nettoye = phrases[0].strip() if phrases else premiere_ligne.strip()
    
#     caracteres_a_retirer = ["[", "]", "'", '"']
#     for char in caracteres_a_retirer:
#         resultat_nettoye = resultat_nettoye.replace(char, "")
    
#     liste_competences = [skill.strip() for skill in resultat_nettoye.split(",") if skill.strip()]
#     print(f"🧠 [PIPELINE IA] Compétences extraites : {liste_competences}")
#     print(f"🧠 [PIPELINE IA] Diplômes extraits : {liste_diplomes}")
#     print(f"🧠 [PIPELINE IA] Expériences extraits : {liste_experiences}")
#     return {
#         "competences": list(liste_competences) if liste_competences else [],
#         "diplomes": list(liste_diplomes) if liste_diplomes else [],
#         "experiences": list(liste_experiences) if liste_experiences else []
#     }


# --- SCRIPT DE TEST POUR VÉRIFIER LE COMPORTEMENT ---
# if __name__ == "__main__":
#     print("🚀 Démarrage du projet (le modèle ne doit pas encore se charger)...")
    
#     texte_cv_1 = "Experienced in Python and Docker."
#     texte_cv_2 = "Knowledge of Kubernetes and PostgreSQL."
    
#     print("\n--- Premier appel (Le modèle va se charger) ---")
#     print(analyseur_texte_extrait(texte_cv_1))
    
#     print("\n--- Deuxième appel (Le modèle est déjà en mémoire, ce sera instantané) ---")
#     print(analyseur_texte_extrait(texte_cv_2))
