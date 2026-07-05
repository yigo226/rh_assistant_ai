import os
from werkzeug.utils import secure_filename
from config.database import db
from models.offre import Offre
from models.offre_analyser import OffreAnalyser
from services.file_service import extract_text
# from services.analyser_dict_service import analyseur_texte_extrait # V1
#from services.analyseur_ai_service import analyseur_texte_extrait
from services.analyseur_ai_service import analyseur_texte_extrait  # V2.1.0

def save_offre(fichier, recruteur, titre, description, date_limite, departement_id):
    nom_fichier = secure_filename(fichier.filename)

    # Harmonisation du dossier d'upload vers static pour VS Code / Flask
    dossier_upload = "static/uploads/offres"
    os.makedirs(dossier_upload, exist_ok=True)
    chemin_fichier = os.path.join(dossier_upload, nom_fichier)
    fichier.save(chemin_fichier)

    # Extraction réelle du texte du PDF
    texte_extrait = extract_text(chemin_fichier)

    # Création complète de l'Offre liée au Recruteur
    offre = Offre(
        titre=titre,
        description=description if description else texte_extrait[:100],
        nom_fichier=nom_fichier,          
        chemin_fichier=chemin_fichier,      
        date_limite=date_limite,
        recruteur_id=recruteur.id,
        departement_id=departement_id
    )
    db.session.add(offre)
    db.session.commit()

    # Analyse IA automatique du texte extrait du PDF
    informations_extraites = analyseur_texte_extrait(texte_extrait)
    print(f"🧠 [OFFRE SERVICE] Analyse IA terminée pour l'offre '{titre}'. Résultat : {informations_extraites}")
    # Utilisation des nouveaux champs et clés en français
    synthese_competences_offre = OffreAnalyser(
        contenu_texte=texte_extrait,
        competences=informations_extraites["competences"],        
        diplomes=informations_extraites["diplomes"],    
        experiences=informations_extraites["experiences"], 
        offre_id=offre.id
    )

    db.session.add(synthese_competences_offre)
    db.session.commit()

    return offre, synthese_competences_offre, informations_extraites
