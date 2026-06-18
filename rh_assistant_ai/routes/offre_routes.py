import os

from flask import (
    Blueprint,
    render_template,
    request,
    session,
    jsonify,
)

from flask_login import (
    login_required,
    current_user
)

from werkzeug.utils import secure_filename

from config.database import db

from models.offre import Offre

from werkzeug.utils import secure_filename
from models.offre_analyser import OffreAnalyser
from services.offre_service import analyseur_texte_extrait, save_offre

from services.file_service import extract_text 



offre_bp = Blueprint(
    "offre",
    __name__,
    url_prefix="/offre"
)


# ❌ ON NE SUPPRIME PLUS L'ANCIENNE OFFRE ICI 

@offre_bp.route("/upload", methods=["POST"])
@login_required
def upload_offre():
    file = request.files.get("file") 

    if not file:
        return jsonify({"success": False, "message": "Aucun fichier sélectionné"}), 400

    # Chaque upload crée une nouvelle entrée indépendante dans l'historique de l'utilisateur
    
    # Traiter et sauvegarder la nouvelle offre
    offre, synthese_criteres_offre, informations_extraites = save_offre(file, current_user)

    # On stocke l'ID de cette offre précise en session pour savoir sur laquelle 
    # l'utilisateur travaille actuellement
    session['current_offre_id'] = offre.id

    return jsonify({
        "success": True,
        "message": "Offre ajoutée à votre historique et analysée",
        "offre_id": offre.id,
        "analysis_id": synthese_criteres_offre.id,
        "filename": offre.nom_fichier
    })

# ❌ ici on SUPPRIME L'ANCIENNE OFFRE 

# @offre_bp.route("/upload", methods=["GET", "POST"])
# @login_required
# def upload_offre():
#     # 1. Rechercher si l'utilisateur a déjà une offre enregistrée
#     existing_offre = Offre.query.filter_by(user_id=current_user.id).first()

#     # Récupération du fichier via la clé définie dans le script JS du template
#     file = request.files.get("file") 

#     if not file:
#         return jsonify({
#             "success": False,
#             "message": "Aucun fichier sélectionné"
#         }), 400

#     # 2. Nettoyer l'ancienne offre et son fichier physique si elle existe
#     if existing_offre:
#         if existing_offre.chemin_fichier and os.path.exists(existing_offre.chemin_fichier):
#             try:
#                 os.remove(existing_offre.chemin_fichier)
#             except Exception as e:
#                 print(f"Erreur lors de la suppression du fichier physique : {e}")

#         db.session.delete(existing_offre)
#         db.session.commit()
    
#     # 3. Traiter et sauvegarder la nouvelle offre
#     # Aligné sur le triplet retourné par votre logique (Objet, Analyse_Objet, Données_brutes)
#     offre, synthese_criteres_offre, informations_extraites = save_offre(file, current_user)

#     print("type synthese_criteres_offre dans offre_route :", type(synthese_criteres_offre))
#     print(f"ID Analyse Offre : {synthese_criteres_offre.id}")
#     print("Fin d'affichage du type synthese_criteres_offre dans offre_route")

#     # 4. Retourner la réponse JSON attendue par le script AJAX du formulaire
#     return jsonify({
#         "success": True,
#         "message": "Offre analysée avec succès dans le système",
#         "offre_id": offre.id,
#         "analysis_id": synthese_criteres_offre.id,
#         "filename": offre.nom_fichier
#     })


@offre_bp.route("/result/<int:analysis_id>")
@login_required
def view_result(analysis_id):
    # Récupérer les critères extraits de l'offre ou renvoyer une erreur 404
    informations_extraites = OffreAnalyser.query.get_or_404(analysis_id)
    print("Le contenu de informations_extraites dans offre_route : ", informations_extraites)

    # Accès à l'offre parente via la relation back_populates du modèle
    offre_utilisateur = informations_extraites.offre
    print("Le contenu de offre_utilisateur dans offre_route : ", offre_utilisateur)
    
    print(type(informations_extraites.skills))
    print(informations_extraites.skills)
    return render_template(
        "offre/result.html",
        offre_utilisateur=offre_utilisateur,
        informations_extraites=informations_extraites
    )

