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

# =============================================================================
# rh_assistant — qwen_interview_service.py
# =============================================================================
# Génération de questions d'entretien via Qwen2.5-1.5B-Instruct (local)
#
# Corrections apportées :
#   - max_new_tokens augmenté + calcul dynamique selon la longueur de l'offre
#   - Extraction JSON robuste par regex (tolère un JSON tronqué)
#   - do_sample=True + temperature basse pour éviter les boucles de répétition
#   - Retour : liste de questions uniquement (sans catégorie)
#   - Lazy loading conservé pour ne pas pénaliser le démarrage Flask
# =============================================================================

import json
import os
import re


# ─────────────────────────────────────────────────────────────────────────────
# LAZY LOADING — modèle chargé une seule fois au premier appel
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# EXTRACTION JSON ROBUSTE
# ─────────────────────────────────────────────────────────────────────────────

def _extraire_questions_brutes(texte: str) -> list[str]:
    """
    Extrait les questions depuis le texte brut généré par le modèle.

    Stratégie en cascade :
      1. json.loads() direct sur le texte nettoyé  → idéal
      2. Regex sur le tableau "questions"           → si JSON tronqué
      3. Regex ligne par ligne sur "question": "…" → dernier recours

    Retourne toujours une liste (vide si rien n'est trouvable).
    """
    texte = texte.strip()

    # ── Nettoyage des blocs markdown parasites ──────────────────────────
    texte = re.sub(r"```[a-zA-Z]*", "", texte).strip()

    # ── Tentative 1 : parsing JSON complet ──────────────────────────────
    try:
        data = json.loads(texte)
        return _extraire_depuis_dict(data)
    except json.JSONDecodeError:
        pass

    # ── Tentative 2 : extraction du tableau "questions" par regex ────────
    # Capture tout ce qui est entre [ et ] après "questions":
    match_array = re.search(r'"questions"\s*:\s*(\[.*?\])', texte, re.DOTALL)
    if match_array:
        try:
            items = json.loads(match_array.group(1))
            questions = [
                item.get("question", "").strip()
                for item in items
                if isinstance(item, dict) and item.get("question", "").strip()
            ]
            if questions:
                return questions
        except json.JSONDecodeError:
            pass

    # ── Tentative 3 : extraction ligne par ligne sur "question": "…" ────
    # Utile quand le JSON est tronqué en plein milieu d'un objet
    questions_regex = re.findall(r'"question"\s*:\s*"([^"]+)"', texte)
    if questions_regex:
        return [q.strip() for q in questions_regex if q.strip()]

    # ── Échec total ──────────────────────────────────────────────────────
    print("⚠️ [QWEN] Aucune question extraite — réponse brute :")
    print(texte[:300])
    return []


def _extraire_depuis_dict(data: dict | list) -> list[str]:
    """Extrait la liste de questions depuis un objet JSON parsé."""
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        # Cherche la première clé dont la valeur est une liste
        items = next(
            (v for v in data.values() if isinstance(v, list)),
            []
        )
    else:
        return []

    return [
        item.get("question", "").strip()
        if isinstance(item, dict)
        else str(item).strip()
        for item in items
        if (isinstance(item, dict) and item.get("question", "").strip())
        or (isinstance(item, str) and item.strip())
    ]


# ─────────────────────────────────────────────────────────────────────────────
# GÉNÉRATION PRINCIPALE
# ─────────────────────────────────────────────────────────────────────────────

def generer_questions_entretien(contenu_texte: str) -> dict:
    """
    Analyse une offre d'emploi et génère 10 questions d'entretien en français.

    Paramètre
    ---------
    contenu_texte : str
        Texte brut de l'offre d'emploi.

    Retourne
    --------
    dict :
        {
            "questions": ["Question 1 ?", "Question 2 ?", ...]
        }
        La liste contient jusqu'à 10 questions, sans catégories.
        En cas d'échec d'extraction, "questions" est une liste vide
        et la clé "raw_response" contient la sortie brute du modèle.
    """
    tokenizer, model = _get_qwen_interview_llm()

    # ── Prompt ────────────────────────────────────────────────────────────
    # Consignes système en anglais : Qwen suit mieux le JSON avec des
    # instructions en anglais qu'en français.
    # On demande UNIQUEMENT le champ "question", pas la catégorie.
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert HR recruiter. "
                "Output ONLY valid raw JSON — no markdown fences, no extra text. "
                "The JSON must have exactly one key: 'questions', "
                "which is an array of exactly 10 objects, each with a single key 'question'."
            ),
        },
        {
            "role": "user",
            "content": (
                "Generate exactly 10 interview questions in French based on the job offer below.\n"
                "Cover: technical skills, experience, problem-solving, and soft skills.\n\n"
                "Required JSON format (no other keys allowed):\n"
                '{"questions": [{"question": "..."}, {"question": "..."}, ...]}\n\n'
                f"Job offer:\n{contenu_texte[:2000]}\n\n"   # tronqué à 2000 car. pour laisser de la place aux tokens de sortie
                "JSON:"
            ),
        },
    ]

    # ── Tokenisation ──────────────────────────────────────────────────────
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=1400,        # contexte d'entrée limité → laisse de la place pour la sortie
    ).to(model.device)

    prompt_length = inputs.input_ids.shape[1]

    # ── Calcul dynamique de max_new_tokens ────────────────────────────────
    # 10 questions × ~60 tokens chacune + enveloppe JSON ≈ 700 tokens
    # On ajoute une marge de 200 pour ne jamais tronquer
    max_new = 900

    # ── Génération ────────────────────────────────────────────────────────
    outputs = model.generate(
        **inputs,
        max_new_tokens=max_new,
        do_sample=True,          # nécessaire pour que repetition_penalty soit efficace
        temperature=0.1,         # très bas → quasi-déterministe, fidèle au schéma JSON
        repetition_penalty=1.25, # décourage les boucles de répétition (cause du tronquage)
        pad_token_id=tokenizer.eos_token_id,  # évite les warnings de padding
    )

    # ── Décodage (partie générée uniquement) ─────────────────────────────
    resultat_brut = tokenizer.decode(
        outputs[0][prompt_length:],
        skip_special_tokens=True,
    ).strip()

    # ── Extraction robuste ────────────────────────────────────────────────
    questions = _extraire_questions_brutes(resultat_brut)

    if not questions:
        return {
            "questions":    [],
            "raw_response": resultat_brut,
        }

    return {
        "questions": questions[:10],   # on s'assure de ne jamais dépasser 10
    }
