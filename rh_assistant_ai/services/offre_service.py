from services.nlp.preprocessing import clean_text

from services.nlp.skill_extractor import extract_skills

from services.nlp.diploma_extractor import extract_diplomas

from services.nlp.experience_extractor import extract_experience

import os
from werkzeug.utils import secure_filename
from config.database import db
from models.offre import Offre
from models.offre_analyser import OffreAnalyser
from services.file_service import extract_text
from services.file_service import analyseur_texte_extrait, extract_text

# def analyze_offre(text):

#     text = clean_text(text)

#     return {
#         "skills": extract_skills(text),
#         "diplomas": extract_diplomas(text),
#         "experiences": extract_experience(text)
#     }

import os
from werkzeug.utils import secure_filename
from config.database import db
from models.offre import Offre
from models.offre_analyser import OffreAnalyser
# Importez votre fonction d'extraction et d'analyse de texte ici si nécessaire
# from services.votre_module import extract_text, analyseur_texte_extrait

def save_offre(file, user):
    filename = secure_filename(file.filename)
    upload_folder = "uploads/offres"
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)

    extracted_text = extract_text(file_path)

    # CORRECTION 1 : Ajout de nom_fichier et chemin_fichier demandés par le nouveau modèle SQL
    offre = Offre(
        titre=filename,
        description=extracted_text[:500],
        nom_fichier=filename,          # Plus de valeur NULL ici ❌
        chemin_fichier=file_path,      # Plus de valeur NULL ici ❌
        contenu_texte=extracted_text,
        user_id=user.id
    )
    db.session.add(offre)
    db.session.commit()

    # Analyser le texte de l'offre
    informations_extraites = analyseur_texte_extrait(extracted_text)

    # Sauvegarder l'analyse dans la base de données
    synthese_competences_offre = OffreAnalyser(
        skills=", ".join(informations_extraites["skills"]),
        diplomas=", ".join(informations_extraites["diplomas"]),
        experiences=", ".join(map(str, informations_extraites["experiences"])),
        offre_id=offre.id
    )
    db.session.add(synthese_competences_offre)
    db.session.commit()

    # CORRECTION 2 : Alignement parfait de l'ordre du triplet retourné avec votre route (Object, Analyse, Data)
    return offre, synthese_competences_offre, informations_extraites


# def save_offre(file, user):
#     filename = secure_filename(file.filename)
#     upload_folder = "uploads/offres"
#     os.makedirs(upload_folder, exist_ok=True)
#     file_path = os.path.join(upload_folder, filename)
#     file.save(file_path)

#     extracted_text = extract_text(file_path)

#     offre = Offre(
#         titre=filename,
#         description=extracted_text[:500],
#         contenu_texte=extracted_text,
#         user_id=user.id
#     )
#     db.session.add(offre)
#     db.session.commit()

#     # Analyser le texte de l'offre
#     # Les données sont des dictionnaires contenant les compétences, diplômes et expériences extraites
#     informations_extraites = analyseur_texte_extrait(extracted_text)

#     # Sauvegarder l'analyse dans la base de données
#     # les données sont des chaînes de caractères séparées par des virgules pour les compétences et les diplômes, et une chaîne de caractères pour les expériences
#     synthese_competences_offre = OffreAnalyser(
#         skills=", ".join(informations_extraites["skills"]),
#         diplomas=", ".join(informations_extraites["diplomas"]),
#         experiences=", ".join(map(str, informations_extraites["experiences"])),
#         offre_id=offre.id
#     )
#     db.session.add(synthese_competences_offre)
#     db.session.commit()

#     return offre, informations_extraites, synthese_competences_offre

