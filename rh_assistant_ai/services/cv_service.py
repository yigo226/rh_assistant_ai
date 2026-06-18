from werkzeug.utils import secure_filename
from config.database import db
from models.cv import CV
from models.cv_analyser import CVAnalyser
from services.file_service import analyseur_texte_extrait, extract_text
import os

# # Ces fonctions  d'nalyse cv
# def analyze_cv(text):
#     text = clean_text(text)
#     skills = extract_skills(text)
#     diplomas = extract_diplomas(text)
#     experiences = extract_experience(text)

#     return {
#         "skills": skills,
#         "diplomas": diplomas,
#         "experiences": experiences
#     }

def save_cv(file, user): 
    filename = secure_filename(file.filename)
    upload_folder = "uploads"
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, filename)
    # sauvegarder le fichier original
    file.save(file_path)
    
    # extraire le texte
    extracted_text = extract_text(file_path)

    # sauvegarder le CV dans la base de données
    cv = CV(
        nom_fichier=filename,
        chemin_fichier=file_path,
        contenu_texte=extracted_text,
        user_id=user.id
    )

    # Ajouter le cv 
    db.session.add(cv)
    db.session.commit()

    # analyser le texte du CV 
    informations_extraites  = analyseur_texte_extrait(extracted_text)

    # sauvegarder l'analyse dans la base de données
    synthese_competences_cv = CVAnalyser(
        # On envoie de la  liste de compétences directement dans le champ skills de l'analyse du cv
        skills=informations_extraites["skills"],
        diplomas=informations_extraites["diplomas"],
        experiences=informations_extraites["experiences"],
        cv_id=cv.id
    )

    # Ajouter l'analyse du cv dans la base de données
    db.session.add(synthese_competences_cv)
    db.session.commit()

    # return le cv créé pour pouvoir l'utiliser dans la route
    return cv, synthese_competences_cv,informations_extraites
