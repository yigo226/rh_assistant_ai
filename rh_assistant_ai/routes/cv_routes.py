

import os
from config.database import db

            
from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
    flash,
    redirect,
    session,
    url_for
)

from flask_login import (
    login_required,
    current_user
)

from werkzeug.utils import secure_filename
from models import cv_analyser

from config.database import db
from services.cv_service import save_cv
from models.cv import CV
from services.file_service import extract_text, extract_text_from_pdf
from models.cv_analyser import CVAnalyser


# Blueprint pour les routes liées aux CV
cv_bp = Blueprint(
    "cv",
    __name__,
    url_prefix="/cv"
)


@cv_bp.route("/chargement", methods=["GET", "POST"])
@login_required
def chargement_cv():

    if request.method == "POST":
        # 1. Récupération du fichier depuis le formulaire
        file = request.files.get("cv")

        if not file or file.filename == '':
            flash("Aucun fichier sélectionné ou le fichier est obligatoire", "danger")
            return redirect(request.url)

        # 2. Recherche et désactivation de l'ancien CV actuellement actif
        ancien_cv = CV.query.filter_by(user_id=current_user.id, est_actif=True).first()
        if ancien_cv:
            ancien_cv.est_actif = False
            db.session.commit()

        # 3. Appel de la logique unifiée (Sauvegarde + Extraction + Analyse IA)
        cv, synthese_cv, infos_ia = save_cv(
            file=file, 
            user=current_user
        )

        # 4. Activation explicite du nouveau CV
        cv.est_actif = True
        db.session.commit()

        # 5. Enregistrement en session pour le matching
        session['current_cv_id'] = cv.id

        flash("Votre nouveau CV a été chargé et activé avec succès !", "success")

        # 6. 🔄 REDIRECTION VERS L'ESPACE CANDIDAT AU LIEU D'UN TEMPLATE FIXE
        return redirect(url_for("candidat.espace_candidat"))
    
    
    # En méthode GET (Affichage de la page de dépôt)
    # On récupère le CV actif actuel pour l'afficher dans le template si besoin
    existing_cv = CV.query.filter_by(user_id=current_user.id, est_actif=True).first()
    return render_template("cv/upload.html", existing_cv=existing_cv)

# # chargement du cv de l'utilisateur
# @cv_bp.route("/chargement", methods=["GET", "POST"])
# @login_required
# def chargement_cv():
#     if request.method == "POST":
#         # 1. Récupération du fichier depuis le formulaire (name="cv")
#         file = request.files.get("cv")

#         if not file or file.filename == '':
#             flash("Aucun fichier sélectionné ou le fichier est obligatoire", "danger")
#             return redirect(request.url)

#         # 2. Appel de la logique unifiée (Sauvegarde + Extraction + Analyse IA)
#         # Reçoit le triplet : l'objet CV, l'analyse SQL, et le dictionnaire brut
#         cv, synthese_cv, infos_ia = save_cv(
#             file=file, 
#             user=current_user
#         )

#         # 3. Enregistrement de l'ID du CV en session (Optionnel, utile pour le matching)
#         session['current_cv_id'] = cv.id

#         flash("Votre CV a été téléversé, enregistré et analysé par l'IA avec succès !", "success")

#         # 4. Affichage de la page de résultats en passant l'objet CV et ses analyses
#         return render_template(
#             "cv/result.html",
#             cv=cv,
#             synthese=synthese_cv,
#             details=infos_ia
#         )

#     # En méthode GET : Affichage simple du formulaire d'upload
#     return render_template("cv/upload.html")


# pour le script (ancien sur une seule page)
@cv_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload_cv():
    existing_cv = CV.query.filter_by(user_id=current_user.id, est_actif = True).first()

    file = request.files.get("cv")

    if not file:
        return jsonify({
            "success": False,
            "message": "Aucun fichier sélectionné"
        }), 400

    # On archive l'ancien CV en le rendant inactif
    if existing_cv:
        existing_cv.est_actif = False
        db.session.commit() 
    
    cv, synthese_competences_cv, informations_extraites = save_cv(file, current_user)

    print("type synthese_competences_cv dans cv_route", type(synthese_competences_cv))
    print(synthese_competences_cv.id)
    print(" Fin d'affiche du type synthese_competences_cv dans cv_route")

    return jsonify({
        "success": True,
        "message": "CV analysé avec succès",
        "cv_id": cv.id,
        "analysis_id": synthese_competences_cv.id,
        "filename": cv.nom_fichier
    })


@cv_bp.route("/result/<int:analysis_id>")
@login_required
def view_result(analysis_id):
    # Récupérer les résultats de l'analyse à partir de l'ID
    # analysis_id correspond à l'id de CVAnalyser, qui contient les compétences, diplômes et expériences extraites du CV
    informations_extraites = CVAnalyser.query.get_or_404(analysis_id)
    print("Le contenu de informations_extraites dans cv_route : ", informations_extraites)

    # ici on peut accéder à cv via la relation définie dans le modèle CVAnalyser
    # je retourne id et nom_fichier pour vérifier que c'est bien le bon cv qui est lié à l'analyse
    cv_utilisateur = informations_extraites.cv
    print("Le contenu de cv_utilisateur dans cv_route : ", cv_utilisateur)
    
    return render_template(
        "cv/result.html",
        cv_utilisateur=cv_utilisateur,
        informations_extraites=informations_extraites
    )


# Route pour afficher l'historique des analyses
@cv_bp.route("/history")
@login_required
def history():

    analyses = CVAnalyser.query\
        .join(CV)\
        .filter(
            CV.user_id == current_user.id
        )\
        .order_by(
            CVAnalyser.created_at.desc()
        )\
        .all()

    return render_template(
        "cv/history.html",
        analyses=analyses
    )

