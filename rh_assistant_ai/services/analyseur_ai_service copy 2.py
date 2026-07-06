import os
import re
from .file_service import clean_text, extract_diplomas, extract_experience

# -------------------------------------------------------------------------
# INSTANCES GLOBALES & LAZY LOADING POUR LES DEUX IA
# -------------------------------------------------------------------------
_gliner_model_instance = None
_flan_tokenizer_instance = None
_flan_model_instance = None

def _get_gliner():
    global _gliner_model_instance
    if _gliner_model_instance is None:
        print("🤖 [IA GLINER] Chargement du modèle...")
        from gliner import GLiNER
        _gliner_model_instance = GLiNER.from_pretrained("urchade/gliner_multi-v2.1")
    return _gliner_model_instance

def _get_flan_t5():
    global _flan_tokenizer_instance, _flan_model_instance
    if _flan_model_instance is None or _flan_tokenizer_instance is None:
        print("🤖 [IA FLAN-T5] Chargement du modèle...")
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        model_name = "google/flan-t5-base"
        _flan_tokenizer_instance = AutoTokenizer.from_pretrained(model_name)
        _flan_model_instance = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    return _flan_tokenizer_instance, _flan_model_instance

# -------------------------------------------------------------------------
# FONCTION INTERNE POUR FLAN-T5 (EXTRACTION PAR PHRASE)
# -------------------------------------------------------------------------
# def _extraire_competence_flan_phrase(phrase, tokenizer, model):
#     """Demande à FLAN-T5 d'extraire les compétences d'une seule phrase."""
#     # Prompt Few-Shot très court adapté pour une seule phrase
#     prompt = (
#         "Task: Extract only professional technologies or technical skills from the text. Return a comma-separated list.\n"
#         "Text: Solides bases Python, Node.js, Typescript/React.\n"
#         "Skills: Python, Node.js, Typescript, React\n"
#         f"Text: {phrase}\n"
#         "Skills:"
#     )
    
#     inputs = tokenizer(prompt, return_tensors="pt")
#     outputs = model.generate(
#         **inputs, 
#         max_new_tokens=20, 
#         num_beams=2, 
#         repetition_penalty=2.0, 
#         early_stopping=True
#     )
#     res_brut = tokenizer.decode(outputs, skip_special_tokens=True)
    
#     # Nettoyage rapide des caractères parasites de génération
#     for c in ["[", "]", "'", '"', "."]:
#         res_brut = res_brut.replace(c, "")
        
#     return [s.strip().lower() for s in res_brut.split(",") if s.strip()]

import re
from .file_service import clean_text

# [Vos fonctions de Lazy Loading _get_flan_t5() restent inchangées]
def _extraire_competences_par_phrase(phrase, tokenizer, model):
    """
    Analyse une phrase et extrait strictement les compétences techniques.
    """
    prompt = (
        "Instructions: Extrais uniquement les compétences techniques, frameworks, langages ou outils informatiques présents dans le texte. "
        "Ne traduis pas le texte. Ne génère pas de phrases. Retourne les mots séparés par une virgule. Si aucune compétence n'est présente, réponds 'Aucune'.\n\n"
        "Texte: Solides bases Python, Node.js, Typescript/React.\n"
        "Compétences: Python, Node.js, Typescript, React\n\n"
        "Texte: Travailler au quotidien avec les fondateurs dans une ambiance dynamique.\n"
        "Compétences: Aucune\n\n"
        "Texte: Connaissances en bases de données (SQL / NoSQL) et en conception d’API.\n"
        "Compétences: SQL, NoSQL, API\n\n"
        f"Texte: {phrase}\n"
        "Compétences:"
    )
    
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(
        **inputs, 
        max_new_tokens=30, 
        num_beams=3, 
        repetition_penalty=2.5, 
        early_stopping=True
    )
    
    # CORRECTION ICI : On décode explicitement le premier index pour obtenir un String propre
    res_brut = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
    
    if res_brut.lower() in ["aucune", "none", ""] or "instructions:" in res_brut.lower():
        return []
        
    for c in ["[", "]", "'", '"', ".", "(", ")"]:
        res_brut = res_brut.replace(c, "")
        
    mots_extraits = re.split(r'[,/]', res_brut)
    return [m.strip().lower() for m in mots_extraits if m.strip()]


# -------------------------------------------------------------------------
# ANALYSEUR PRINCIPAL
# -------------------------------------------------------------------------
def analyseur_texte_extrait(text):
    """
    Analyseur principal utilisant FLAN-T5 de manière structurée.
    """
    tokenizer, model = _get_flan_t5()
    
    # Découpage du texte brut par ligne ou par point
    phrases = [p.strip() for p in re.split(r'[\n\.]', text) if p.strip()]
    
    competences_trouvees = set()
    
    for phrase in phrases:
        skills = _extraire_competences_par_phrase(phrase, tokenizer, model)
        for skill in skills:
            # FILTRE DE SÉCURITÉ IA : Une compétence informatique fait rarement plus de 2 mots
            # Cela élimine les phrases que le modèle aurait pu copier par erreur
            if len(skill.split()) <= 2:
                competences_trouvees.add(skill)
                
    competences_finales = sorted(list(competences_trouvees))

    # Vos fonctions existantes pour le reste du dictionnaire
    text_nettoye = clean_text(text)
    liste_diplomes = extract_diplomas(text_nettoye)
    liste_experiences = extract_experience(text_nettoye)
    
    print(f"🧠 [PIPELINE IA] Compétences extraites : {competences_finales}")
    
    return {
        "competences": competences_finales,
        "diplomes": list(liste_diplomes) if liste_diplomes else [],
        "experiences": list(liste_experiences) if liste_experiences else []
    }
