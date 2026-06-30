import os
from werkzeug.utils import secure_filename
from config.database import db
from models.cv import CV
from models.cv_analyser import CVAnalyser
from services.file_service import analyseur_texte_extrait, extract_text

def save_cv(file, candidat): 
    filename = secure_filename(file.filename)

    upload_folder = "static/uploads/cvs"
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, filename)
    
    # Sauvegarder le fichier original
    file.save(file_path)
    
    # Extraire le texte du PDF
    extracted_text = extract_text(file_path)

    # 🟢 CORRECTION : Liaison stricte vers la table enfant candidats via candidat_id
    cv = CV(
        nom_fichier=filename,
        chemin_fichier=file_path,
        contenu_texte=extracted_text,
        candidat_id=candidat.id # 👈 Modifié ici pour s'aligner sur votre modèle CV
    )

    # Ajouter le cv en base de données
    db.session.add(cv)
    db.session.commit()

    # Analyser le texte du CV avec votre assistant IA
    informations_extraites = analyseur_texte_extrait(extracted_text)

    # Sauvegarder la synthèse IA dans la table CVAnalyser
    synthese_competences_cv = CVAnalyser(
        skills=informations_extraites["skills"],
        diplomas=informations_extraites["diplomas"],
        experiences=informations_extraites["experiences"],
        cv_id=cv.id
    )

    # Ajouter l'analyse du cv dans la base de données
    db.session.add(synthese_competences_cv)
    db.session.commit()

    # Retourner le triplet (Objet, Analyse, Dictionnaire brut) exploité par vos routes
    return cv, synthese_competences_cv, informations_extraites
