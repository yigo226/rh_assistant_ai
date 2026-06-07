

import os

from flask import (
    Blueprint,
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
from services.cv_service import analyze_cv

from config.database import db

from models.cv import CV
from services.cv_service import analyze_cv
from services.file_service import extract_text_from_pdf
from models.cv_analysis import CVAnalysis
# Blueprint pour les routes liées aux CV
cv_bp = Blueprint(
    "cv",
    __name__,
    url_prefix="/cv"
)

# Route pour l'upload et l'analyse du CV
@cv_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload_cv():

    if request.method == "POST":

        # récupération fichier
        file = request.files.get("cv")

        if not file:

            flash(
                "Aucun fichier sélectionné",
                "danger"
            )

            return redirect(
                request.url
            )

        filename = secure_filename(
            file.filename
        )

        upload_folder = "uploads"

        os.makedirs(
            upload_folder,
            exist_ok=True
        )

        file_path = os.path.join(
            upload_folder,
            filename
        )

        # sauvegarde physique
        file.save(file_path)

        # extraction texte
        extracted_text = extract_text_from_pdf(
            file_path
        )
        
        #analyse du CV
        analysis = analyze_cv(extracted_text)

        # création CV
        cv = CV(
            nom_fichier=filename,
            chemin_fichier=file_path,
            contenu_texte=extracted_text,
            user_id=current_user.id
        )

        db.session.add(cv)

        db.session.commit()

        cv_analysis = CVAnalysis(
            skills=", ".join(analysis["skills"]),
            diplomas=", ".join(analysis["diplomas"]),
            experiences=", ".join(analysis["experiences"]),
            cv_id=cv.id
        )

        db.session.add(cv_analysis)
        db.session.commit()

        flash(
            "CV analysé avec succès",
            "success"
        )

        return render_template(
            "cv/result.html",
            cv=cv,
            analysis=analysis,
            saved_analysis=cv_analysis
        )

    return render_template(
        "cv/upload.html"
    )

# Route pour afficher l'historique des analyses
@cv_bp.route("/history")
@login_required
def history():

    analyses = CVAnalysis.query\
        .join(CV)\
        .filter(
            CV.user_id == current_user.id
        )\
        .order_by(
            CVAnalysis.created_at.desc()
        )\
        .all()

    return render_template(
        "cv/history.html",
        analyses=analyses
    )

