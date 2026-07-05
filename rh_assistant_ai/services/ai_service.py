import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

# L'instance reste à None au démarrage de Flask (Lazy Loading approuvé par le prof)
_pipeline_llm_instance = None

def _get_pipeline_llm():
    global _pipeline_llm_instance
    if _pipeline_llm_instance is None:
        print("🤖 [IA LOCAL] Premier appel détecté : Chargement du Mini-LLM Qwen en RAM...")
        nom_modele = "Qwen/Qwen2.5-0.5B-Instruct"
        
        tokenizer = AutoTokenizer.from_pretrained(nom_modele)
        print("Tokenizer chargé avec succès.")
        model = AutoModelForCausalLM.from_pretrained(
            nom_modele,
            torch_dtype="auto",
            device_map="auto"
        )
        _pipeline_llm_instance = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer
        )
        print("✨ [IA LOCAL] Modèle Qwen chargé avec succès.")
    return _pipeline_llm_instance


def analyseur_texte_extrait(text):
    """
    Analyse le texte brut d'un document (CV ou Offre).
    Le prompt système force l'IA à extraire les données sous forme de JSON structuré.
    """
    if not text or not text.strip():
        return {"competences": [], "diplomes": [], "experiences": []}

    # Récupération de l'instance de l'IA à la demande
    pipeline_llm = _get_pipeline_llm()

    # 🟢 LE PROMPT SYSTÈME CRUCIAL POUR LE SIRH :
    prompt_systeme = (
        "Tu es un expert en recrutement SIRH. Analyse le texte fourni et extrait :\n"
        "1) Les compétences techniques ou humaines (competences).\n"
        "2) Les diplômes ou certifications (diplomes).\n"
        "3) Les titres de postes passés ou requis (experiences).\n"
        "Tu dois répondre UNIQUEMENT sous la forme d'un objet JSON valide avec ces 3 clés :\n"
        '{"competences": [...], "diplomes": [...], "experiences": [...]}.\n'
        "Ne saisis aucun texte avant ou après le JSON, pas d'explication, pas de balises."
    )

    # Structuration des rôles pour le modèle Instruct
    messages = [
        {"role": "system", "content": prompt_systeme},
        {"role": "user", "content": f"Voici le texte à analyser :\n{text}"}
    ]

    # try:
    #     # Génération par l'IA
    #     outputs = pipeline_llm(messages, max_new_tokens=512, return_full_text=False)
    #     texte_reponse = outputs['generated_text'].strip()

    #     # Nettoyage des éventuels résidus de blocs de code Markdown (```json ... ```)
    #     if texte_reponse.startswith("```json"):
    #         texte_reponse = texte_reponse.replace("```json", "").replace("```", "").strip()
    #     elif texte_reponse.startswith("```"):
    #         texte_reponse = texte_reponse.replace("```", "").strip()

    #     # Conversion brute du texte de l'IA en dictionnaire Python pour l'ORM
    #     donnees_extraites = json.loads(texte_reponse)
        
    #     return {
    #         "competences": sorted(list(set(donnees_extraites.get("competences", [])))),
    #         "diplomes": sorted(list(set(donnees_extraites.get("diplomes", [])))),
    #         "experiences": sorted(list(set(donnees_extraites.get("experiences", []))))
    #     }

    # except Exception as e:
    #     print(f"⚠️ Erreur de parsing JSON de la réponse LLM : {str(e)}. Retour de listes vides de secours.")
    #     return {"competences": [], "diplomes": [], "experiences": []}
   
    try:
        # Génération par l'IA (Retourne une liste contenant un dictionnaire)
        outputs = pipeline_llm(messages, max_new_tokens=512, return_full_text=False)
        
        # 🟢 CORRECTION CHIRURGICALE : On accède d'abord au premier élément de la liste [0]
        texte_reponse = outputs[0]['generated_text'].strip()
        print(f"🤖 [IA LOCAL] Réponse brute du LLM :\n{texte_reponse}") # Pour observer le JSON dans le terminal

        # Nettoyage des éventuels résidus de blocs de code Markdown (```json ... ```)
        if texte_reponse.startswith("```json"):
            texte_reponse = texte_reponse.replace("```json", "").replace("```", "").strip()
        elif texte_reponse.startswith("```"):
            texte_reponse = texte_reponse.replace("```", "").strip()

        # Conversion brute du texte du LLM en dictionnaire Python
        donnees_extraites = json.loads(texte_reponse)
        
        return {
            "competences": sorted(list(set(donnees_extraites.get("competences", [])))),
            "diplomes": sorted(list(set(donnees_extraites.get("diplomes", [])))),
            "experiences": sorted(list(set(donnees_extraites.get("experiences", []))))
        }

    except Exception as e:
        print(f"⚠️ Erreur de parsing JSON de la réponse LLM : {str(e)}. Retour de listes vides de secours.")
        return {"competences": [], "diplomes": [], "experiences": []}
