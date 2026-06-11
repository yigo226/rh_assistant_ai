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
from models.offre_analysis import OffreAnalysis
from services.offre_service import analyze_offre

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

        analysis = analyze_offre(description)

        return render_template(
            "offre/result.html",
            offre=offre,
            analysis=analysis,
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
            print("Aucun fichier sélectionné")
            flash(
                "Veuillez sélectionner un fichier",
                "danger"
            )

            return redirect(request.url)

        filename = secure_filename(
            file.filename
        )

        upload_folder = "uploads/offres"

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
        extracted_text = extract_text(file_path)


        # analyse de l'offre
        analysis = analyze_offre(
            extracted_text
        )

        # création offre
        # ici on lie l'offre à l'utilisateur connecté pour pouvoir afficher l'historique plus tard
        offre = Offre(

            titre=filename,

            description=extracted_text[:500],

            contenu_texte=extracted_text,

            user_id=current_user.id
        )

        db.session.add(offre)
        db.session.commit()

        # sauvegarde analyse
        # ici on lie l'analyse à l'offre créée pour pouvoir afficher les résultats plus tard
        offre_analysis = OffreAnalysis(

            skills=",".join(
                analysis["skills"]
            ),

            diplomas=",".join(
                analysis["diplomas"]
            ),

            experiences=",".join(
                map( str,
                    analysis["experiences"]
                )
            ),

            offre_id=offre.id
        )
        print("offre_analysis: ", offre_analysis)
        db.session.add(offre_analysis )
        db.session.commit()

        flash(
            "Offre analysée avec succès",
            "success"
        )

        return render_template(
            "offre/result.html",

            offre=offre,
            analysis=analysis,
            saved_analysis=offre_analysis
        )

    return render_template(
        "offre/upload.html"
    )

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