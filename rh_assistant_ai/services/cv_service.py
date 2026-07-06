import os
from werkzeug.utils import secure_filename
from config.database import db
from models.cv import CV
from models.cv_analyser import CVAnalyser
from services.file_service import extract_text
from services.analyser_dict_service import analyseur_texte_extrait # V1
#from services.analyseur_ai_service import analyseur_texte_extrait # V2.1.0

def save_cv(fichier, candidat): 
    nom_fichier = secure_filename(fichier.filename)

    dossier_upload = "static/uploads/cvs"
    os.makedirs(dossier_upload, exist_ok=True)
    chemin_fichier = os.path.join(dossier_upload, nom_fichier)
    
    # Sauvegarder le fichier original
    fichier.save(chemin_fichier)
    
    # Extraire le texte du PDF
    texte_extrait = extract_text(chemin_fichier)



    # Création du CV lié à la table enfant candidats
    cv = CV(
        nom_fichier=nom_fichier,
        chemin_fichier=chemin_fichier,
        candidat_id=candidat.id
    )

    # Ajouter le cv en base de données
    db.session.add(cv)
    db.session.commit()

    # Analyser le texte du CV avec l'assistant IA (Retourne les clés en français)
    informations_extraites = analyseur_texte_extrait(texte_extrait)

    # Utilisation des nouveaux champs et clés en français
    synthese_competences_cv = CVAnalyser(
        contenu_texte=texte_extrait,
        competences=informations_extraites["competences"],
        diplomes=informations_extraites["diplomes"],
        experiences=informations_extraites["experiences"],
        cv_id=cv.id
    )

    # Ajouter l'analyse du cv dans la base de données
    db.session.add(synthese_competences_cv)
    db.session.commit()

    # Retourner le triplet exploité par vos routes
    return cv, synthese_competences_cv, informations_extraites
