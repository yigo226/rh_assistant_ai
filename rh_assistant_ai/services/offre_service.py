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


# Importez votre fonction d'extraction et d'analyse de texte ici si nécessaire
# from services.votre_module import extract_text, analyseur_texte_extrait

# def save_offre(file, user):
#     filename = secure_filename(file.filename)
#     upload_folder = "uploads/offres"
#     os.makedirs(upload_folder, exist_ok=True)
#     file_path = os.path.join(upload_folder, filename)
#     file.save(file_path)

#     extracted_text = extract_text(file_path)

#     # CORRECTION 1 : Ajout de nom_fichier et chemin_fichier demandés par le nouveau modèle SQL
#     offre = Offre(
#         titre=filename,
#         description=extracted_text[:500],
#         nom_fichier=filename,          # Plus de valeur NULL ici ❌
#         chemin_fichier=file_path,      # Plus de valeur NULL ici ❌
#         contenu_texte=extracted_text,
#         user_id=user.id
#     )
#     db.session.add(offre)
#     db.session.commit()

#     # Analyser le texte de l'offre
#     informations_extraites = analyseur_texte_extrait(extracted_text)

#     # Sauvegarder l'analyse dans la base de données
#     synthese_competences_offre = OffreAnalyser(
#         #On envoie de la  liste de compétences directement dans le champ skills de l'analyse de l'offre
#         diplomas=informations_extraites["diplomas"],    # Idem
#         skills=informations_extraites["skills"],        
#         experiences=informations_extraites["experiences"], # Idem
#         offre_id=offre.id
#     )

#     # Ajouter l'analyse de l'offre dans la base de données
#     db.session.add(synthese_competences_offre)
#     db.session.commit()

#     # CORRECTION 2 : Alignement parfait de l'ordre du triplet retourné avec votre route (Object, Analyse, Data)
#     return offre, synthese_competences_offre, informations_extraites

def save_offre(file, user, titre, description, date_limite, departement_id, nom_entreprise):
    filename = secure_filename(file.filename)
    
    # Harmonisation du dossier d'upload vers static pour VS Code / Flask
    upload_folder = "static/uploads/offres"
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)

    # Extraction réelle du texte du PDF
    extracted_text = extract_text(file_path)

    # Création complète de l'Offre avec toutes les variables du formulaire
    offre = Offre(
        titre=titre,
        entreprise=nom_entreprise,
        description=description if description else extracted_text[:500],
        nom_fichier=filename,          
        chemin_fichier=file_path,      
        contenu_texte=extracted_text,
        date_limite=date_limite,
        user_id=user.id,
        departement_id=departement_id
    )
    db.session.add(offre)
    db.session.commit()

    # Analyse IA automatique du texte extrait du PDF
    informations_extraites = analyseur_texte_extrait(extracted_text)

    # Sauvegarde de la synthèse IA dans la table OffreAnalyser
    synthese_competences_offre = OffreAnalyser(
        diplomas=informations_extraites["diplomas"],    
        skills=informations_extraites["skills"],        
        experiences=informations_extraites["experiences"], 
        offre_id=offre.id
    )

    db.session.add(synthese_competences_offre)
    db.session.commit()

    return offre, synthese_competences_offre, informations_extraites
