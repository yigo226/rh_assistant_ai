import json
import os
import re
from transformers import AutoTokenizer, AutoModelForCausalLM, logging

# Masquer les avertissements de téléchargement inutiles
logging.set_verbosity_error()
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Instances globales pour le Lazy Loading
_qwen_tokenizer_instance = None
_qwen_model_instance = None

def _get_qwen_interview_llm():
    """Initialise le modèle Qwen et son tokenizer uniquement au premier appel."""
    global _qwen_tokenizer_instance, _qwen_model_instance
    
    if _qwen_model_instance is None or _qwen_tokenizer_instance is None:
        print("🤖 [IA QWEN] Chargement du modèle de génération de questions...")
        
        # Le modèle 1.5B est le parfait compromis vitesse/précision en local
        model_name = "Qwen/Qwen2.5-0.5B-Instruct" 
        
        _qwen_tokenizer_instance = AutoTokenizer.from_pretrained(model_name)
        _qwen_model_instance = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype="auto",   # Aligne la précision selon votre CPU/GPU automatiquement
            device_map="auto"     # Bascule automatiquement sur GPU si disponible
        )
        print("✨ [IA QWEN] Modèle prêt pour la génération de questionnaires.")
        
    return _qwen_tokenizer_instance, _qwen_model_instance


def generer_questions_entretien(contenu_texte: str):
    """
    Analyse l'offre d'emploi et génère un dictionnaire standardisé 
    contenant exactement 10 questions d'entretien triées par catégorie.
    """
    tokenizer, model = _get_qwen_interview_llm()

    # Structure système stricte en anglais (Qwen suit mieux le JSON avec des consignes système en anglais)
    messages = [
        {
            "role": "system", 
            "content": "You are an expert HR recruiter. You output ONLY valid raw JSON matching the requested schema. No markdown block like ```json, no conversational text."
        },
        {
            "role": "user", 
            "content": f"""Generate exactly 10 interview questions in French based on this job offer. 
Cover technical skills, experience, behavioural skills, and problem solving.

Format:
{{
    "questions": [
        {{
            "categorie": "Technique",
            "question": "..."
        }},
        {{
            "categorie": "Comportemental",
            "question": "..."
        }}
    ]
}}

Job Offer:
{contenu_texte}

JSON:"""
        }
    ]
    
    # Application du template de chat natif de Qwen
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    
    # Encodage (max_length de 1500 pour accueillir l'offre complète)
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1500).to(model.device)

    # Paramètres de génération optimisés pour le JSON (temperature=0 pour éviter les divagations)
    outputs = model.generate(
        **inputs,
        max_new_tokens=800,  
        do_sample=False,
        repetition_penalty=1.1
    )

    # Récupération de la partie générée uniquement (on ignore le prompt initial)
    input_length = inputs.input_ids.shape[1]
    resultat_brut = tokenizer.decode(outputs[0][input_length:], skip_special_tokens=True).strip()

    print("\n 🤖 [IA QWEN] Réponse brute du modèle : \n", resultat_brut)
    # Sécurité anti-markdown : si Qwen entoure le code de blocs ```json ... ```
    if "```" in resultat_brut:
        resultat_brut = re.sub(r"```[a-zA-Z]*", "", resultat_brut).strip()

    try:
        # Transformation directe de la chaîne de caractères en dictionnaire Python
        return json.loads(resultat_brut)
    except Exception as e:
        print(f"⚠️ [IA QWEN] Erreur de parsing JSON. Réponse brute conservée.")
        print(f"Erreur: {str(e)}")
        return {
            "questions": [],
            "raw_response": resultat_brut
        }
