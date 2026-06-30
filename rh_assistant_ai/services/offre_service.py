import os
from werkzeug.utils import secure_filename
from config.database import db
from models.offre import Offre
from models.offre_analyser import OffreAnalyser
from services.file_service import extract_text, analyseur_texte_extrait

# Importations optionnelles si utilisées par ailleurs
from services.nlp.preprocessing import clean_text
from services.nlp.skill_extractor import extract_skills
from services.nlp.diploma_extractor import extract_diplomas
from services.nlp.experience_extractor import extract_experience

def save_offre(file, recruteur, titre, description, date_limite, departement_id, nom_entreprise):
    filename = secure_filename(file.filename)
    
    # Harmonisation du dossier d'upload vers static pour VS Code / Flask
    upload_folder = "static/uploads/offres"
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)

    # Extraction réelle du texte du PDF
    extracted_text = extract_text(file_path)

    # 🟢 CORRECTION : Remplacement de user_id par recruteur_id 
    # pour s'aligner sur l'héritage polymorphique de votre BDD
    offre = Offre(
        titre=titre,
        entreprise=nom_entreprise,
        description=description if description else extracted_text[:500],
        nom_fichier=filename,          
        chemin_fichier=file_path,      
        contenu_texte=extracted_text,
        date_limite=date_limite,
        recruteur_id=recruteur.id, # 👈 Modifié ici
        departement_id=departement_id
    )
    db.session.add(offre)
    db.session.commit()

    # Analyse IA automatique du texte extrait du PDF
    informations_extraites = analyseur_texte_extrait(extracted_text)

    # Sauvegarde de la synthèse IA dans la table OffreAnalyser
    # (Utilise la liaison propre gérée en cascade)
    synthese_competences_offre = OffreAnalyser(
        diplomas=informations_extraites["diplomas"],    
        skills=informations_extraites["skills"],        
        experiences=informations_extraites["experiences"], 
        offre_id=offre.id
    )

    db.session.add(synthese_competences_offre)
    db.session.commit()

    return offre, synthese_competences_offre, informations_extraites
