import re
from transformers import pipeline
from gliner import GLiNER

# ==========================================================
# INITIALISATION (Lazy Loading)
# ==========================================================

_gliner = None
_skill_model = None

from transformers import pipeline

pipe = pipeline(
    "token-classification",
    model="Ivo/emscad-skill-extraction-token-classification",
    aggregation_strategy=None
)

res = pipe("Python React Docker SQL")

print(res)

# def _init_models():
#     global _gliner, _skill_model

#     if _gliner is None:
#         print("🤖 Chargement de GLiNER...")
#         _gliner = GLiNER.from_pretrained(
#             "urchade/gliner_multi-v2.1"
#         )

#     if _skill_model is None:
#         print("🤖 Chargement du modèle Skill Extraction...")

#         _skill_model = pipeline(
#             "token-classification",
#             model="Ivo/emscad-skill-extraction-token-classification",
#             aggregation_strategy="simple"
#         )

#     print("✅ Modèles chargés.")


# ==========================================================
# OUTILS
# ==========================================================

# def nettoyer(texte):
#     texte = re.sub(r"\s+", " ", texte)
#     return texte.strip()


# ==========================================================
# EXTRACTION DES COMPÉTENCES
# ==========================================================

# def extraire_competences(texte):

#     resultats = _skill_model(texte)

#     competences = set()

#     for r in resultats:

#         mot = r["word"].replace("##", "").strip()

#         if len(mot) > 1:
#             competences.add(mot)

#     return sorted(competences)


# ==========================================================
# EXTRACTION DES DIPLÔMES / MÉTIERS
# ==========================================================

# def extraire_entites(texte):

#     labels = [
#         "diplôme",
#         "métier",
#         "poste"
#     ]

#     entites = _gliner.predict_entities(
#         texte,
#         labels
#     )

#     diplomes = set()
#     experiences = set()

#     for e in entites:

#         valeur = e["text"].strip()

#         if len(valeur) < 2:
#             continue

#         if e["label"] == "diplôme":
#             diplomes.add(valeur)

#         else:
#             experiences.add(valeur)

#     return list(diplomes), list(experiences)


# ==========================================================
# FONCTION PRINCIPALE
# ==========================================================

# def analyseur_texte_extrait(texte):

#     if not texte or not texte.strip():

#         return {
#             "competences": [],
#             "diplomes": [],
#             "experiences": []
#         }

#     _init_models()

#     texte = nettoyer(texte)

#     competences = extraire_competences(texte)

#     diplomes, experiences = extraire_entites(texte)

#     return {
#         "competences": competences,
#         "diplomes": diplomes,
#         "experiences": experiences
#     }

