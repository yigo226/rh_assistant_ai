

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

from config.database import db

from models.cv import CV
from services.file_service import extract_text_from_pdf

cv_bp = Blueprint(
    "cv",
    __name__,
    url_prefix="/cv"
)

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

        # création CV
        cv = CV(
            nom_fichier=filename,
            chemin_fichier=file_path,
            contenu_texte=extracted_text,
            user_id=current_user.id
        )

        db.session.add(cv)

        db.session.commit()

        flash(
            "CV analysé avec succès",
            "success"
        )

        return render_template(
            "cv/result.html",
            cv=cv
        )

    return render_template(
        "cv/upload.html"
    )