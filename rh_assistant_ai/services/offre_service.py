import os
from werkzeug.utils import secure_filename
from config.database import db
from models.offre import Offre
from models.offre_analyser import OffreAnalyser
from services.file_service import extract_text, analyseur_texte_extrait

def save_offre(fichier, recruteur, titre, description, date_limite, departement_id):
    # 🟢 CORRECTION : Le paramètre nom_entreprise a été supprimé de la signature
    nom_fichier = secure_filename(fichier.filename)

    # Harmonisation du dossier d'upload vers static pour VS Code / Flask
    dossier_upload = "static/uploads/offres"
    os.makedirs(dossier_upload, exist_ok=True)
    chemin_fichier = os.path.join(dossier_upload, nom_fichier)
    fichier.save(chemin_fichier)

    # Extraction réelle du texte du PDF
    texte_extrait = extract_text(chemin_fichier)

    # Création complète de l'Offre liée au Recruteur
    # 🟢 CORRECTION : Suppression de la colonne fantôme entreprise=nom_entreprise
    offre = Offre(
        titre=titre,
        description=description if description else texte_extrait[:500],
        nom_fichier=nom_fichier,          
        chemin_fichier=chemin_fichier,      
        contenu_texte=texte_extrait,
        date_limite=date_limite,
        recruteur_id=recruteur.id,
        departement_id=departement_id
    )
    db.session.add(offre)
    db.session.commit()

    # Analyse IA automatique du texte extrait du PDF
    informations_extraites = analyseur_texte_extrait(texte_extrait)

    # Utilisation des nouveaux champs et clés en français
    synthese_competences_offre = OffreAnalyser(
        competences=informations_extraites["competences"],        
        diplomes=informations_extraites["diplomes"],    
        experiences=informations_extraites["experiences"], 
        offre_id=offre.id
    )

    db.session.add(synthese_competences_offre)
    db.session.commit()

    return offre, synthese_competences_offre, informations_extraites


# def save_offre(fichier, recruteur, titre, description, date_limite, departement_id, nom_entreprise):
#     nom_fichier = secure_filename(fichier.filename)
    
#     # Harmonisation du dossier d'upload vers static pour VS Code / Flask
#     dossier_upload = "static/uploads/offres"
#     os.makedirs(dossier_upload, exist_ok=True)
#     chemin_fichier = os.path.join(dossier_upload, nom_fichier)
#     fichier.save(chemin_fichier)

#     # Extraction réelle du texte du PDF
#     texte_extrait = extract_text(chemin_fichier)

#     # Création complète de l'Offre liée au Recruteur
#     offre = Offre(
#         titre=titre,
#         entreprise=nom_entreprise,
#         description=description if description else texte_extrait[:500],
#         nom_fichier=nom_fichier,          
#         chemin_fichier=chemin_fichier,      
#         contenu_texte=texte_extrait,
#         date_limite=date_limite,
#         recruteur_id=recruteur.id,
#         departement_id=departement_id
#     )
#     db.session.add(offre)
#     db.session.commit()

#     # Analyse IA automatique du texte extrait du PDF (Retourne les clés en français)
#     informations_extraites = analyseur_texte_extrait(texte_extrait)

#     # 🟢 CORRECTION : Utilisation des nouveaux champs et clés en français
#     synthese_competences_offre = OffreAnalyser(
#         competences=informations_extraites["competences"],        
#         diplomes=informations_extraites["diplomes"],    
#         experiences=informations_extraites["experiences"], 
#         offre_id=offre.id
#     )

#     db.session.add(synthese_competences_offre)
#     db.session.commit()

#     return offre, synthese_competences_offre, informations_extraites
