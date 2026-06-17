

import os
from config.database import db

            
from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
    flash,
    redirect,
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


@cv_bp.route("/matching", methods=["GET", "POST"])
@login_required
def matching():
    # 1. Vérifier si l'utilisateur a déjà un CV en base de données
    existing_cv = CV.query.filter_by(user_id=current_user.id).first()

    
    if request.method == "POST":
        file = request.files.get("cv")
        if not file:
            print("Aucun fichier sélectionné", "danger")
            return redirect(request.url)
        
        # Si l'utilisateur veut remplacer son CV existant
        if existing_cv:

            #  Supprimer proprement l'ancien pour valider la contrainte avant le save_cv
            # Supprimer le fichier physique sur le disque s'il existe
            if os.path.exists(existing_cv.chemin_fichier):
                os.remove(existing_cv.chemin_fichier)
                
            # Supprimer l'entrée en BDD
            db.session.delete(existing_cv)
            db.session.commit() # On valide la suppression pour libérer la contrainte unique

        # 2. Maintenant qu'il n'y a plus de doublon possible, on peut sauvegarder le nouveau
        cv, synthese_competences_cv, informations_extraites = save_cv(file, current_user)


        return render_template("cv/result.html", cv=cv, informations_extraites=informations_extraites, synthese_competences_cv=synthese_competences_cv)
    
    return render_template("cv/upload.html", existing_cv=existing_cv)



@cv_bp.route("/upload", methods=["POST"])
@login_required
def upload_cv():

    existing_cv = CV.query.filter_by(user_id=current_user.id).first()

    file = request.files.get("cv")

    if not file:
        return jsonify({
            "success": False,
            "message": "Aucun fichier sélectionné"
        }), 400

    if existing_cv:

        if os.path.exists(existing_cv.chemin_fichier):
            os.remove(existing_cv.chemin_fichier)

        db.session.delete(existing_cv)
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

