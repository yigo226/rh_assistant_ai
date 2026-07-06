# =============================================================================
# rh_assistant — analyseur.py
# =============================================================================
# ANALYSEUR PRINCIPAL
# -----------------------------------------------------------------------------
# Extraction sémantique de compétences à partir de texte brut (CV, offre…)
#
# Approche :
#   1. Nettoyage et découpage du texte brut en phrases / blocs (pur Python)
#   2. Envoi des phrases à l'API Anthropic (Claude) pour extraction sémantique
#   3. Déduplication et normalisation des compétences retournées
#
# Aucune liste de compétences prédéfinie — c'est le modèle qui infère.
# Fonctionne en français et en anglais.
# =============================================================================
from .file_service import clean_text, extract_diplomas, extract_experience

import re
import json
import os
import requests
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────────────────────────────────────

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL   = "claude-sonnet-4-6"

# Taille maximale de texte envoyée au modèle (tokens ≈ caractères / 4)
MAX_CHARS_PER_CHUNK = 3000

# Séparateurs de phrases :
#   - fin de phrase classique (. ! ?)
#   - paragraphe vide (double saut de ligne)
#   - point-virgule
#   - tirets et puces de liste en début de ligne
PHRASE_SEPARATORS = re.compile(
    r'(?<=[.!?])\s+|'
    r'\n{2,}|'
    r'(?<=;)\s+|'
    r'\n\s*[-•·▪▸*]\s*'
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. NETTOYAGE ET DÉCOUPAGE DU TEXTE
# ─────────────────────────────────────────────────────────────────────────────

def _nettoyer(texte: str) -> str:
    """
    Supprime les artefacts courants d'un texte extrait de PDF :
      - caractères de contrôle
      - espaces multiples
      - lignes de séparation (tirets, underscores répétés)
    """
    # Caractères de contrôle (hors \n et \t)
    texte = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', texte)
    # Espaces multiples sur une même ligne
    texte = re.sub(r'[ \t]{2,}',           ' ',    texte)
    # Lignes de séparation visuelles (---, ===, ___)
    texte = re.sub(r'[-_=]{3,}',           '\n',   texte)
    # Sauts de ligne excessifs
    texte = re.sub(r'\n{3,}',              '\n\n', texte)
    return texte.strip()


def _decouper_en_phrases(texte: str) -> list[str]:
    """
    Découpe le texte brut en phrases / blocs significatifs.

    Stratégie :
      - Split sur les séparateurs (regex PHRASE_SEPARATORS)
      - Fragments courts (< 8 car.) → accumulés dans un tampon
        pour ne pas atomiser les listes "Python · Java · SQL"
      - Le tampon est vidé dès qu'un fragment long est rencontré
    """
    bruts = PHRASE_SEPARATORS.split(texte)

    phrases = []
    tampon  = ""

    for fragment in bruts:
        fragment = fragment.strip()
        if not fragment:
            continue

        if len(fragment) < 8:
            tampon = (tampon + " " + fragment).strip() if tampon else fragment
        else:
            if tampon:
                phrases.append(tampon)
                tampon = ""
            phrases.append(fragment)

    if tampon:
        phrases.append(tampon)

    return phrases


def _grouper_en_chunks(phrases: list[str], max_chars: int = MAX_CHARS_PER_CHUNK) -> list[str]:
    """
    Regroupe les phrases en blocs ≤ max_chars caractères pour :
      - Réduire le nombre d'appels API
      - Rester sous la limite de tokens du modèle
    """
    chunks, chunk_courant = [], ""

    for phrase in phrases:
        if len(chunk_courant) + len(phrase) + 2 > max_chars:
            if chunk_courant:
                chunks.append(chunk_courant.strip())
            chunk_courant = phrase
        else:
            chunk_courant = (chunk_courant + "\n" + phrase).strip()

    if chunk_courant:
        chunks.append(chunk_courant.strip())

    return chunks


# ─────────────────────────────────────────────────────────────────────────────
# 2. APPEL API — extraction sémantique
# ─────────────────────────────────────────────────────────────────────────────

# Prompt système : instructions strictes au modèle.
# Pas de liste de référence — le modèle infère librement.
_PROMPT_SYSTEME = """\
Tu es un extracteur de compétences professionnelles et techniques.
Ta seule tâche : lire un bloc de texte (extrait de CV ou d'offre d'emploi)
et retourner la liste des compétences, outils, technologies, langages,
méthodologies, domaines métier et aptitudes professionnelles mentionnés
ou clairement impliqués dans ce texte.

Règles strictes :
- Retourne UNIQUEMENT un tableau JSON de chaînes, sans aucun autre texte.
- Chaque compétence : 1 à 4 mots, en minuscules, sans articles.
- Si une phrase implique une compétence sans la nommer
  (ex: "je gère des équipes" → "management d'équipe"), inclus-la.
- Si la même compétence apparaît sous deux formes
  (ex: "ML" et "machine learning"), n'en garde qu'une.
- Si aucune compétence n'est détectable, retourne [].
- Réponds UNIQUEMENT avec le JSON, rien avant ni après.

Exemples :
  Entrée : "Java est utilisé pour le développement fullstack."
  Sortie : ["java", "développement fullstack"]

  Entrée : "Je suis ingénieur en data science. J'utilise plus Python que C."
  Sortie : ["data science", "python", "c"]

  Entrée : "Expérience en pilotage de projets Agile, équipes de 10 personnes."
  Sortie : ["gestion de projet", "agile", "management d'équipe"]
"""


def _appeler_api(chunk: str, api_key: str) -> list[str]:
    """
    Envoie un chunk de texte à l'API Anthropic.
    Retourne la liste de compétences extraites (peut être vide).
    Lève RuntimeError en cas de problème réseau ou HTTP.
    """
    headers = {
        "Content-Type":      "application/json",
        "x-api-key":         api_key,
        "anthropic-version": "2023-06-01",
    }

    payload = {
        "model":      ANTHROPIC_MODEL,
        "max_tokens": 512,
        "system":     _PROMPT_SYSTEME,
        "messages":   [{"role": "user", "content": chunk}],
    }

    try:
        response = requests.post(
            ANTHROPIC_API_URL,
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()

    except requests.exceptions.Timeout:
        raise RuntimeError("Timeout lors de l'appel à l'API Anthropic.")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(
            f"Erreur HTTP Anthropic {e.response.status_code} : {e.response.text}"
        )
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Erreur réseau : {e}")

    data = response.json()

    # Extraire le texte brut de la réponse
    try:
        texte_reponse = data["content"][0]["text"].strip()
    except (KeyError, IndexError):
        return []

    # Parser le JSON — on tolère un préfixe/suffixe parasite du modèle
    match = re.search(r'\[.*?\]', texte_reponse, re.DOTALL)
    if not match:
        return []

    try:
        competences = json.loads(match.group())
        return [str(c).strip().lower() for c in competences if c]
    except json.JSONDecodeError:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# 3. DÉDUPLICATION ET NORMALISATION
# ─────────────────────────────────────────────────────────────────────────────

def _normaliser(competence: str) -> str:
    """Minuscules + espaces nettoyés."""
    return re.sub(r'\s+', ' ', competence.strip().lower())


def _dedupliquer(liste: list[str]) -> list[str]:
    """
    Supprime les doublons stricts et les sous-chaînes redondantes.

    Logique :
      - Si "python" et "python 3" coexistent, on garde "python 3"
        (forme la plus précise / longue).
      - Résultat trié alphabétiquement pour faciliter la lecture.

    Exemples :
      ["python", "python", "python 3"]  →  ["python 3"]
      ["sql", "sql avancé", "java"]     →  ["java", "sql avancé"]
    """
    normalisees = [_normaliser(c) for c in liste if c.strip()]

    # Étape 1 : déduplications strictes en préservant l'ordre
    vues, uniques = set(), []
    for c in normalisees:
        if c not in vues:
            vues.add(c)
            uniques.append(c)

    # Étape 2 : retirer les sous-chaînes redondantes
    resultat = [
        c for c in uniques
        if not any(c != autre and c in autre for autre in uniques)
    ]

    return sorted(resultat)


# ─────────────────────────────────────────────────────────────────────────────
# ANALYSEUR PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def analyseur_texte_extrait(
    text:    str,
    api_key: Optional[str] = None,
) -> dict:
    """
    Extrait et retourne les compétences contenues dans un texte brut.

    Paramètres
    ----------
    text : str
        Texte brut à analyser (CV, offre d'emploi, profil LinkedIn…).
        Peut contenir des artefacts PDF (retours à la ligne, puces, etc.).

    api_key : str, optionnel
        Clé API Anthropic. Si absente, la variable d'environnement
        ANTHROPIC_API_KEY est utilisée automatiquement.

    Retourne
    --------
    dict avec la clé :
        "competences" : list[str]
            Liste de compétences normalisées, dédupliquées et triées
            alphabétiquement.

    Exemple de sortie :
        {
            "competences": ["agile", "c", "data science", "java", "python", "sql"]
        }

    Lève
    ----
    ValueError
        Si aucune clé API Anthropic n'est disponible.
    RuntimeError
        Si un appel API échoue (réseau, HTTP).

    Exemples
    --------
    >>> result = analyseur_texte_extrait(
    ...     "Java est utilisé pour le développement fullstack. "
    ...     "Je suis ingénieur en data science, j'utilise plus Python que C."
    ... )
    >>> print(result)
    {'competences': ['c', 'data science', 'développement fullstack', 'java', 'python']}
    """

    # ── Résolution de la clé API ──────────────────────────────────────────
    cle = api_key or os.getenv("ANTHROPIC_API_KEY")
    if not cle:
        raise ValueError(
            "Clé API Anthropic manquante. "
            "Passez-la en paramètre ou définissez la variable d'environnement "
            "ANTHROPIC_API_KEY."
        )

    if not text or not text.strip():
        return {"competences": []}

    # ── Étape 1 : nettoyage et découpage ─────────────────────────────────
    texte_propre = _nettoyer(text)
    phrases      = _decouper_en_phrases(texte_propre)
    chunks       = _grouper_en_chunks(phrases)

    # ── Étape 2 : extraction via API (un appel par chunk) ─────────────────
    toutes: list[str] = []
    for chunk in chunks:
        if chunk.strip():
            toutes.extend(_appeler_api(chunk, cle))

    # ── Étape 3 : déduplication et normalisation ──────────────────────────
    competences_list = _dedupliquer(toutes)
        # 2. VOS FONCTIONS QUI MARCHENT DÉJÀ (Inchangées)
    text_nettoye = clean_text(text)
    liste_diplomes = extract_diplomas(text_nettoye)
    liste_experiences = extract_experience(text_nettoye)
    print(f"🧠 [PIPELINE IA] Compétences extraites : {competences_list}")
    return {
        "competences": competences_list,
        "diplomes": list(liste_diplomes) if liste_diplomes else [],
        "experiences": list(liste_experiences) if liste_experiences else []
    }


# ─────────────────────────────────────────────────────────────────────────────
# POINT D'ENTRÉE DE TEST  →  python analyseur.py
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    TEXTE_TEST = """
    Jean DUPONT — Chef de Projet Senior

    Je suis ingénieur en data science avec 8 ans d'expérience.
    J'utilise Python au quotidien, beaucoup plus que C ou C++.
    Je travaille sur des pipelines de données avec Apache Spark et Kafka.

    Dans mon poste actuel chez Société Générale, je pilote des projets
    de transformation digitale en méthode Agile / Scrum.
    Je manage une équipe de 12 personnes et j'assure la relation client.

    • Java est utilisé pour le développement fullstack.
    • Je maîtrise SQL, PostgreSQL, et un peu de MongoDB.
    • En machine learning : scikit-learn, TensorFlow et HuggingFace.

    Langues : Français natif · Anglais C1 (TOEIC 920) · Espagnol B2.
    Certifications : PMP, AWS Solutions Architect Associate.
    """

    SEP = "─" * 60

    print(SEP)
    print("TEST — analyseur_texte_extrait()")
    print(SEP)
    print()

    try:
        resultats = analyseur_texte_extrait(TEXTE_TEST)
        competences = resultats["competences"]
        print(f"{len(competences)} compétences détectées :\n")
        for i, c in enumerate(competences, 1):
            print(f"  {i:>2}. {c}")
        print(f"\nStructure retournée : {{'competences': [{len(competences)} éléments]}}")

    except ValueError as e:
        print(f"⚠  {e}")
        print("   → Définissez ANTHROPIC_API_KEY=sk-... pour lancer le test.")

    except RuntimeError as e:
        print(f"✗  Erreur API : {e}")

    print()
    print(SEP)