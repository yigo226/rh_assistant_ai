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


# Route pour créer une offre manuellement
@offre_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_offre():

    if request.method == "POST":

        titre = request.form.get("titre")
        description = request.form.get(
            "description")

        offre = Offre(
            titre=titre,
            description=description,
            contenu_texte=description,
            user_id=current_user.id
        )

        db.session.add(offre)
        db.session.commit()

        informations_extraites = analyseur_texte_extrait(description)

        return render_template(
            "offre/result.html",
            offre=offre,
            analysis=informations_extraites ,
            saved_analysis=OffreAnalysis,
        )

    return render_template(
        "offre/create.html"
    )

# Route pour l'upload et l'analyse d'une offre

@offre_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload_offre():
    if request.method == "POST":
        file = request.files.get("offre_file")
        if not file:
            flash("Veuillez sélectionner un fichier", "danger")
            return redirect(request.url)

        offre, analysis, offre_analysis = save_offre(file, current_user)

        flash("Offre analysée avec succès", "success")
        return render_template("offre/result.html", 
                               offre=offre, 
                               analysis=analysis, 
                               saved_analysis=offre_analysis)

    return render_template("offre/upload.html")

# Historique des analyses d'offres
@offre_bp.route("/history")
@login_required
def history():

    offres = Offre.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Offre.date_creation.desc()
    ).all()

    return render_template(
        "offre/history.html",
        offre=offres
    )