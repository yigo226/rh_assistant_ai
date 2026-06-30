import os
from flask import Blueprint, jsonify, render_template, request, flash, redirect, session, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from config.database import db
from models import CV, CVAnalyser
from models.utilisateur import Candidat

from services.cv_service import save_cv

# Blueprint pour les routes liées aux CV
cv_bp = Blueprint(
    "cv",
    __name__,
    url_prefix="/cv"
)

# ============================================================
# 1. CHARGEMENT TRADITIONNEL (Formulaire HTML standard)
# ============================================================
@cv_bp.route("/chargement", methods=["GET", "POST"])
@login_required
def chargement_cv():
    if request.method == "POST":
        # Récupération du fichier depuis le formulaire
        file = request.files.get("cv")

        if not file or file.filename == '':
            flash("Aucun fichier sélectionné ou le fichier est obligatoire", "danger")
            return redirect(request.url)

        # 🟢 CORRECTION : Filtrage sur la bonne clé candidat_id
        ancien_cv = CV.query.filter_by(candidat_id=current_user.id, est_actif=True).first()
        if ancien_cv:
            ancien_cv.est_actif = False
            db.session.commit()

        # 🟢 CORRECTION : Passage de l'argument typé candidat (conforme au nouveau service)
        cv, synthese_cv, infos_ia = save_cv(
            file=file, 
            candidat=current_user
        )

        # Activation explicite du nouveau CV
        cv.est_actif = True
        db.session.commit()

        # Enregistrement en session pour le matching rapide
        session['current_cv_id'] = cv.id

        flash("Votre nouveau CV a été chargé et activé avec succès !", "success")
        return redirect(url_for("candidat.espace_candidat"))
    
    # En méthode GET : Récupération du CV actif pour l'affichage de l'état actuel dans le template
    existing_cv = CV.query.filter_by(candidat_id=current_user.id, est_actif=True).first()
    return render_template("cv/upload.html", existing_cv=existing_cv)


# ============================================================
# 2. UPLOAD EN ARRIÈRE-PLAN (Requête AJAX du Formulaire de Matching)
# ============================================================
@cv_bp.route("/upload", methods=["POST"])
@login_required
def upload_cv():
    # 🟢 CORRECTION : Filtrage sur candidat_id
    existing_cv = CV.query.filter_by(candidat_id=current_user.id, est_actif=True).first()

    file = request.files.get("cv")
    if not file:
        return jsonify({
            "success": False,
            "message": "Aucun fichier sélectionné"
        }), 400

    # Archivage automatique de l'ancien document
    if existing_cv:
        existing_cv.est_actif = False
        db.session.commit() 
    
    # Enregistrement et calcul de la synthèse IA
    cv, synthese_competences_cv, informations_extraites = save_cv(file, candidat=current_user)

    print(f"CV Analysé avec succès. ID Analyse généré : {synthese_competences_cv.id}")

    return jsonify({
        "success": True,
        "message": "CV analysé avec succès",
        "cv_id": cv.id,
        "analysis_id": synthese_competences_cv.id,
        "filename": cv.nom_fichier
    })


# ============================================================
# 3. APERÇU DE LA SYNTHÈSE DES COMPÉTENCES DU CV
# ============================================================
@cv_bp.route("/result/<int:analysis_id>")
@login_required
def view_result(analysis_id):
    # Récupérer l'analyse ou renvoyer une erreur 404
    informations_extraites = CVAnalyser.query.get_or_404(analysis_id)
    cv_utilisateur = informations_extraites.cv
    
    return render_template(
        "cv/result.html",
        cv_utilisateur=cv_utilisateur,
        informations_extraites=informations_extraites
    )


# ============================================================
# 4. HISTORIQUE GLOBAL DES ANCIENS CVS ARCHIVÉS
# ============================================================
@cv_bp.route("/history")
@login_required
def history():
    # 🟢 CORRECTION : Jointure et filtrage sur la clé candidat_id
    # Tri basé sur le champ temporel réel de la table cvs (date_upload)
    analyses = CVAnalyser.query\
        .join(CV)\
        .filter(CV.candidat_id == current_user.id)\
        .order_by(CV.date_upload.desc())\
        .all()

    return render_template(
        "cv/history.html",
        analyses=analyses
    )
