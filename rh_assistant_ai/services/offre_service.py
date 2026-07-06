import os
import json
from werkzeug.utils import secure_filename
from config.database import db
from models.offre import Offre
from models.offre_analyser import OffreAnalyser
from models.question_entretien import QuestionEntretien
from .file_service import extract_text
from .question_entretien_service import generer_questions_entretien

from .analyser_dict_service import analyseur_texte_extrait # V1
#from services.analyseur_ai_service import analyseur_texte_extrait  # V2.1.0

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

    # Dans votre fichier offre_service.py après avoir créé l'offre en BDD :
    resultat_ia = generer_questions_entretien(texte_extrait)
    print("\n 🤖 [IA QWEN] Résultat de la génération de questions : \n", resultat_ia)
    for q in resultat_ia.get("questions", []):
        nouvelle_question = QuestionEntretien(
            offre_id=offre.id, # L'ID de l'offre tout juste créée
            donnees_json=json.dumps(resultat_ia)
        )
        db.session.add(nouvelle_question)

    db.session.commit()


    return offre, synthese_competences_offre, informations_extraites
